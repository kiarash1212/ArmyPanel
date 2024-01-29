import datetime
import io
import json
import logging
import threading

import qrcode
from django.utils import timezone
from telegram import Update, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.error import BadRequest, TimedOut
from telegram.ext import ContextTypes

from bot.context.config import SERVICE_ROUTES, START_ROUTES
from bot.context.messages import NOT_HAVE_ANY_SERVICE_MSG, ORDER_SUCCESS_MSG, ORDER_SUCCESS_DETAILS_MSG, \
    ERROR_IN_REGISTER_MSG, SERVICE_NOT_EXIST_MSG, NOT_ENOUGH_BALANCE_MSG, SEARCHING_SERVICES_MSG, HAVE_ANY_SERVICE_MSG, \
    ORDER_DETAILS_MSG, ORDER_NOT_EXIST_MSG, ORDER_CONFIG_MSG, ORDER_EXTENSION_FACTOR_PAYING_MSG, ORDER_EXTENSION_NO_MSG, \
    ORDER_EXTENSION_ERROR_MSG, BACK_BTN_MSG, ORDER_TEST_EXTENSION_NO_MSG, ORDER_CANCELED_MSG, \
    ORDER_EXTENSION_IP_FACTOR_PAYING_MSG
from bot.widgets.order import get_order_list_inline_keyboard, get_order_details_inline_keyboard, \
    get_order_back_inline_keyboard, get_order_link_inline_keyboard
from models.configure.models import SiteConfiguration
from models.order.models import Order, Discount
from models.order.utils.order_create import create_order
from models.service.models import Service
from models.transactions.models import Transaction
from models.user.models import UserModel

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


async def order_list_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    orders = []
    try:
        user_model = UserModel.objects.get(telegram_id=update.message.from_user.id)
        orders = Order.objects.filter(user_id=user_model.id, enable=True)
        if orders:
            await update.message.reply_text(text="لطفا انتخاب کنید 👇", reply_markup=ReplyKeyboardMarkup(
                [[SEARCHING_SERVICES_MSG], [BACK_BTN_MSG]], one_time_keyboard=False, resize_keyboard=True))
            replay_message = HAVE_ANY_SERVICE_MSG
        else:
            replay_message = NOT_HAVE_ANY_SERVICE_MSG
    except UserModel.DoesNotExist:
        replay_message = NOT_HAVE_ANY_SERVICE_MSG

    reply_markup = InlineKeyboardMarkup(
        get_order_list_inline_keyboard(orders, offset=0)
    )

    await update.message.reply_text(text=replay_message, reply_markup=reply_markup)
    return SERVICE_ROUTES


async def order_list_inline_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    offset = int(query.data.replace('order_list_', ''))
    orders = []
    try:
        user_model = UserModel.objects.get(telegram_id=query.from_user.id)
        orders = Order.objects.filter(user_id=user_model.id, enable=True)
        if orders:
            replay_message = HAVE_ANY_SERVICE_MSG
        else:
            replay_message = NOT_HAVE_ANY_SERVICE_MSG
    except UserModel.DoesNotExist:
        replay_message = NOT_HAVE_ANY_SERVICE_MSG

    reply_markup = InlineKeyboardMarkup(
        get_order_list_inline_keyboard(orders, offset)
    )
    await query.edit_message_text(text=replay_message, reply_markup=reply_markup)
    return SERVICE_ROUTES


async def order_details_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    order_id = query.data.replace('order_details_', '')

    try:
        order_model = Order.objects.get(id=order_id)

        enable = "غیرفعال ❌"
        if order_model.enable:
            enable = "فعال✅"

        total_value = order_model.service.count
        if total_value > 1:
            total_value = "{} گیگابایت".format(total_value)
        else:
            total_value = "{} مگابایت".format(int(total_value * 1024))

        total_used = order_model.total
        if total_used > 1024:
            total_used = "{} گیگابایت".format(round(total_used / 1024, 2))
        else:
            total_used = "{} مگابایت".format(int(total_used))

        total_free = order_model.service.count - (order_model.total / 1024)
        if total_free > 1:
            total_free = "{} گیگابایت".format(round(total_free, 2))
        else:
            if total_free < 0:
                total_free = 0
            total_free = "{} مگابایت".format(int(total_free * 1024))

        message = ORDER_DETAILS_MSG.format(
            "{} گیگ، {} روزه".format(
                order_model.service.count,
                order_model.service.periods.value
            ),
            order_model.service.country.name,
            order_model.service.user_count,
            total_value,
            total_used,
            total_free,
            order_model.published_shamsi(),
            order_model.expired_date_shamsi(),
            enable,
            "{:,} تومان".format(int(order_model.price))
        )
        reply_markup = InlineKeyboardMarkup(
            get_order_details_inline_keyboard(order_model)
        )
    except Order.DoesNotExist:
        message = ORDER_NOT_EXIST_MSG
        reply_markup = None

    try:
        await query.delete_message()
    except BadRequest:
        pass

    await context.bot.send_message(
        chat_id=query.from_user.id,
        text=message,
        reply_markup=reply_markup,
        parse_mode='html'
    )
    return SERVICE_ROUTES


