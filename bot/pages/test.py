import logging

from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot.context.config import SERVICE_ROUTES, START_ROUTES
from bot.context.messages import BUY_SERVICE_WELCOME_MSG, SERVICE_NOT_EXIST_MSG, \
    FACTOR_PAYING_MSG, TEST_FACTOR_PAYING_MSG, ERROR_IN_REGISTER_MSG, ORDER_CONFIG_MSG, ORDER_SUCCESS_DETAILS_MSG, \
    ORDER_SUCCESS_MSG, TEST_SERVICE_EXIST_MSG, ORDER_CANCELED_MSG, ORDER_TEST_SUCCESS_MSG, ORDER_TEST_CANCELED_MSG
from bot.widgets.service import get_country_list_inline_keyboard
from bot.widgets.test import get_test_country_list_inline_keyboard, get_test_factor_paying_inline_keyboard, \
    get_test_back_inline_keyboard
from models.configure.models import SiteConfiguration
from models.order.models import Order
from models.service.models import Service
from models.user.models import UserModel

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


async def test_country_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reply_markup = InlineKeyboardMarkup(
        get_test_country_list_inline_keyboard()
    )
    await update.message.reply_text(BUY_SERVICE_WELCOME_MSG, reply_markup=reply_markup)
    return SERVICE_ROUTES


async def test_country_inline_handler(update, context):
    query = update.callback_query
    reply_markup = InlineKeyboardMarkup(
        get_test_country_list_inline_keyboard()
    )
    await query.edit_message_text(
        text=BUY_SERVICE_WELCOME_MSG, reply_markup=reply_markup
    )
    return SERVICE_ROUTES


async def test_factor_handler(update, context):
    query = update.callback_query
    country_id = str(query.data).replace('test_country_', '')

    configure = SiteConfiguration.get_solo()
    user_model = UserModel.objects.get(telegram_id=query.from_user.id)
    if Order.objects.filter(
            user_id=user_model.id,
            service__country_id=country_id,
            is_test_config=True
    ).count() >= configure.account_test_limition:
        await query.answer(
            text=TEST_SERVICE_EXIST_MSG,
            show_alert=True
        )
        return SERVICE_ROUTES

    try:
        service_model = Service.objects.get(country_id=country_id, is_test=True)
        msg = TEST_FACTOR_PAYING_MSG.format(
            service_model.country.name,
            service_model.periods.value,
            service_model.user_count,
            int(service_model.count * 1024),
        )
        reply_markup = InlineKeyboardMarkup(
            get_test_factor_paying_inline_keyboard(service_model)
        )
    except Service.DoesNotExist:
        msg = SERVICE_NOT_EXIST_MSG
        reply_markup = InlineKeyboardMarkup(
            get_test_back_inline_keyboard()
        )
    await query.edit_message_text(
        text=msg, reply_markup=reply_markup
    )
    return SERVICE_ROUTES


async def test_create_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query

    try:
        user_model = UserModel.objects.get(telegram_id=query.from_user.id)
    except UserModel.DoesNotExist:
        await query.answer(text=ERROR_IN_REGISTER_MSG, show_alert=True)
        return SERVICE_ROUTES

    server_id = query.data.replace('test_get_', '')

    try:
        service_model = Service.objects.get(id=server_id)
    except Service.DoesNotExist:
        await query.answer(text=SERVICE_NOT_EXIST_MSG, show_alert=True)
        return SERVICE_ROUTES

    configure = SiteConfiguration.get_solo()
    if Order.objects.filter(
            user_id=user_model.id,
            service_id=service_model.id,
            is_test_config=True
    ).count() >= configure.account_test_limition:
        await query.answer(text=TEST_SERVICE_EXIST_MSG, show_alert=True)
        return SERVICE_ROUTES

    await query.edit_message_text(text=ORDER_TEST_SUCCESS_MSG)

    order_model = Order.objects.create(
        service_id=service_model.id,
        user_id=user_model.id,
        is_test_config=True
    )

    config_url = order_model.create_config()

    if config_url:
        await context.bot.send_message(
            chat_id=order_model.user.telegram_id,
            text=ORDER_CONFIG_MSG.format(order_model.id, config_url),
            parse_mode='html'
        )
        await context.bot.send_message(chat_id=user_model.telegram_id, text=ORDER_SUCCESS_DETAILS_MSG)
    else:

        order_model.delete()
        await context.bot.send_message(
            chat_id=order_model.user.telegram_id,
            text=ORDER_TEST_CANCELED_MSG,
            parse_mode='html'
        )
        return START_ROUTES

    return SERVICE_ROUTES
