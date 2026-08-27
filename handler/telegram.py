import os
import base64
import httpx
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ContextTypes
from core.wrapper import TelegramMessageWrapper
from agent.mcp_client import agent
from utils.auth import check_pairing, FRONTEND_URL
from utils.redis import get_or_create_user_identity

load_dotenv()

MODAL_STT_URL = os.getenv(
    "MODAL_STT_URL",
    "https://obliepius13--asha-twi-stt-service-ashastt-transcribe-433a09-dev.modal.run" # noqa
).rstrip("/")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    wrapper = TelegramMessageWrapper(update)
    address = wrapper.sender["address"]
    chat_id = str(update.effective_chat.id if update.effective_chat else "")

    identity_key, user_pairing_code = get_or_create_user_identity(
        "telegram",
        address,
        conversation_id=chat_id,
    )

    if not await check_pairing(user_pairing_code, wrapper):
        return

    try:
        agent_reply = await agent(wrapper, identity_key)
        if agent_reply:
            await wrapper.reply(agent_reply)
    except Exception as e:
        print(f"agent() failed: {e}")
        await wrapper.reply("Hit a snag on my end. Mind trying that again?")


async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    audio = update.message.voice or update.message.audio
    if not audio:
        return

    wrapper = TelegramMessageWrapper(update)
    address = wrapper.sender["address"]
    chat_id = str(update.effective_chat.id if update.effective_chat else "")

    identity_key, user_pairing_code = get_or_create_user_identity(
        "telegram",
        address,
        conversation_id=chat_id,
    )

    if not await check_pairing(user_pairing_code, wrapper):
        return

    try:
        tg_file = await context.bot.get_file(audio.file_id)
        audio_bytes = await tg_file.download_as_bytearray()
        print(f"Downloaded audio message for {address} ({len(audio_bytes)} bytes, duration: {audio.duration}s)") # noqa

        if not MODAL_STT_URL:
            await wrapper.reply("STT endpoint not configured.")
            return

        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(MODAL_STT_URL, json={"audio_base64": audio_b64}) # noqa
            if resp.status_code == 200:
                data = resp.json()
                twi_text = data.get("twi_text", "").strip()
                english_text = data.get("english_text", "").strip()
                print(f"[STT + NLLB Result] {address} -> Twi: '{twi_text}' | Eng: '{english_text}'") # noqa

                if not twi_text and not english_text:
                    await wrapper.reply("Couldn't hear anything in the voice note. Mind trying again?") # noqa
                    return

                # Send dual Twi + English context to agent
                wrapper.text = f"[Spoken in Twi]: {twi_text}\n[Machine Translation]: {english_text}" # noqa

                agent_reply = await agent(wrapper, identity_key)
                if agent_reply:
                    await wrapper.reply(agent_reply)
            else:
                print(f"Modal STT error {resp.status_code}: {resp.text}")
                await wrapper.reply(f"STT processing failed with status {resp.status_code}") # noqa

    except Exception as e:
        print(f"handle_audio error: {e}")
        await wrapper.reply("Could not process the audio message. Mind sending it again?") # noqa


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    user = update.effective_user
    address = user.username if (user and user.username) else str(user.id if user else "unknown") # noqa
    identity_key, user_pairing_code = get_or_create_user_identity("telegram", address) # noqa

    if not user_pairing_code:
        web_link = f"{FRONTEND_URL}/pair?channel=telegram&address={address}"
        reply_text = f"Welcome to ASHA!\n\nPlease link your hardware device by clicking here:\n{web_link}" # noqa
        await update.message.reply_text(reply_text)
    else:
        await update.message.reply_text("ASHA is online and ready for your commands!") # noqa