async def order_extension_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    order_id = query.data.replace('order_extension_', '')
    try:
        order_model = Order.objects.get(id=order_id, is_test_config=False)
        configure = SiteConfiguration.get_solo()
        ext_service_role = configure.ext_service_role.split('-')

        today = timezone.now()

        delta2 = datetime.timedelta(days=int(ext_service_role[1]))

        service = order_model.service

        if order_model.is_test_config:
            await query.answer(text=ORDER_TEST_EXTENSION_NO_MSG, show_alert=True)
            return SERVICE_ROUTES

        if not order_model.expired_date:
            await query.answer(text=ORDER_EXTENSION_NO_MSG, show_alert=True)
            return SERVICE_ROUTES

        service_count = order_model.service.count - (order_model.service.count * configure.alarm_value) / 100
        if (
                order_model.expired_date >= today >= order_model.expired_date - delta2 or order_model.total / 1024 >= service_count) and order_model.enable:
            price = service.price - ((service.price * service.price_discount) / 100)
            discount = service.price_discount
        elif not order_model.enable and order_model.expired_date >= today:
            price = service.price - ((service.price * service.price_discount) / 100)
            discount = service.price_discount
        elif not order_model.enable and order_model.expired_date <= today:
            price = service.price - ((service.price * service.price_normal_discount) / 100)
            discount = service.price_normal_discount
        else:
            await query.answer(text=ORDER_EXTENSION_NO_MSG, show_alert=True)
            return SERVICE_ROUTES

        message = ORDER_EXTENSION_FACTOR_PAYING_MSG.format(
            service.country.name,
            service.periods.value,
            service.user_count,
            service.count,
            discount,
            int(price)
        )
        reply_markup = InlineKeyboardMarkup(
            get_order_back_inline_keyboard(order_model, 'order_accept_extension_')
        )
        await query.edit_message_text(text=message, reply_markup=reply_markup, parse_mode='html')
    except Order.DoesNotExist:
        await query.answer(text=ORDER_NOT_EXIST_MSG, show_alert=True)
    return SERVICE_ROUTES


async def order_extension_accept_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    order_id = query.data.replace('order_accept_extension_', '')

    try:
        order_model = Order.objects.get(id=order_id, is_test_config=False)
        configure = SiteConfiguration.get_solo()
        ext_service_role = configure.ext_service_role.split('-')

        today = timezone.now()

        delta2 = datetime.timedelta(days=int(ext_service_role[1]))

        service = order_model.service

        service_count = order_model.service.count - (order_model.service.count * configure.alarm_value) / 100

        if (order_model.expired_date >= today >= order_model.expired_date - delta2 or order_model.total / 1024 >= service_count) and order_model.enable:
            price = service.price - ((service.price * service.price_discount) / 100)
        elif not order_model.enable and order_model.expired_date >= today:
            price = service.price - ((service.price * service.price_discount) / 100)
        elif not order_model.enable and order_model.expired_date <= today:
            price = service.price - ((service.price * service.price_normal_discount) / 100)
        else:
            await query.answer(text=ORDER_EXTENSION_NO_MSG, show_alert=True)
            return SERVICE_ROUTES

        if order_model.user.balance < price:
            await query.answer(text=NOT_ENOUGH_BALANCE_MSG, show_alert=True)
            return SERVICE_ROUTES

        config_url = order_model.create_config(is_extension=True)

        if config_url:
            order_model.user.balance -= price
            order_model.user.save(update_fields=['balance'])

            order_model.reset_data()

            order_model.price = price
            order_model.expired_date = timezone.now() + datetime.timedelta(days=order_model.service.periods.value)
            order_model.published = timezone.now()
            order_model.enable = True
            order_model.alarm_send_data = None
            order_model.save()

            await query.edit_message_text(text=ORDER_SUCCESS_MSG.format(order_model.id), reply_markup=None)

        if config_url:
            await context.bot.send_message(
                chat_id=order_model.user.telegram_id,
                text=ORDER_CONFIG_MSG.format(order_model.id, config_url),
                parse_mode='html'
            )
            await context.bot.send_message(chat_id=order_model.user.telegram_id, text=ORDER_SUCCESS_DETAILS_MSG)
        else:
            await context.bot.send_message(
                chat_id=order_model.user.telegram_id,
                text=ORDER_CANCELED_MSG.format(order_model.id),
                parse_mode='html'
            )
    except Order.DoesNotExist:
        await query.answer(text=ORDER_NOT_EXIST_MSG, show_alert=True)
    return SERVICE_ROUTES


