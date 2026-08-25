import os
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder
from telegram.request import HTTPXRequest

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("Telegram_bot") or os.getenv("TELEGRAM_TOKEN") # noqa

request_config = HTTPXRequest(
    connect_timeout=30.0,
    read_timeout=30.0,
    write_timeout=30.0,
    pool_timeout=30.0,
)

telegram_app = (
    ApplicationBuilder()
    .token(TOKEN)
    .request(request_config)
    .build()
    if TOKEN
    else None
)
