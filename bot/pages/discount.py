import json

from django.utils import timezone
from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup

from bot.context.config import DISCOUNT_ROUTS, SERVICE_ROUTES
from bot.context.messages import DISCOUNT_MSG, BACK_KEYBOARD_MSG, DISCOUNT_ERROR_MSG, DISCOUNT_SUCCESS_MSG
from bot.widgets.discount import discount_next_inline_keyboard
from models.order.models import Discount, Order
from models.service.models import Service
from models.user.models import UserModel


async def discount_error_callback(callback, update):
    markup = ReplyKeyboardMarkup(
        BACK_KEYBOARD_MSG, one_time_keyboard=False,
        resize_keyboard=True
    )
    await update.message.reply_text(
        DISCOUNT_ERROR_MSG,
        reply_markup=markup,
    )
    return DISCOUNT_ROUTS


async def discount_success_callback(update, user_model, discount):
    data = json.loads(user_model.data)
    reply_markup = InlineKeyboardMarkup(
        discount_next_inline_keyboard(data['callback'])
    )

    user_model.data = json.dumps({'discount': discount.id})
    user_model.save(update_fields=['data'])

    await update.message.reply_text(
        DISCOUNT_SUCCESS_MSG.format(
            discount.amount
        ),
        reply_markup=reply_markup,
    )
    return SERVICE_ROUTES


async def discount_set_handler(update, context):
    query = update.callback_query
    query.delete_message()

    markup = ReplyKeyboardMarkup(
        BACK_KEYBOARD_MSG, one_time_keyboard=False,
        resize_keyboard=True
    )

    await context.bot.send_message(
        chat_id=query.from_user.id,
        text=DISCOUNT_MSG,
        reply_markup=markup,
        parse_mode='html'
    )
    return DISCOUNT_ROUTS


async def discount_validation_handler(update, context):
    user = update.message.from_user
    discount_code = str(update.message.text)

    user_model = UserModel.objects.get(telegram_id=user.id)
    data = json.loads(user_model.data)
    discount = Discount.objects.filter(code=discount_code)

    if discount.exists():
        discount_model = discount.first()
        if 'callback' in data:
            service_id = data['callback'].replace("service_", "")
        else:
            markup = ReplyKeyboardMarkup(
                BACK_KEYBOARD_MSG, one_time_keyboard=False,
                resize_keyboard=True
            )
            await update.message.reply_text(
                "خطا در بارگذاری داده، لطفا مجددا از اول اقدام به ثبت سفارش نمایید.",
                reply_markup=markup,
            )
            return DISCOUNT_ROUTS

        order_discount = Order.objects.filter(discount_id=discount_model.id)
        if order_discount.count() >= discount_model.count:
            result = await discount_error_callback(data['callback'], update)
            return result

        if discount_model.expired:
            if discount_model.expired.timestamp() < timezone.now().timestamp():
                result = await discount_error_callback(data['callback'], update)
                return result

        if discount_model.users.all():
            if discount_model.users.filter(telegram_id=user_model.telegram_id):
                result = await discount_success_callback(update, user_model, discount_model)
                return result
            else:
                result = await discount_error_callback(data['callback'], update)
                return result

        if discount_model.service.all():

            if discount_model.service.filter(id=service_id):
                result = await discount_success_callback(update, user_model, discount_model)
                return result

            else:
                result = await discount_error_callback(data['callback'], update)
                return result

        if discount_model.country.all():
            service_model = Service.objects.get(id=service_id)
            if discount_model.country.filter(id=service_model.country_id):
                result = await discount_success_callback(update, user_model, discount_model)
                return result
            else:
                result = await discount_error_callback(data['callback'], update)
                return result

        result = await discount_success_callback(update, user_model, discount_model)
        return result
    else:
        result = await discount_error_callback(data['callback'], update)
        return result
