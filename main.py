import os
import threading
import uvicorn
from dotenv import load_dotenv
from telegram.ext import CommandHandler, MessageHandler, filters
from core.telegram import telegram_app
from core.fastapi import app
from routes.ashaStass import router as asha_router
from handler.telegram import handle_message, handle_audio, start
load_dotenv()

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000").rstrip("/")

app.include_router(asha_router)


def start_telegram():
    if not telegram_app:
        print("Telegram bot token not found, skipping bot...")
        return
    print("ASHA bot is listening for Telegram messages...")
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    telegram_app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_audio))
    telegram_app.run_polling(stop_signals=None, bootstrap_retries=-1)


def main():
    tg_thread = threading.Thread(target=start_telegram, daemon=True)
    tg_thread.start()
    print("Starting ashaStass API server on port 8081...")
    uvicorn.run(app, host="0.0.0.0", port=8081)


if __name__ == "__main__":
    main()
