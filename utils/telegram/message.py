import json

import requests
import asyncio
from configbot.settings import TELEGRAM_TOKEN
# from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
# from telegram.request import HTTPXRequest
# from telegram.ext import Application
#
# bot = Bot(token=TELEGRAM_TOKEN, request=HTTPXRequest(proxy_url="socks5://:@127.0.0.1:1080"))
# application = Application.builder().bot(bot).build()
# loop = asyncio.get_event_loop()

def send_message_telegram(chat_id, text, inline_keyboard=None, file=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    if file:
        file.seek(0)
        byte_image = file.getvalue()
        return send_telegram_photo(byte_image, text, chat_id)

    payload = {
        'text': text,
        'chat_id': chat_id,
        'parse_mode': 'html'
    }

    if inline_keyboard:
        payload.update({
            'reply_markup': json.dumps(inline_keyboard)
        })

    # while True:
    #     try:
    response = requests.post(url, data=payload,
                             verify=False, timeout=20)

    return response.status_code
    # keyboard = None
    # if inline_keyboard:
    #     for row in inline_keyboard:
    #         for i,j in enumerate(row):
    #             row[i] = InlineKeyboardButton(j[0], callback_data=j[1])
    #     keyboard = InlineKeyboardMarkup(inline_keyboard)
    # try:
    #     loop.run_until_complete(bot.send_message(chat_id, text, reply_markup=keyboard, parse_mode='html'))
    # except:pass
    #
    # return 200
def send_telegram_photo(photo_bytes, text, chat_id):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"

    files = {'photo': ("image.png", photo_bytes, "image/png")}
    payload = {
        'chat_id': chat_id,
        'caption': text,
        'parse_mode': 'html'
    }
    response = requests.post(url, data=payload, files=files)
    return response
