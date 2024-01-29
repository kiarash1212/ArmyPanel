from telegram import InlineKeyboardButton

from bot.context.messages import TICKET_TECHNICAL_BTN, TICKET_FINANCIAL_BTN, TICKET_OTHER_BTN


def ticket_subject_inline_keyboard():
    return [
        [InlineKeyboardButton(TICKET_TECHNICAL_BTN, callback_data=str("ticket_subject_technical"))],
        [InlineKeyboardButton(TICKET_FINANCIAL_BTN, callback_data=str("ticket_request_financial_0"))],
        [InlineKeyboardButton(TICKET_OTHER_BTN, callback_data=str("ticket_request_other_0"))],
    ]
