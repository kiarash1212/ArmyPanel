import logging
from datetime import timedelta

from django.utils import timezone
from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot.context.config import SERVICE_ROUTES
from bot.context.messages import EXTENSION_ENTER_MSG, EXTENSION_NOT_MSG
from bot.widgets.extension import get_order_list_inline_keyboard
from models.configure.models import SiteConfiguration
from models.order.models import Order


async def extension_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user

    configure = SiteConfiguration.get_solo()
    ext_service_role = configure.ext_service_role.split('-')
    today = timezone.now().date()
    date_days_later = today + timedelta(days=int(ext_service_role[0]))
    date_days_ago = today - timedelta(days=int(ext_service_role[1]))
    orders_date = Order.objects.filter(
        user__telegram_id=user.id,
        expired_date__gte=date_days_ago,
        expired_date__lte=date_days_later,
        is_test_config=False
    )
    orders_value = Order.objects.filter(user__telegram_id=user.id, alarm_send_data__isnull=False, is_test_config=False)

    all_order = orders_date | orders_value
    if not all_order:
        msg = EXTENSION_NOT_MSG
        reply_markup = None
    else:
        msg = EXTENSION_ENTER_MSG
        reply_markup = InlineKeyboardMarkup(
            get_order_list_inline_keyboard(
                all_order
            )
        )

    await update.message.reply_text(msg, reply_markup=reply_markup)
    return SERVICE_ROUTES
