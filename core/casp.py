from caspian_sdk import CommClient
import os
from dotenv import load_dotenv
load_dotenv()


client = CommClient()
telegram = client.connect_telegram(bot_token=os.getenv("Telegram_bot", " "))
inbox = client.connect_email()
# client.connect_discord(bot_token=os.getenv("DISCORD_BOT_TOKEN"))
