import json
import logging

from telegram import Update, InlineKeyboardMarkup, ReplyKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from bot.context.config import SERVICE_ROUTES
from bot.context.messages import BUY_SERVICE_WELCOME_MSG, SERVICE_SELECT_MSG, PERIOD_SELECT_MSG, SERVICE_NOT_EXIST_MSG, \
    FACTOR_PAYING_MSG, PRICE_LIST_MSG, PRICE_SERVICE_LIST_MSG, PRICE_SERVICE_OBJ_MSG, REFERRAL_BODY_MSG, \
    REFERRAL_BANNER_TEXT_MSG, PRICE_LIST_ITEM_MSG
from bot.widgets.account import get_referral_info_inline_keyboard
from bot.widgets.service import get_service_list_inline_keyboard, get_factor_paying_inline_keyboard, \
    get_country_list_inline_keyboard, get_period_inline_keyboard
from models.order.models import Discount
from models.service.models import Service
from models.user.models import UserModel

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


async def country_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reply_markup = InlineKeyboardMarkup(
        get_country_list_inline_keyboard()
    )

    if update.message:
        await update.message.reply_text(BUY_SERVICE_WELCOME_MSG, reply_markup=reply_markup)
    return SERVICE_ROUTES


async def country_inline_handler(update, context):
    query = update.callback_query
    reply_markup = InlineKeyboardMarkup(
        get_country_list_inline_keyboard()
    )
    await query.edit_message_text(
        text=BUY_SERVICE_WELCOME_MSG, reply_markup=reply_markup
    )
    return SERVICE_ROUTES


async def period_handler(update, context):
    query = update.callback_query

    reply_markup = InlineKeyboardMarkup(
        get_period_inline_keyboard(query.data)
    )
    await query.edit_message_text(
        text=SERVICE_SELECT_MSG, reply_markup=reply_markup
    )
    return SERVICE_ROUTES


async def service_handler(update, context):
    query = update.callback_query
    reply_markup = InlineKeyboardMarkup(
        get_service_list_inline_keyboard(query.data)
    )
    await query.edit_message_text(
        text=PERIOD_SELECT_MSG, reply_markup=reply_markup
    )
    return SERVICE_ROUTES


async def factor_handler(update, context):
    query = update.callback_query
    service_id = str(query.data).replace('service_', '')
    discount = None

    user_model = UserModel.objects.get(telegram_id=query.from_user.id)
    data = json.loads(user_model.data)

    if data:
        if 'discount' in data:
            try:
                discount = Discount.objects.get(id=data['discount'])
            except Discount.DoesNotExist:
                pass
    else:
        data = {}

    data['callback'] = query.data
    user_model.data = json.dumps(data)
    user_model.save(update_fields=['data'])

    try:
        service_model = Service.objects.get(id=service_id, is_test=False)

        if discount:
            price = service_model.price - ((service_model.price * discount.amount) / 100)
        else:
            price = service_model.price

        msg = FACTOR_PAYING_MSG.format(
            service_model.country.name,
            service_model.periods.value,
            service_model.user_count,
            service_model.count,
            int(price)
        )
        reply_markup = InlineKeyboardMarkup(
            get_factor_paying_inline_keyboard(service_model)
        )
    except Service.DoesNotExist:
        msg = SERVICE_NOT_EXIST_MSG
        reply_markup = InlineKeyboardMarkup(
            get_service_list_inline_keyboard(query.data)
        )
    await query.edit_message_text(
        text=msg, reply_markup=reply_markup
    )
    return SERVICE_ROUTES


async def price_list_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = []
    for item in Service.objects.filter(is_active=True, is_test=False).order_by('price'):
        keyboard.append([
            InlineKeyboardButton(PRICE_LIST_ITEM_MSG.format(
                item.country.name,
                int(item.count),
                item.periods.name,
                item.h_toman()
            ), callback_data=str(f"service_{item.id}")),
        ], )
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        PRICE_SERVICE_LIST_MSG,
        parse_mode='html',
        reply_markup=reply_markup
    )
    return SERVICE_ROUTES


async def referral_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    user_model = UserModel.objects.get(telegram_id=user.id, )

    reply_markup = InlineKeyboardMarkup(
        get_referral_info_inline_keyboard()
    )
    await update.message.reply_text(
        REFERRAL_BODY_MSG.format(
            user_model.refal_count, user_model.refal_income, user_model.telegram_id,
            f"https://t.me/v2rayarmybot?start={user_model.telegram_id}"
        ),
        reply_markup=reply_markup,
        parse_mode='html'
    )
    return SERVICE_ROUTES