async def order_extension_ip_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    order_id = query.data.replace('order_extension_ip_', '')

    try:
        order_model = Order.objects.get(id=order_id, is_test_config=False)
        configure = SiteConfiguration.get_solo()
        ext_service_role = configure.ext_service_role.split('-')

        today = timezone.now()

        delta2 = datetime.timedelta(days=int(ext_service_role[1]))

        three_days_later = today + delta2
        service = order_model.service

        if order_model.is_test_config:
            await query.answer(text=ORDER_TEST_EXTENSION_NO_MSG, show_alert=True)
            return SERVICE_ROUTES

        if not order_model.expired_date:
            await query.answer(text=ORDER_EXTENSION_NO_MSG, show_alert=True)
            return SERVICE_ROUTES

        service_count = order_model.service.count - (order_model.service.count * configure.alarm_value) / 100
        if order_model.expired_date >= today >= order_model.expired_date - delta2 or order_model.total / 1024 >= service_count or not order_model.enable:
            price = service.price + ((service.price * service.price_ip_discount) / 100)
            discount = service.price_ip_discount
        else:
            await query.answer(text=ORDER_EXTENSION_NO_MSG, show_alert=True)
            return SERVICE_ROUTES

        message = ORDER_EXTENSION_IP_FACTOR_PAYING_MSG.format(
            service.country.name,
            service.periods.value,
            service.user_count,
            service.count,
            discount,
            int(price)
        )
        reply_markup = InlineKeyboardMarkup(
            get_order_back_inline_keyboard(order_model, 'order_accept_extension_ip_')
        )

        await query.edit_message_text(text=message, reply_markup=reply_markup, parse_mode='html')
    except Order.DoesNotExist:
        await query.answer(text=ORDER_NOT_EXIST_MSG, show_alert=True)

    return SERVICE_ROUTES


async def order_extension_ip_accept_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    order_id = query.data.replace('order_accept_extension_ip_', '')

    try:
        order_model = Order.objects.get(id=order_id, is_test_config=False)
        configure = SiteConfiguration.get_solo()
        ext_service_role = configure.ext_service_role.split('-')

        today = timezone.now()

        delta2 = datetime.timedelta(days=int(ext_service_role[1]))

        three_days_later = today + delta2
        service = order_model.service

        service_count = order_model.service.count - (order_model.service.count * configure.alarm_value) / 100
        if order_model.expired_date >= today >= order_model.expired_date - delta2 or order_model.total / 1024 >= service_count or not order_model.enable:
            price = service.price + ((service.price * service.price_ip_discount) / 100)
        else:
            await query.answer(text=ORDER_EXTENSION_NO_MSG, show_alert=True)
            return SERVICE_ROUTES

        if order_model.user.balance < price:
            await query.answer(text=NOT_ENOUGH_BALANCE_MSG, show_alert=True)
            return SERVICE_ROUTES

        config_url = order_model.create_config(ip_server=True, is_extension=True)

        if config_url:
            order_model.user.balance -= price
            order_model.user.save(update_fields=['balance'])

            order_model.reset_data()

            order_model.price = price
            order_model.expired_date = timezone.now() + datetime.timedelta(days=order_model.service.periods.value)
            order_model.published = timezone.now()
            order_model.alarm_send_data = None
            order_model.enable = True
            order_model.save()

            await query.edit_message_text(text=ORDER_SUCCESS_MSG.format(order_model.id), reply_markup=None)

            await context.bot.send_message(
                chat_id=order_model.user.telegram_id,
                text=ORDER_CONFIG_MSG.format(order_model.id, config_url),
                parse_mode='html'
            )
            await context.bot.send_message(chat_id=order_model.user.telegram_id, text=ORDER_SUCCESS_DETAILS_MSG)
        else:
            await context.bot.send_message(
                chat_id=order_model.user.telegram_id,
                text=ORDER_CANCELED_MSG.format(order_model.id),
                parse_mode='html'
            )
            return START_ROUTES
    except Order.DoesNotExist:
        await query.answer(text=ORDER_NOT_EXIST_MSG, show_alert=True)
    return SERVICE_ROUTES


