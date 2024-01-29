from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot.context.config import SERVICE_ROUTES
from bot.context.messages import HELP_START_MSG, ANDROID_TEXT, IOS_TEXT, MAC_TEXT, WINDOWS_TEXT, LINUX_TEXT, FAQ_TEXT, AMOOZESH_MSG_TEXT
from bot.widgets.help import get_help_inline_keyboard, get_help_back_inline_keyboard


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reply_markup = InlineKeyboardMarkup(
        get_help_inline_keyboard()
    )
    await update.message.reply_text(HELP_START_MSG, reply_markup=reply_markup)
    return SERVICE_ROUTES

async def amoozesh_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(AMOOZESH_MSG_TEXT)
    return SERVICE_ROUTES

async def help_inline_handler(update, context):
    query = update.callback_query
    reply_markup = InlineKeyboardMarkup(
        get_help_inline_keyboard()
    )
    await query.edit_message_text(
        text=HELP_START_MSG, reply_markup=reply_markup
    )
    return SERVICE_ROUTES


async def help_device_inline_handler(update, context):
    query = update.callback_query
    reply_markup = InlineKeyboardMarkup(
        get_help_back_inline_keyboard()
    )
    device = str(query.data).replace('device_', '')

    text = FAQ_TEXT
    if device == 'android':
        text = ANDROID_TEXT
    elif device == 'ios':
        text = IOS_TEXT
    elif device == 'windows':
        text = WINDOWS_TEXT
    elif device == 'mac':
        text = MAC_TEXT
    elif device == 'linux':
        text = LINUX_TEXT

    await query.edit_message_text(
        text=text, reply_markup=reply_markup
    )
    return SERVICE_ROUTES
