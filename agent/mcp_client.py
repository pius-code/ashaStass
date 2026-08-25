# flake8: noqa
"""This file controls the agent, its loop, message entry, agent behaviour, model selection etc"""
from agents import Agent, Runner
from agents.items import ToolCallItem, ToolCallOutputItem
import json
import uuid
import asyncio
from agents.models.openai_chatcompletions import OpenAIChatCompletionsModel
from dotenv import load_dotenv
from agent.client import OR_CLIENT, GROQ_CLIENT, gpt_groq_model, openRouter_claude_Sonnet_model
from utils.redis import r, store_message, get_user_messages, clear_identity_completely, _history_to_input_items
from utils.caspian import _keep_typing
from core.fastmcp import _connect_mcp_servers
from prompt.system import get_system_prompt
load_dotenv()


async def agent(message, identity_key: str):
    typing_task = asyncio.create_task(_keep_typing(message, interval=4.0))
    try:
        return await _agent_inner(message, identity_key)
    finally:
        typing_task.cancel()


async def _agent_inner(message, identity_key: str):
    if message.text and message.text.strip().lower() == "clear":
        clear_identity_completely(identity_key)
        await message.reply("History/session erased from memory")
        return None

    if message.text and message.text.strip().lower() == "flashashairis":
        r.flushall()
        await message.reply("Redis database completely flushed")
        return None

    store_message(identity_key, "user", message.text, message.channel)
    history = get_user_messages(identity_key)

    print(f"--- History for {identity_key} ({len(history)} messages) ---")
    for h in history:
        print(f"  {h['role']:<12} | {h.get('channel'):<10} | {h['text'][:200]}")
    print("---------------------------------------------------------")

    input_items = _history_to_input_items(history)

    raw_code = r.hget(identity_key, "pairing_code")
    user_pairing_code = raw_code.decode("utf-8") if isinstance(raw_code, bytes) else str(raw_code or "")

    async with _connect_mcp_servers(pairing_code=user_pairing_code) as active_mcp_servers:
        agent_instance = Agent(
            name="ASHA",
            instructions=get_system_prompt(),
            mcp_servers=active_mcp_servers,
            model=OpenAIChatCompletionsModel(
                model=gpt_groq_model,
                openai_client=GROQ_CLIENT
            )
        )
        result = await Runner.run(agent_instance, input_items)

        pending_call_id = None
        for item in result.new_items:
            if isinstance(item, ToolCallItem):
                pending_call_id = item.call_id or uuid.uuid4().hex
                tool_name = getattr(item.raw_item, "name", "")
                tool_args = getattr(item.raw_item, "arguments", "")
                store_message(
                    identity_key, "tool_call",
                    json.dumps({
                        "call_id": pending_call_id,
                        "name": tool_name,
                        "arguments": tool_args,
                    }),
                    message.channel
                )
            elif isinstance(item, ToolCallOutputItem):
                store_message(
                    identity_key, "tool_result",
                    json.dumps({
                        "call_id": pending_call_id,
                        "output": str(item.output),
                    }),
                    message.channel
                )

        store_message(identity_key, "assistant", result.final_output, message.channel)
        print(result.final_output)
        return result.final_output
