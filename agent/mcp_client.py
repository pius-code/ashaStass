# flake8: noqa
"""This file controls the agent, its loop, message entry, agent behaviour, model selection etc""" # noqa
from agents import Agent, Runner
from agents.items import ToolCallItem, ToolCallOutputItem
import json
import uuid
import asyncio
from agents.models.openai_chatcompletions import OpenAIChatCompletionsModel
from dotenv import load_dotenv
from agent.client import OR_CLIENT, GROQ_CLIENT, gpt_groq_model, openRouter_claude_Sonnet_model  # noqa
from utils.redis import r, store_message, get_user_messages, clear_identity_completely, get_user_identity, normalize_address, _history_to_input_items  # noqa
from utils.caspian import _keep_typing  # noqa
from core.fastmcp import _connect_mcp_servers  # noqa
load_dotenv()


async def agent(message):
    typing_task = asyncio.create_task(_keep_typing(message, interval=10))
    try:
        return await _agent_inner(message)
    finally:
        typing_task.cancel()


async def _agent_inner(message):
    conv_id = getattr(message, "conversation_id", None)
    identity_key = get_user_identity(
        message.channel,
        message.sender['address'],
        conversation_id=conv_id,
    )
    if identity_key is None:
        identity_key = f"identity:{uuid.uuid4().hex}"
        r.hset(identity_key, mapping={message.channel: normalize_address(message.sender['address'])})

    if message.text and message.text.strip().lower() == "clear":
        clear_identity_completely(identity_key)
        message.reply("History/session erased from memory")
        return None

    if message.text and message.text.strip().lower() == "flashashairis":
        r.flushall()
        message.reply("Redis database completely flushed")
        return None

    store_message(identity_key, "user", message.text, message.channel)
    history = get_user_messages(identity_key)
    input_items = _history_to_input_items(history)

    async with _connect_mcp_servers() as active_mcp_servers:
        agent = Agent(
            name="ASHA",
            instructions="You are ASHA, a helpful personal assistant AI with ASHA IoT tools.",
            mcp_servers=active_mcp_servers,
            model=OpenAIChatCompletionsModel(
                model=gpt_groq_model,
                openai_client=GROQ_CLIENT
            )
        )
        result = await Runner.run(agent, input_items)

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
