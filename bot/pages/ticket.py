import io
import json
import logging
import random

from telegram import Update, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import ContextTypes

from bot.context.config import SERVICE_ROUTES, TICKET_ROUTES, REPLY_TICKET_ROUTES
from bot.context.messages import TICKET_WELLCOME_MSG, TICKET_SUBJECT_CHOICES_MSG, \
    TICKET_TECHNICAL_BTN, TICKET_FINANCIAL_BTN, TICKET_OTHER_BTN, TICKET_ENTER_REQUEST_MSG, TICKET_SERVICE_MSG, \
    BACK_KEYBOARD_MSG, START_KEYBOARD_MSG, TICKET_ACCEPTED_MSG, NOT_HAVE_ANY_SERVICE_MSG, \
    TICKET_REPLAY_ERROR_MSG, TICKET_LIMIT_MSG, TICKET_ORDER_LIMIT_MSG, TICKET_LIMIT_TEXT_MSG, TICKET_ANSWER_REQUEST_MSG
from bot.widgets.order import get_order_list_inline_keyboard
from bot.widgets.ticket import ticket_subject_inline_keyboard
from models.configure.models import SiteConfiguration
from models.order.models import Order
from models.ticket.models import Ticket, Answer
from models.user.models import UserModel
from django.core.files.images import ImageFile

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


async def ticket_subject_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reply_markup = InlineKeyboardMarkup(
        ticket_subject_inline_keyboard()
    )
    await update.message.reply_text(TICKET_WELLCOME_MSG, reply_markup=reply_markup)
    return SERVICE_ROUTES


async def ticket_service_inline_handler(update, context):
    query = update.callback_query

    subject = query.data.replace("ticket_subject_", "")

    orders = Order.objects.filter(user__telegram_id=query.from_user.id, is_test_config=False)

    if "technical" == subject:
        subject_msg = TICKET_TECHNICAL_BTN
    elif "financial" == subject:
        subject_msg = TICKET_FINANCIAL_BTN
    else:
        subject_msg = TICKET_OTHER_BTN

    if subject_msg != TICKET_TECHNICAL_BTN:
        tickets = Ticket.objects.filter(
            user__telegram_id=query.from_user.id,
            status__in=['pending', 'suspended'],
            subject=subject_msg
        ).count()

        configure = SiteConfiguration.get_solo()
        if tickets >= configure.ticket_count:
            await query.answer(text=TICKET_LIMIT_MSG.format(configure.ticket_count), show_alert=True)
            return SERVICE_ROUTES

    reply_markup = InlineKeyboardMarkup(
        get_order_list_inline_keyboard(orders, subject=subject)
    )

    if orders:
        message = TICKET_SERVICE_MSG
    else:
        message = NOT_HAVE_ANY_SERVICE_MSG

    await query.edit_message_text(
        text=message, reply_markup=reply_markup
    )

    return SERVICE_ROUTES


