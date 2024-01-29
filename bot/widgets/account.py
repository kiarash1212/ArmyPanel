from telegram import InlineKeyboardButton

from bot.context.messages import BACK_BTN_MSG, PAY_WITH_WALLET_MSG, PAY_WITH_CART_MSG, TEST_ACCOUNT_MSG, BACK_MSG, \
    BUY_SERVICE_MSG, DEPOSIT_MSG, REFERRAL_LINK_MSG, REFERRAL_BANNER_MSG


def get_account_info_inline_keyboard():
    return [
        [
            InlineKeyboardButton(DEPOSIT_MSG, callback_data=str("account_deposit"))
        ]
    ]

def get_referral_info_inline_keyboard():
    return [
        [
            InlineKeyboardButton(REFERRAL_BANNER_MSG, callback_data=str("referral_banner")),
        ]
    ]