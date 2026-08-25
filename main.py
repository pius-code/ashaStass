import os
import threading
import uvicorn
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, filters, ContextTypes

from core.telegram import telegram_app
from core.wrapper import TelegramMessageWrapper
from utils.redis import get_or_create_user_identity
from agent.mcp_client import agent
from core.fastapi import app
from routes.ashaStass import router as asha_router
import utils.middleware # noqa

load_dotenv()

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000").rstrip("/")

app.include_router(asha_router)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    user = update.effective_user
    address = user.username if (user and user.username) else str(user.id if user else "unknown")
    identity_key, user_pairing_code = get_or_create_user_identity("telegram", address)

    if not user_pairing_code:
        web_link = f"{FRONTEND_URL}/pair?channel=telegram&address={address}"
        reply_text = f"Welcome to ASHA!\n\nPlease link your hardware device by clicking here:\n{web_link}"
        await update.message.reply_text(reply_text)
    else:
        await update.message.reply_text("ASHA is online and ready for your commands!")


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

    if not user_pairing_code:
        web_link = f"{FRONTEND_URL}/pair?channel=telegram&address={address}"
        reply_text = f"Looks like your account is unpaired!\n\nPlease click here to log in and pair your device:\n{web_link}"
        await update.message.reply_text(reply_text)
        return

    try:
        agent_reply = await agent(wrapper, identity_key)
        if agent_reply:
            await update.message.reply_text(agent_reply)
    except Exception as e:
        print(f"agent() failed: {e}")
        await update.message.reply_text("Hit a snag on my end. Mind trying that again?")


def start_telegram():
    if not telegram_app:
        print("Telegram bot token not found, skipping bot...")
        return
    print("ASHA bot is listening for Telegram messages...")
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    telegram_app.run_polling(bootstrap_retries=-1)


def main():
    tg_thread = threading.Thread(target=start_telegram, daemon=True)
    tg_thread.start()
    print("Starting ashaStass API server on port 8081...")
    uvicorn.run(app, host="0.0.0.0", port=8081)


if __name__ == "__main__":
    main()
