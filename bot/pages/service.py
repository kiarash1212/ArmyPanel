from bot.context.config import SEARCH_SERVICES_ROUTES
from bot.context.messages import BACK_KEYBOARD_MSG
from telegram import Update, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.error import BadRequest
from telegram.ext import ContextTypes

from bot.context.config import SERVICE_ROUTES
from bot.context.messages import ORDER_DETAILS_MSG, ORDER_NOT_EXIST_MSG

from bot.widgets.order import get_order_details_inline_keyboard

from models.order.models import Order

async def services_search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user

    await update.message.reply_text("لطفا 'شماره سفارش' یا لینک 'لینک کانفیگ' سرویس مورد نظرتون رو بفرستین.",
                                    reply_markup=ReplyKeyboardMarkup(BACK_KEYBOARD_MSG, resize_keyboard=True))
    return SEARCH_SERVICES_ROUTES

async def services_search_send(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    text = update.message.text

    if text.startswith("vless:"):
        theOrder = Order.objects.get(config__exact=text)

    else:
        theOrder = Order.objects.get(id=text)

    if theOrder:
        order_id = theOrder.id
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

        await context.bot.send_message(
            chat_id=user.id,
            text=message,
            reply_markup=reply_markup,
            parse_mode='html'
        )
        return SERVICE_ROUTES
    else:
        await update.message.reply_text("سفارشی با این مشخصات یافت نشد !")
        return SERVICE_ROUTES


