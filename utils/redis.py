import os
import uuid
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


def normalize_address(address: str) -> str:
    """Telegram usernames and emails are both effectively case-insensitive
    in practice, so treat any casing/whitespace variant as the same address.
    """
    return address.strip().lower()


def _safe_str(val: bytes | str | None) -> str | None:
    if val is None:
        return None
    if isinstance(val, bytes):
        return val.decode("utf-8")
    return str(val)


def get_or_create_user_identity(channel: str, address: str, conversation_id: str | None = None) -> tuple[str, str | None]: # noqa
    address = normalize_address(address)
    for key in r.scan_iter("identity:*"):
        data = r.hgetall(key)
        if data.get(channel) == address:
            key_str = key.decode("utf-8") if isinstance(key, bytes) else str(key) # noqa
            return key_str, _safe_str(data.get("pairing_code"))

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
                            print(f"Updated identity {id_key} {channel} handle {old_address} -> {address}") # noqa
                            id_key_str = id_key.decode("utf-8") if isinstance(id_key, bytes) else str(id_key) # noqa
                            return id_key_str, _safe_str(id_data.get("pairing_code")) # noqa

    new_key = f"identity:{uuid.uuid4().hex}"
    r.hset(new_key, mapping={channel: address})
    return new_key, None


def get_user_identity(channel: str, address: str, conversation_id: str | None = None): # noqa
    key, _ = get_or_create_user_identity(channel, address, conversation_id)
    return key


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


def _history_to_input_items(history, max_messages: int = 100):
    recent_history = history[-max_messages:] if len(history) > max_messages else history
    input_items = []
    seen_call_ids = set()

    for h in recent_history:
        try:
            if h["role"] == "tool_call":
                call = json.loads(h["text"])
                tool_name = call.get("name")
                call_id = call.get("call_id")
                if tool_name and call_id:
                    seen_call_ids.add(call_id)
                    input_items.append({
                        "type": "function_call",
                        "call_id": call_id,
                        "name": tool_name,
                        "arguments": call.get("arguments", "{}"),
                    })
            elif h["role"] == "tool_result":
                result = json.loads(h["text"])
                call_id = result.get("call_id")
                if call_id and call_id in seen_call_ids:
                    input_items.append({
                        "type": "function_call_output",
                        "call_id": call_id,
                        "output": result.get("output", ""),
                    })
            elif h["role"] == "assistant":
                if h.get("text"):
                    input_items.append({"role": "assistant", "content": h["text"]})
            else:
                if h.get("text"):
                    input_items.append({"role": "user", "content": f"[via {h['channel']}] {h['text']}"})
        except Exception:
            continue

    return input_items
