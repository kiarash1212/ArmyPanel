import asyncio
import datetime
import io
import random
import threading
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

import qrcode
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from telegram import Bot

from bot.context.messages import EMERGENCY_MSG
from configbot.settings import TELEGRAM_TOKEN
from models.configure.models import Account
from models.emergency.models import Emergency
from models.order.models import Order
from utils.api.account import create_account
from utils.api.node import get_config_url
from utils.telegram.message import send_telegram_photo


def send_config_orders(orders, instance):
    for item in orders:
        node = instance.emergency_node
        server = instance.emergency_node.server

        account = None
        user_pass = f"{item.user.telegram_id}{random.randint(10000, 99999)}"

        # Fetch new token for login
        if not Account.objects.filter(username=user_pass, password=user_pass).exists():
            server.get_token()

            result = create_account(
                server,
                {
                    'username': user_pass,
                    'password': user_pass,
                    'value': instance.value * 1024,
                    'expireTime': (timezone.now() + datetime.timedelta(days=instance.day)).timestamp()
                }
            )

            if 'type' in result:
                if result['type'] == 'success':
                    account = Account.objects.create(
                        username=user_pass,
                        password=user_pass,
                    )
                    instance.accounts.add(account)
        else:
            account = Account.objects.get(username=user_pass)

        account.get_token(server)
        node_response = get_config_url(server, node, account)

        parsed_url = urlparse(node_response['data'])
        query_params = parse_qs(parsed_url.query)
        if 'flow' in query_params:
            del query_params['flow']
        new_query = urlencode(query_params, doseq=True)

        new_url_parts = parsed_url._replace(query=new_query)
        new_address = urlunparse(new_url_parts)

        address, name = new_address.split("#")

        config = f"{address}#user{item.user.id}_{instance.value}GB_{instance.day}DAYS_V2RayArmy"

        qr = qrcode.QRCode()
        qr.add_data(config)
        qr.make(fit=True)

        byte_stream = io.BytesIO()
        qr.make_image().save(byte_stream, format='PNG')
        byte_stream.seek(0)
        byte_image = byte_stream.getvalue()

        send_telegram_photo(
            chat_id=item.user.telegram_id,
            photo_bytes=byte_image,
            text=EMERGENCY_MSG.format(
                instance.server.name,
                instance.value,
                instance.day,
                config
            ),
        )

    instance.is_lunched = True
    instance.save()


@receiver(post_save, sender=Emergency)
def send_configs(sender, instance, **kwargs):
    if not instance.is_lunched:
        orders = Order.objects.filter(enable=True, node__server_id=instance.server.id)

        t = threading.Thread(target=send_config_orders, args=[orders, instance])
        t.setDaemon(True)
        t.start()