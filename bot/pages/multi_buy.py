import json
import logging

from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot.context.config import SERVICE_ROUTES
from bot.context.messages import BUY_SERVICE_WELCOME_MSG, SERVICE_SELECT_MSG, PERIOD_SELECT_MSG, \
    SERVICE_NOT_EXIST_MSG, MULTI_COUNT_MSG, MULTI_FACTOR_PAYING_MSG
from bot.widgets.multi import get_multi_country_list_inline_keyboard, get_multi_period_inline_keyboard, \
    get_multi_service_list_inline_keyboard, get_multi_factor_paying_inline_keyboard, get_multi_count_inline_keyboard
from models.service.models import Service
from models.user.models import UserModel

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


async def multi_country_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reply_markup = InlineKeyboardMarkup(
        get_multi_country_list_inline_keyboard()
    )
    await update.message.reply_text(BUY_SERVICE_WELCOME_MSG, reply_markup=reply_markup)
    return SERVICE_ROUTES


async def multi_country_inline_handler(update, context):
    query = update.callback_query
    reply_markup = InlineKeyboardMarkup(
        get_multi_country_list_inline_keyboard()
    )
    await query.edit_message_text(
        text=BUY_SERVICE_WELCOME_MSG, reply_markup=reply_markup
    )
    return SERVICE_ROUTES


async def multi_period_handler(update, context):
    query = update.callback_query

    reply_markup = InlineKeyboardMarkup(
        get_multi_period_inline_keyboard(query.data)
    )
    await query.edit_message_text(
        text=SERVICE_SELECT_MSG, reply_markup=reply_markup
    )
    return SERVICE_ROUTES


async def multi_service_handler(update, context):
    query = update.callback_query
    reply_markup = InlineKeyboardMarkup(
        get_multi_service_list_inline_keyboard(query.data)
    )
    await query.edit_message_text(
        text=PERIOD_SELECT_MSG, reply_markup=reply_markup
    )
    return SERVICE_ROUTES


async def multi_count_handler(update, context):
    query = update.callback_query
    service_id = str(query.data).replace('service_multi_', '')
    reply_markup = InlineKeyboardMarkup(
        get_multi_count_inline_keyboard(service_id)
    )
    await query.edit_message_text(
        text=MULTI_COUNT_MSG, reply_markup=reply_markup
    )
    return SERVICE_ROUTES


async def multi_factor_handler(update, context):
    query = update.callback_query
    service_id, count = str(query.data).replace('count_multi_', '').split('_')

    user_model = UserModel.objects.get(telegram_id=query.from_user.id)
    user_model.data = json.dumps({"callback": query.data})
    user_model.save(update_fields=['data'])

    try:
        service_model = Service.objects.get(id=service_id)
        msg = MULTI_FACTOR_PAYING_MSG.format(
            service_model.country.name,
            service_model.periods.value,
            service_model.user_count,
            service_model.count,
            service_model.price,
            count,
            int((service_model.price - ((service_model.price * service_model.price_multi_discount) / 100)) * int(count))
        )
        reply_markup = InlineKeyboardMarkup(
            get_multi_factor_paying_inline_keyboard(service_model, count)
        )
    except Service.DoesNotExist:
        msg = SERVICE_NOT_EXIST_MSG
        reply_markup = InlineKeyboardMarkup(
            get_multi_service_list_inline_keyboard(query.data)
        )
    await query.edit_message_text(
        text=msg, reply_markup=reply_markup
    )
    return SERVICE_ROUTES
