from telegram import Update
from telegram.ext import ContextTypes

from models.configure.models import SiteConfiguration


async def handle_group_messages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    message = update.message
    print(message.chat.type)
    print(message.text)
    if message.chat.type == 'group' or message.chat.type == 'supergroup':
        text = message.text
        if 'code:' in text:
            configure = SiteConfiguration.get_solo()
            configure.wepad_code = text.split("code: ")[1]
            configure.save(update_fields=['wepad_code'])