import os

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'configbot.settings')
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
django.setup()
from telegram import InlineKeyboardMarkup

from bot.context.config import SERVICE_ROUTES
from bot.context.messages import DEPOSIT_CARD_ACCEPT_FACTOR_MSG, NO_TRS_CARD_MSG, WAITING_TX_VALIDATION_MSG, \
    INVALID_TX_ID_MSG
from bot.widgets.deposit import deposit_confirm_card_inline_keyboard
from models.transactions.models import Transaction
from models.user.models import UserModel
from utils.telegram.message import send_message_telegram

import re
import time

import requests

from models.configure.models import SiteConfiguration


def weopad_login(mobile):
    url = "http://pertoonfa.shop/otp.php?mobileNumber={}".format(mobile)

    response = requests.request("GET", url)
    print(response.text)
    try:
        result = response.json()
    except Exception as e:
        return {
            'keyId': None,
            'status': False,
            'e': str(e)
        }

    if response.status_code == 200:
        return {
            'keyId': result['keyId'],
            'status': True,
        }

    return {
        'keyId': None,
        'status': False
    }


def weopad_get_token(key, mobile, otp):
    url = "http://pertoonfa.shop/token.php?key={}&otp={}&mobileNumber={}".format(
        key,
        otp,
        mobile,
    )

    response = requests.request("GET", url)
    print(url)
    print(response.text)

    try:
        result = response.json()
    except Exception as e:
        return {
            'token': None,
            'status': False,
            'e': str(e)
        }

    if response.status_code == 200:
        if 'token' in result:
            return {
                'token': result['token']['accessToken'],
                'status': True,
            }

    return {
        'token': None,
        'status': False
    }


def weopad_refresh_token(token):
    url = "http://pertoonfa.shop/refresh.php?accessToken={}".format(token)

    try:
        response = requests.request("GET", url)
        result = response.json()
    except Exception as e:
        return {
            'token': None,
            'status': False,
            'e': str(e)
        }

    if response.status_code == 200:
        return {
            'token': result['accessToken'],
            'status': True,
        }

    return {
        'token': None,
        'status': False
    }


def weopad_transaction_check(token, track_id):
    url = "http://pertoonfa.shop/check.php?accessToken={}".format(token)

    try:
        response = requests.request("GET", url)
        print(response.text)
        result = response.json()

    except:
        return {
            'amount': 0,
            'track_id': '',
            'card_id': '',
            'status': "token",
        }

    if response.status_code == 200:
        for item in result:
            numbers = re.findall(r'\d+', item['description'])
            if track_id in numbers:
                return {
                    'amount': item['amount'] / 10,
                    'track_id': numbers[3],
                    'card_id': track_id,
                    'status': 'searched'
                }
    return {
        'amount': 0,
        'track_id': '',
        'card_id': '',
        'status': False
    }


def check_and_process_data(key, mobile, counter=0):
    configure = SiteConfiguration.get_solo()
    if configure.wepad_code:
        token = weopad_get_token(key, mobile, configure.wepad_code)
        configure.wepad_code = None
        configure.wepad_token = token['token']
        configure.save(update_fields=['wepad_code', 'wepad_token'])
        return True
    else:
        if counter >= 15:
            return False
        counter += 1
        time.sleep(2)
        return check_and_process_data(key, mobile, counter)


def wepoad_main(card_id, user):
    configure = SiteConfiguration.get_solo()
    token = False
    reply_markup = None

    response = weopad_transaction_check(configure.wepad_token, card_id)
    print(response)
    # if response['status'] == 'token':
    #     new_token = weopad_refresh_token(configure.wepad_token)
    #     if new_token['token']:
    #         configure = SiteConfiguration.get_solo()
    #         configure.wepad_token = new_token['token']
    #         configure.save()
    #         response = weopad_transaction_check(new_token['token'], card_id)
    print(response['status'] == 'token')
    if response['status'] == 'token':
        send_otp = weopad_login(configure.wepad_mobile)
        if send_otp['status']:
            key = send_otp['keyId']
            result_data = check_and_process_data(key, configure.wepad_mobile)
            if result_data:
                configure = SiteConfiguration.get_solo()
                token = configure.wepad_token
        if token:
            response = weopad_transaction_check(token, card_id)

    if response['status'] and response['track_id']:
        msg_text = DEPOSIT_CARD_ACCEPT_FACTOR_MSG.format(
            int(response['amount']),
            response['track_id']
        )
        user_model = UserModel.objects.get(telegram_id=user.id)

        tx_id_exists = Transaction.objects.filter(track_id=response['track_id']).exists()

        if tx_id_exists:
            msg_text = NO_TRS_CARD_MSG
        else:
            transaction_model, is_created = Transaction.objects.get_or_create(
                track_id=response['track_id'],
                card_id=response['card_id'],
                amount=float(response['amount']),
                status='suspended',
                user=user_model,
                type='card'
            )
            reply_markup = InlineKeyboardMarkup(
                deposit_confirm_card_inline_keyboard(transaction_model.id),
            ).to_dict()
    elif response['status'] and response['track_id']:
        msg_text = WAITING_TX_VALIDATION_MSG.format(
            response['amount']
        )
    else:
        msg_text = INVALID_TX_ID_MSG

    send_message_telegram(user.id, msg_text, reply_markup)

    return SERVICE_ROUTES


user_model = UserModel.objects.get(id=1)
wepoad_main(6119861046392147, user_model)
