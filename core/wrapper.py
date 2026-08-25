from telegram import Update
from telegram.constants import ChatAction


class TelegramMessageWrapper:
    def __init__(self, update: Update, override_text: str | None = None):
        self.update = update
        if override_text is not None:
            self.text = override_text
        else:
            self.text = update.message.text if update.message and update.message.text else "" # noqa
        self.channel = "telegram"
        user = update.effective_user
        address = user.username if (user and user.username) else str(user.id if user else "unknown") # noqa
        self.sender = {"address": address}

    async def reply(self, text: str):
        if self.update.message:
            await self.update.message.reply_text(text)

    async def send_typing(self):
        if self.update.effective_chat:
            await self.update.effective_chat.send_action(ChatAction.TYPING)