async def order_config_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    order_id = query.data.replace('order_link_', '')

    try:
        order_model = Order.objects.get(id=order_id)

        if not order_model.enable:
            await query.answer(text=ORDER_EXTENSION_ERROR_MSG, show_alert=True)
            return SERVICE_ROUTES

        message = ORDER_CONFIG_MSG.format(
            order_model.id,
            order_model.config
        )

        reply_markup = InlineKeyboardMarkup(
            get_order_link_inline_keyboard(order_model)
        )
    except Order.DoesNotExist:
        message = ORDER_NOT_EXIST_MSG
        reply_markup = None

    qr = qrcode.QRCode()
    qr.add_data(order_model.config)
    qr.make(fit=True)

    byte_stream = io.BytesIO()
    qr.make_image().save(byte_stream, format='PNG')
    byte_stream.seek(0)
    byte_image = byte_stream.getvalue()

    await query.delete_message()
    await context.bot.sendPhoto(
        chat_id=query.from_user.id,
        photo=byte_image,
        caption=message,
        reply_markup=reply_markup,
        parse_mode='html'
    )

    return SERVICE_ROUTES


async def order_qrcode_handler(update, context):
    query = update.callback_query
    order_id = query.data.replace('order_qrcode_', '')

    order_model = Order.objects.get(id=order_id)

    qr = qrcode.QRCode()
    qr.add_data(order_model.config)
    qr.make(fit=True)

    byte_stream = io.BytesIO()
    qr.make_image().save(byte_stream, format='PNG')
    byte_stream.seek(0)
    byte_image = byte_stream.getvalue()

    await context.bot.sendPhoto(
        chat_id=query.from_user.id,
        photo=byte_image,
        caption="",
        parse_mode='html'
    )
    return SERVICE_ROUTES


async def order_create_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    referral_amount, user_referral, discount_model = 0, None, None
    try:
        user_model = UserModel.objects.get(telegram_id=query.from_user.id)
        data = json.loads(user_model.data)
    except UserModel.DoesNotExist:
        await query.answer(text=ERROR_IN_REGISTER_MSG, show_alert=True)
        return SERVICE_ROUTES

    count = 1
    if 'pay_multi_wallet_' in query.data:
        server_id, count = query.data.replace('pay_multi_wallet_', '').split('_')
        count = int(count)
    else:
        server_id = query.data.replace('pay_wallet_', '')

    try:
        service_model = Service.objects.get(id=server_id)
    except Service.DoesNotExist:
        await query.answer(text=SERVICE_NOT_EXIST_MSG, show_alert=True)
        return SERVICE_ROUTES

    price = service_model.price * count
    if 'pay_multi_wallet_' in query.data:
        price = (service_model.price - (
                (service_model.price * service_model.price_multi_discount) / 100)) * count

    if 'discount' in data:
        try:
            discount_model = Discount.objects.get(id=data['discount'])
            price = price - ((price * discount_model.amount) / 100)
        except Discount.DoesNotExist:
            discount_model = None

    if user_model.balance >= price:

        try:
            await query.edit_message_text(text=ORDER_SUCCESS_MSG)
        except TimedOut:
            pass

        x = threading.Thread(target=create_order, args=(
            service_model, user_model, discount_model, count, referral_amount, price
        ))
        x.start()
    else:
        await query.answer(text=NOT_ENOUGH_BALANCE_MSG, show_alert=True)

    user_model.data = json.dumps({})
    user_model.save(update_fields=['data'])

    return SERVICE_ROUTES
