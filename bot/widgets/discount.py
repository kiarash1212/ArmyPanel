from telegram import InlineKeyboardButton


def discount_back_inline_keyboard(callback):
    return [
        [
            InlineKeyboardButton("بازگشت به صفحه سفارش", callback_data=str(callback)),
        ]
    ]

def discount_next_inline_keyboard(callback):
    return [
        [
            InlineKeyboardButton("ادامه", callback_data=str(callback)),
        ]
    ]