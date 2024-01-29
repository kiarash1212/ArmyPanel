from utils.telegram.message import send_message_telegram
import concurrent

from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from telegram import Bot

from configbot.settings import TELEGRAM_TOKEN
from models.notification.models import Notification
from models.order.models import Order
from models.user.models import UserModel


@receiver(m2m_changed, sender=Notification.users.through)
def send_message(sender, instance, action, **kwargs):
    if action == 'post_add':
        if instance.users.all() and not instance.all_user:

            users = instance.users.all().values_list('telegram_id', flat=True)

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future_to_user = {executor.submit(send_message_telegram, user, instance.text): user for user in users}

                for future in concurrent.futures.as_completed(future_to_user):
                    future_to_user[future]
    return True


@receiver(m2m_changed, sender=Notification.country.through, dispatch_uid="handle_country_change")
def handle_country_change(sender, instance, action, pk_set, **kwargs):
    if action == 'post_add':
        users = []
        if instance.country.all() and not instance.all_user:
            orders = []
            for s in instance.country.all():
                orders += Order.objects.filter(enable=True, service__country_id=s.id)

            for item in orders:
                user_id = item.user.telegram_id

                if user_id not in users:  # بررسی تکراری بودن ارسال پیام
                    users.append(user_id)

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future_to_user = {executor.submit(send_message_telegram, user, instance.text): user for user in users}

                for future in concurrent.futures.as_completed(future_to_user):
                    future_to_user[future]


@receiver(m2m_changed, sender=Notification.server.through, dispatch_uid="handle_server_change")
def handle_server_change(sender, instance, action, pk_set, **kwargs):
    if action == 'post_add':
        users = []

        if instance.server.all() and not instance.all_user:
            servers = instance.server.all()
            orders = []
            for s in servers:
                orders += Order.objects.filter(enable=True, node__server_id=s.id)

            for item in orders:
                user_id = item.user.telegram_id

                if user_id not in users:  # بررسی تکراری بودن ارسال پیام
                    users.append(user_id)

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future_to_user = {executor.submit(send_message_telegram, user, instance.text): user for user in users}

                for future in concurrent.futures.as_completed(future_to_user):
                    future_to_user[future]


@receiver(m2m_changed, sender=Notification.service.through, dispatch_uid="handle_service_change")
def handle_service_change(sender, instance, action, pk_set, **kwargs):
    if action == 'post_add':
        users = []

        if instance.service.all() and not instance.all_user:
            services = instance.service.all()
            orders = []
            for s in services:
                orders += Order.objects.filter(enable=True, service_id=s.id)

            for item in orders:
                user_id = item.user.telegram_id

                if user_id not in users:
                    users.append(user_id)

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future_to_user = {executor.submit(send_message_telegram, user, instance.text): user for user in users}

                for future in concurrent.futures.as_completed(future_to_user):
                    future_to_user[future]


@receiver(post_save, sender=Notification)
def general_message(sender, instance, **kwargs):
    if instance.all_user:
        users = UserModel.objects.filter(is_active=True, is_staff=False).values_list('telegram_id', flat=True)

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_user = {executor.submit(send_message_telegram, user, instance.text): user for user in users}

            for future in concurrent.futures.as_completed(future_to_user):
                user = future_to_user[future]