async def ticket_subject_inline_handler(update, context):
    query = update.callback_query

    subject, order_id = query.data.replace("ticket_request_", "").split("_")

    if "technical" == subject and order_id:
        subject_msg = TICKET_TECHNICAL_BTN
    elif "financial" == subject:
        subject_msg = TICKET_FINANCIAL_BTN
    else:
        subject_msg = TICKET_OTHER_BTN

    tickets = Ticket.objects.filter(
        user__telegram_id=query.from_user.id,
        status__in=['pending', 'suspended'],
        order_id=order_id
    ).count()

    configure = SiteConfiguration.get_solo()
    if tickets >= configure.ticket_count:
        await query.answer(text=TICKET_ORDER_LIMIT_MSG, show_alert=True)
        return SERVICE_ROUTES

    if int(order_id) != 0:
        order_model = Order.objects.get(id=order_id)
    else:
        order_id = None

    if "technical" == subject and order_id:
        message = TICKET_SUBJECT_CHOICES_MSG.format(
            subject_msg,
            f"{order_model.service.country.key.upper()}_{order_model.service.periods.value}D_{order_model.service.user_count}U_{order_model.service.count}G_ID{order_model.id}"
        )
    elif "financial" == subject:
        message = TICKET_SUBJECT_CHOICES_MSG.format(subject_msg)
    else:
        message = TICKET_SUBJECT_CHOICES_MSG.format(subject_msg)

    await query.edit_message_text(
        text=message,
        reply_markup=None
    )

    user_model = UserModel.objects.get(telegram_id=query.from_user.id)

    data = {
        'subject': subject_msg,
        'order_id': order_id
    }
    user_model.data = json.dumps(data)
    user_model.save(update_fields=['data'])

    markup = ReplyKeyboardMarkup(
        BACK_KEYBOARD_MSG, one_time_keyboard=False,
        resize_keyboard=True
    )
    await context.bot.send_message(
        chat_id=query.from_user.id,
        text=TICKET_ENTER_REQUEST_MSG,
        reply_markup=markup,
    )

    return TICKET_ROUTES


async def ticket_request_handler(update, context):
    user = update.message.from_user
    request = str(update.message.text)
    if update.message.photo:
        print(update.message.photo)
        imageBytes = await (await context.bot.get_file(update.message.photo[-1].file_id)).download_as_bytearray()
        image = io.BytesIO(imageBytes)
        request = str(update.message.caption)
        image = ImageFile(image, "name.jpg")
    else:
        image = None

    print(request, len(request))
    if len(request) < 10:
        markup = ReplyKeyboardMarkup(
            BACK_KEYBOARD_MSG, one_time_keyboard=False,
            resize_keyboard=True
        )
        await update.message.reply_text(
            text=TICKET_LIMIT_TEXT_MSG,
            reply_markup=markup
        )
        return TICKET_ROUTES

    user_model = UserModel.objects.get(telegram_id=user.id)

    data = json.loads(user_model.data)

    Ticket.objects.create(
        subject=data['subject'],
        order_id=data['order_id'],
        image=image,
        user_id=user_model.id,
        request=request
    )

    user_model.data = json.dumps({})
    user_model.save(update_fields=['data'])

    markup = ReplyKeyboardMarkup(START_KEYBOARD_MSG, one_time_keyboard=False)
    await update.message.reply_text(
        text=TICKET_ACCEPTED_MSG,
        reply_markup=markup
    )
    return SERVICE_ROUTES


async def ticket_answer_handler(update, context):
    user = update.message.from_user
    text = update.message.text
    print('revecied reply.')

    try:
        ticketPk = context.user_data.get(f"replyTicket")
        if not ticketPk:ticketPk = int(update.message.reply_to_message.text.split("\n")[0].split()[-1].strip())
        ticket_model = Ticket.objects.get(
            pk=ticketPk
        )
    except Answer.DoesNotExist:
        await update.message.reply_text(TICKET_REPLAY_ERROR_MSG)
        return SERVICE_ROUTES

    image = None
    if update.message.photo:
        imageBytes = await (await context.bot.get_file(update.message.photo[-1].file_id)).download_as_bytearray()
        image = io.BytesIO(imageBytes)
        text = str(update.message.caption)
        image = ImageFile(image, f"{user.id}.jpg")

    ticket_model.status = 'pending'
    ticket_model.save(update_fields=['status'])
    answer = Answer.objects.create(
        message= text or "None",
        ticket=ticket_model,
        side='user',
        image=image
    )

    await update.message.reply_text(TICKET_ACCEPTED_MSG)

    return SERVICE_ROUTES

async def replying_query_handler(update, context):
    query = update.callback_query.data

    pk = int(query.split("_")[1])

    context.user_data[f"replyTicket"] = pk
    await context.bot.send_message(update.callback_query.from_user.id, TICKET_ANSWER_REQUEST_MSG)

    return REPLY_TICKET_ROUTES