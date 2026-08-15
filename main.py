from core.casp import client
from core.fastmcp import mcp
from utils.asha import check_pairing_code_validity
from agent.mcp_client import agent
import threading
import asyncio


def main():
    @client.on_message
    def handle(message):
        print(message)
        valid_pairing_code = check_pairing_code_validity(message.text.strip())
        if valid_pairing_code is None:
            message.reply("Looks, like you are unauntheticated")
        try:
            agent_reply = asyncio.run(agent(message))
        except Exception as e:
            print(f"agent() failed for {message.channel}:{message.sender.get('address')}: {e}") # noqa
            message.reply("Hit a snag on my end — mind trying that again?")
            return
        if agent_reply:
            message.reply(agent_reply)

    listener_thread = threading.Thread(target=client.listen, daemon=True) # noqa
    listener_thread.start()
    mcp.run(transport="http", host="0.0.0.0", port=8081)


if __name__ == "__main__":
    main()
