import asyncio
import uuid
from core.casp import client
from utils.asha import check_pairing_code_validity
from utils.redis import r, get_user_identity, normalize_address
from agent.mcp_client import agent


def main():
    @client.on_message
    def handle(message):
        print(message)
        conv_id = getattr(message, "conversation_id", None)
        identity_key = get_user_identity(
            message.channel,
            message.sender['address'],
            conversation_id=conv_id,
        )
        if identity_key is None:
            identity_key = f"identity:{uuid.uuid4().hex}"
            r.hset(identity_key, mapping={message.channel: normalize_address(message.sender['address'])}) # noqa

        user_pairing_code = r.hget(identity_key, "pairing_code")

        if not user_pairing_code:
            valid_data = asyncio.run(check_pairing_code_validity(message.text.strip())) # noqa
            if not valid_data:
                message.reply("Looks like you are unauthenticated. Please enter your pairing code.") # noqa
                return

            r.hset(identity_key, "pairing_code", message.text.strip())
            project_name = valid_data.get("project_name", "Device")
            message.reply(f"Device '{project_name}' successfully paired! How can I help you?") # noqa
            return

        try:
            agent_reply = asyncio.run(agent(message, identity_key))
        except Exception as e:
            print(f"agent() failed: {e}")
            message.reply("Hit a snag on my end. Mind trying that again?")
            return

        if agent_reply:
            message.reply(agent_reply)

    print("ASHA bot is listening for incoming messages...")
    client.listen()


if __name__ == "__main__":
    main()
