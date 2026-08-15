import os
import redis
import json
from dotenv import load_dotenv
load_dotenv()

r = redis.Redis.from_url(
    os.getenv("REDIS_URL", ""),
    decode_responses=True,
    socket_timeout=10.0,
    socket_connect_timeout=10.0,
    retry_on_timeout=True,
)

# TODO: post-capstone, move this to a permanent DB


def normalize_address(address: str) -> str:
    """Telegram usernames and emails are both effectively case-insensitive
    in practice, so treat any casing/whitespace variant as the same address.
    """
    return address.strip().lower()


def get_user_identity(channel: str, address: str, conversation_id: str | None = None): # noqa
    address = normalize_address(address)
    # 1. Primary check: exact channel + address match
    for key in r.scan_iter("identity:*"):
        data = r.hgetall(key)
        if data.get(channel) == address:
            return key

    # 2. Fallback check: match strictly by conversation_id (unique 1-to-1 chat thread) # noqa
    if conversation_id:
        for key in r.scan_iter(f"{channel}:*"):
            c_data = r.hgetall(key)
            if c_data.get("conversation_id") == conversation_id:
                old_address = c_data.get("address")
                if old_address and old_address != address:
                    for id_key in r.scan_iter("identity:*"):
                        id_data = r.hgetall(id_key)
                        if id_data.get(channel) == old_address:
                            r.hset(id_key, channel, address)
                            print(f"Updated identity {id_key} {channel} handlrr{old_address} -> {address}") # noqa
                            return id_key

    return None


# def lookup_contact(channel: str, address: str):
#     address = normalize_address(address)
#     key = f"{channel}:{address}"
#     data = r.hgetall(key)
#     return data if data else None


def store_message(identity_key: str, role: str, text: str, channel: str):
    """Append one message (user or assistant) to this identity's history."""
    key = f"history:{identity_key}"
    entry = json.dumps({"role": role, "text": text, "channel": channel})
    r.rpush(key, entry)


def get_user_messages(identity_key: str) -> list[dict]:
    """Fetch full message history for this user, oldest first."""
    key = f"history:{identity_key}"
    raw = r.lrange(key, 0, -1)
    return [json.loads(item) for item in raw]


def clear_history(identity_key: str) -> None:
    r.delete(f"history:{identity_key}")


def clear_identity_completely(identity_key: str) -> None:
    """Completely flash and erase history, identity mapping, and linked channel keys.""" # noqa
    if not identity_key:
        return
    channels = r.hgetall(identity_key)
    for channel, address in channels.items():
        if channel and address:
            r.delete(f"{channel}:{address}")
    r.delete(f"history:{identity_key}")
    r.delete(identity_key)


def _history_to_input_items(history):
    input_items = []
    for h in history:
        if h["role"] == "tool_call":
            call = json.loads(h["text"])
            input_items.append({
                "type": "function_call",
                "call_id": call["call_id"],
                "name": call["name"],
                "arguments": call["arguments"],
            })
        elif h["role"] == "tool_result":
            result = json.loads(h["text"])
            input_items.append({
                "type": "function_call_output",
                "call_id": result["call_id"],
                "output": result["output"],
            })
        else:
            input_items.append({"role": h["role"], "content": f"[via {h['channel']}] {h['text']}"}) # noqa

    return input_items
