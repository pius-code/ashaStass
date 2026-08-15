from dataclasses import dataclass


@dataclass
class FakeMessage:
    channel: str
    sender: dict
    text: str


def build_fake_message(task_id: str, prompt_text: str, channel: str = "system", sender_address: str | None = None) -> FakeMessage:
    """
    Builds a synthetic message for events with no real inbound Caspian message
    (e.g. MQTT-triggered retries). Uses real contact channel/address if provided
    so identity resolution maps back to the existing user identity record.
    """
    return FakeMessage(
        channel=channel,
        sender={"address": sender_address or task_id},
        text=prompt_text,
    )
