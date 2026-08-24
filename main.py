import asyncio
import threading
import uvicorn
from core.casp import client
from utils.redis import get_or_create_user_identity
from agent.mcp_client import agent
from core.fastapi import app
from routes.ashaStass import router as asha_router
import utils.middleware # noqa # loads and uses the cors 


app.include_router(asha_router)


@client.on_message
def handle(message):
    print(message)
    conv_id = getattr(message, "conversation_id", None)
    identity_key, user_pairing_code = get_or_create_user_identity(
        message.channel,
        message.sender["address"],
        conversation_id=conv_id,
    )

    if not user_pairing_code:
        web_link = f"http://localhost:3000/pair?channel={message.channel}&address={message.sender['address']}"  # noqa
        reply_text = f"Looks like your account is unpaired!\n\nPlease click here to log in and pair your device:\n{web_link}" # noqa
        message.reply(reply_text)
        return

    try:
        agent_reply = asyncio.run(agent(message, identity_key))
    except Exception as e:
        print(f"agent() failed: {e}")
        message.reply("Hit a snag on my end. Mind trying that again?")
        return

    if agent_reply:
        message.reply(agent_reply)


def start_caspian():
    print("ASHA bot is listening for incoming messages...")
    client.listen()


def main():
    caspian_thread = threading.Thread(target=start_caspian, daemon=True)
    caspian_thread.start()
    print("Starting ashaStass API server on port 8081...")
    uvicorn.run(app, host="0.0.0.0", port=8081)


if __name__ == "__main__":
    main()
