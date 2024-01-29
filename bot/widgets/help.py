from telegram import InlineKeyboardButton

from bot.context.messages import ANDROID_MSG, WINDOWS_MSG, LINUX_MSG, MAC_MSG, IOS_MSG, FAQ_MSG, BACK_BTN_MSG


def get_help_inline_keyboard():
    keyboard = [
        [
            InlineKeyboardButton(ANDROID_MSG, callback_data=str('device_android')),
            InlineKeyboardButton(IOS_MSG, callback_data=str('device_ios')),
        ],
        [
            InlineKeyboardButton(WINDOWS_MSG, callback_data=str('device_windows')),
            InlineKeyboardButton(MAC_MSG, callback_data=str('device_mac')),
        ],
        [
            InlineKeyboardButton(LINUX_MSG, callback_data=str('device_linux')),
            InlineKeyboardButton(FAQ_MSG, callback_data=str('device_faq')),
        ]
    ]
    return keyboard


def get_help_back_inline_keyboard():
    keyboard = [
        [
            InlineKeyboardButton(BACK_BTN_MSG, callback_data=str(f"help_back")),
        ]
    ]
    return keyboard
