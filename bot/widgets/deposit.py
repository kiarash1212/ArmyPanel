from telegram import InlineKeyboardButton

from bot.context.messages import NEXT_MSG, DEPOSIT_CARD_MSG, DEPOSIT_CRYPTO_MSG, DEPOSIT_CRYPTO_CONFIRMED_MSG, \
    DEPOSIT_CRYPTO_NEXT_MSG


def deposit_account_inline_keyboard():
    return [
        [
            InlineKeyboardButton(NEXT_MSG, callback_data=str("deposit_next"))
        ]
    ]


def deposit_payment_inline_keyboard(amount):
    return [
        [
            InlineKeyboardButton(DEPOSIT_CRYPTO_MSG, callback_data=str(f"payment_crypto_{amount}")),
            InlineKeyboardButton(DEPOSIT_CARD_MSG, callback_data=str(f"payment_card_{amount}"))
        ]
    ]


def deposit_confirm_crypto_inline_keyboard(trs_id):
    return [
        [
            InlineKeyboardButton(DEPOSIT_CRYPTO_NEXT_MSG, callback_data=str(f"payment_crypto_confirmed_{trs_id}")),
        ]
    ]


def deposit_confirm_card_inline_keyboard(trs_id):
    return [
        [
            InlineKeyboardButton(DEPOSIT_CRYPTO_NEXT_MSG, callback_data=str(f"payment_confirmed_card_{trs_id}")),
        ]
    ]