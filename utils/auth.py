import os
from dotenv import load_dotenv
from core.wrapper import TelegramMessageWrapper

load_dotenv()

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000").rstrip("/")


async def check_pairing(user_pairing_code: str | None, wrapper: TelegramMessageWrapper) -> bool: # noqa
    """
    Returns True if user is paired.
    If unpaired, sends the web pairing link using the wrapper and returns False. # noqa
    """
    if not user_pairing_code:
        web_link = f"{FRONTEND_URL}/pair?channel={wrapper.channel}&address={wrapper.sender['address']}"  # noqa
        reply_text = f"Looks like your account is unpaired!\n\nPlease click here to log in and pair your device:\n{web_link}" # noqa
        await wrapper.reply(reply_text) # noqa
        return False
    return True
