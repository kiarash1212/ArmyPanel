import json
import random
import threading

from datetime import datetime, date, timedelta
from django.utils import timezone
from jalali_date import datetime2jalali
from telegram import InlineKeyboardMarkup, ReplyKeyboardMarkup

from bot.context.config import ACCOUNT_ROUTES, SERVICE_ROUTES, DEPOSIT_ROUTES, START_ROUTES, DEPOSIT_VALIDATION_ROUTES, \
    DEPOSIT_CARD_VALIDATION_ROUTES
from bot.context.messages import BACK_MSG, ACCOUNT_INFO_MSG, DEPOSIT_AMOUNT_MSG, BACK_KEYBOARD_MSG, DEPOSIT_CRYPTO_FACTOR_MSG, \
    DEPOSIT_CRYPTO_CONFIRMED_MSG, START_KEYBOARD_MSG, DEPOSIT_CRYPTO_ACCEPT_FACTOR_MSG, INVALID_TX_ID_MSG, \
    WAITING_TX_VALIDATION_MSG, TX_ID_EXISTS_MSG, ORDER_CONFIG_MSG, ORDER_UNDER_PAY_MSG, \
    DEPOSIT_CRYPTO_HELP_MSG, DEPOSIT_CARD_FACTOR_MSG, DEPOSIT_CARD_HELP_MSG, INCOME_REFERRAL_MSG, \
    REFERRAL_BANNER_TEXT_MSG, DEPOSIT_CARD_W_MSG, ORDER_CANCELED_MSG, ADD_BALANCE_ORDER, DEPOSIT_LIMIT_MSG, \
    DEPOSIT_CARD_ACCEPT_FACTOR_MSG, NO_TRS_CARD_MSG, BAD_DATA_CARD_MSG, DEPOSIT_CARD_BAN_MSG, DEPOSIT_BAN_MSG, \
    DEPOSIT_BAN_ALARM_MSG, DEPOSIT_BANED_MSG
from bot.widgets.account import get_account_info_inline_keyboard
from bot.widgets.deposit import deposit_payment_inline_keyboard, \
    deposit_confirm_crypto_inline_keyboard, deposit_confirm_card_inline_keyboard
from models.configure.models import SiteConfiguration
from models.order.models import Order, Discount
from models.service.models import Service
from models.transactions.models import Transaction
from models.user.models import UserModel


async def accounts_handler(update, context):
    user = update.message.from_user

    user_model = UserModel.objects.get(
        telegram_id=user.id,
    )
    reply_markup = InlineKeyboardMarkup(
        get_account_info_inline_keyboard()
    )

    order_count = Order.objects.filter(user_id=user_model.id).count()
    transaction = Transaction.objects.filter(
        user_id=user_model.id,
    )
    trs_not_payed_count = transaction.filter(status__in=['pending', 'canceled', 'suspended']).count()
    trs_payed_count = transaction.filter(status='payed').count()

    await update.message.reply_text(
        text=ACCOUNT_INFO_MSG.format(
            user_model.telegram_id,
            user_model.refal_count,
            order_count,
            trs_payed_count,
            trs_not_payed_count,
            user_model.balance
        ),
        reply_markup=reply_markup
    )
    return ACCOUNT_ROUTES


async def account_deposit_handler(update, context):
    query = update.callback_query
    markup = ReplyKeyboardMarkup(
        BACK_KEYBOARD_MSG, one_time_keyboard=False,
        resize_keyboard=True
    )

    configure = SiteConfiguration.get_solo()

    await context.bot.send_message(chat_id=query.from_user.id,
                                   text=DEPOSIT_AMOUNT_MSG.format(configure.min_deposit, configure.max_deposit),
                                   reply_markup=markup, )
    return DEPOSIT_ROUTES


async def deposit_amount_handler(update, context):
    user = update.message.from_user
    try:
        amount = int(update.message.text)
    except ValueError:
        await context.bot.send_message(
            chat_id=user.id,
            text="لطفا مبلغ درست وارد نمایید"
        )
        return DEPOSIT_ROUTES

    configure = SiteConfiguration.get_solo()

    user_model = UserModel.objects.get(telegram_id=user.id)
    user_model.data = json.dumps({})
    user_model.save(update_fields=['data'])

    if not configure.min_deposit < amount < configure.max_deposit:
        await context.bot.send_message(
            chat_id=user.id,
            text="مبلغ وارد شده باید بیشتر از {:,} تومان و کمتر از {:,} تومان باشد.".format(configure.min_deposit,
                                                                                            configure.max_deposit)
        )
    else:
        reply_markup = InlineKeyboardMarkup(
            deposit_payment_inline_keyboard(amount),
        )
        await update.message.reply_text(
            text="لطفا روش پرداخت را انتخاب نمایید.",
            reply_markup=reply_markup
        )
    return DEPOSIT_ROUTES


async def deposit_directed_handler(update, context):
    query = update.callback_query
    count = 1
    if 'direct_pay_multi_' in query.data:
        service_id, count = str(query.data).replace("direct_pay_multi_", "").split("_")
    else:
        service_id = str(query.data).replace("direct_pay_", "")

    service_model = Service.objects.get(id=service_id)
    user_model = UserModel.objects.get(telegram_id=query.from_user.id)

    user_data = json.loads(user_model.data)
    discount_id = None

    amount = service_model.price * int(count)
    if 'direct_pay_multi_' in query.data:
        amount = amount - ((amount * service_model.price_multi_discount) / 100)

    if 'discount' in user_data:
        discount_id = user_data['discount']

        try:
            discount_model = Discount.objects.get(id=discount_id)
            amount = (amount - ((amount * discount_model.amount) / 100)) * int(count)
        except Discount.DoesNotExist:
            discount_id = None

    data = {
        'discount': discount_id,
        'service_id': service_model.id,
        'amount': int(amount),
        'count': int(count)
    }

    user_model.data = json.dumps(data)
    user_model.save(update_fields=['data'])

    reply_markup = InlineKeyboardMarkup(
        deposit_payment_inline_keyboard(data['amount']),
    )
    await query.edit_message_text(
        text="لطفا روش پرداخت را انتخاب نمایید.",
        reply_markup=reply_markup
    )
    return SERVICE_ROUTES


async def crypto_deposit_handler(update, context):
    query = update.callback_query

    amount = int(query.data.replace("payment_crypto_", ""))
    configure = SiteConfiguration.get_solo()

    tron_amount = int(amount / configure.tron_price)

    await query.edit_message_text(
        text=DEPOSIT_CRYPTO_FACTOR_MSG.format(
            tron_amount,
            configure.crypto_wallet
        ),
        parse_mode='html'
    )

    markup = ReplyKeyboardMarkup(
        BACK_KEYBOARD_MSG, one_time_keyboard=False,
        resize_keyboard=True
    )

    await context.bot.send_message(
        chat_id=query.from_user.id,
        text=DEPOSIT_CRYPTO_HELP_MSG,
        reply_markup=markup,
    )
    return DEPOSIT_VALIDATION_ROUTES


async def crypto_validation_transaction_handler(update, context):
    user = update.message.from_user
    tx_id = str(update.message.text)

    configure = SiteConfiguration.get_solo()

    msg = await context.bot.send_message(
        chat_id=user.id,
        text="⌛ درحال بررسی تراکنش ..."
    )

    from utils.tron.main import crypto_transaction_validation
    response = await crypto_transaction_validation(
        tx_id,
        configure.crypto_wallet
    )

    tx_id_exists = Transaction.objects.filter(track_id=tx_id).exists()

    if response['validate'] and response['confirm'] and not tx_id_exists:
        msg_text = DEPOSIT_CRYPTO_ACCEPT_FACTOR_MSG.format(
            response['amount'],
            response['from_address']
        )
        user_model = UserModel.objects.get(telegram_id=user.id)

        transaction_model, is_created = Transaction.objects.get_or_create(
            track_id=tx_id,
            card_id=response['from_address'],
            amount=float(response['amount']) * configure.tron_price,
            type='crypto',
            status='suspended',
            user=user_model
        )
        reply_markup = InlineKeyboardMarkup(
            deposit_confirm_crypto_inline_keyboard(transaction_model.id),
        )
    elif tx_id_exists:
        msg_text = TX_ID_EXISTS_MSG
        reply_markup = None
    elif response['validate'] and not response['confirm']:
        msg_text = WAITING_TX_VALIDATION_MSG.format(
            response['amount']
        )
        reply_markup = None
    else:
        msg_text = INVALID_TX_ID_MSG
        reply_markup = None

    await context.bot.edit_message_text(
        chat_id=user.id,
        message_id=msg.message_id,
        text=msg_text,
        reply_markup=reply_markup,
        parse_mode='html'
    )

    return DEPOSIT_VALIDATION_ROUTES


async def crypto_deposit_confirmed_handler(update, context):
    query = update.callback_query
    transaction_id = str(query.data).replace('payment_crypto_confirmed_', '')
    referral_amount, user_referral = 0, None

    await query.delete_message()

    is_direct_pay = False

    transaction_model = Transaction.objects.get(id=transaction_id)
    transaction_model.status = 'payed'
    transaction_model.save(update_fields=['status'])

    if transaction_model.user.data:
        data = json.loads(transaction_model.user.data)
        if 'service_id' in data:
            service_model = Service.objects.get(id=data['service_id'])

            transaction_model.user.data = json.dumps({})
            transaction_model.user.save(update_fields=['data'])

            discount_model = None
            base_price = service_model.price
            if 'discount' in data and data['discount']:
                discount_model = Discount.objects.get(id=data['discount'])
                base_price = service_model.price - ((service_model.price * discount_model.amount) / 100)

            full_price = (base_price * int(data['count']))
            full_balance = transaction_model.amount

            is_direct_pay = True

            if full_balance >= full_price:
                for item in range(0, data['count']):
                    order_model = Order.objects.create(
                        service_id=service_model.id,
                        user_id=transaction_model.user.id,
                    )

                    config_url = order_model.create_config()

                    if config_url:
                        if discount_model:
                            order_model.discount_id = discount_model.id
                        full_balance -= base_price
                        await context.bot.send_message(
                            chat_id=order_model.user.telegram_id,
                            text=ORDER_CONFIG_MSG.format(order_model.id, config_url),
                            parse_mode='html'
                        )
                    else:
                        await context.bot.send_message(
                            chat_id=order_model.user.telegram_id,
                            text=ORDER_CANCELED_MSG.format(order_model.id),
                            parse_mode='html'
                        )

                        if full_balance > 0:
                            transaction_model.user.balance += full_balance
                            transaction_model.user.save(update_fields=['balance'])

                        order_model.delete()

                        return START_ROUTES

                    if order_model.user.parent:
                        configure = SiteConfiguration.get_solo()
                        user_referral = UserModel.objects.get(telegram_id=order_model.user.parent)
                        referral_amount += (configure.referral_count * service_model.price) / 100

                if referral_amount > 0 and user_referral:
                    trs_referral = Transaction.objects.create(
                        user=user_referral,
                        card_id="درآمد زیرمجموعه",
                        amount=referral_amount,
                        status='payed',
                        type='referral'
                    )
                    user_referral.balance += trs_referral.amount
                    user_referral.refal_income += trs_referral.amount
                    user_referral.save(update_fields=['balance', 'refal_income'])

                    await context.bot.send_message(
                        chat_id=user_referral.telegram_id,
                        text=INCOME_REFERRAL_MSG.format(trs_referral.amount),
                        parse_mode='html'
                    )

                if full_balance > 0:
                    transaction_model.user.balance += full_balance
                    transaction_model.user.save(update_fields=['balance'])
            else:
                transaction_model.user.balance += full_balance
                transaction_model.user.save(update_fields=['balance'])
                await context.bot.send_message(chat_id=transaction_model.user.telegram_id, text=ORDER_UNDER_PAY_MSG)

            transaction_model.user.data = json.dumps({})
            transaction_model.user.save(update_fields=['data'])
        else:
            transaction_model.user.balance += transaction_model.amount
            transaction_model.user.save(update_fields=['balance'])
    else:
        transaction_model.user.balance += transaction_model.amount
        transaction_model.user.save(update_fields=['balance'])

    transaction_model.status = 'payed'
    transaction_model.save()

    text = DEPOSIT_CRYPTO_CONFIRMED_MSG
    if is_direct_pay:
        text = ADD_BALANCE_ORDER.format("{:,}".format(full_balance))

    markup = ReplyKeyboardMarkup(START_KEYBOARD_MSG, one_time_keyboard=False)
    await context.bot.send_message(
        chat_id=query.from_user.id,
        text=text,
        reply_markup=markup,

        parse_mode='html'
    )

    return START_ROUTES


async def crypto_card_handler(update, context):
    query = update.callback_query
    amount = int(query.data.replace("payment_card_", ""))

    configure = SiteConfiguration.get_solo()
    now_time = timezone.now()
    time_limit = configure.card_deposit_time
    start_time, end_time = time_limit.split('-')

    if int(start_time) <= datetime2jalali(now_time).hour < int(end_time):
        await query.answer(text=DEPOSIT_LIMIT_MSG.format(start_time, end_time), show_alert=True)
        return SERVICE_ROUTES

    user_model = UserModel.objects.get(telegram_id=query.from_user.id)

    if user_model.alarm_count > 2:
        if user_model.alarm_date + timedelta(days=1) > timezone.now():
            await query.answer(text=DEPOSIT_BAN_MSG, show_alert=True)
            return SERVICE_ROUTES
        user_model.alarm_date = None
        user_model.alarm_count = 0
        user_model.save()

    user_transaction = Transaction.objects.filter(user_id=user_model.id).order_by('-update').first()
    if user_transaction:
        if timezone.now() < user_transaction.update + timedelta(minutes=configure.card_ban_time):
            await query.answer(
                text=DEPOSIT_CARD_BAN_MSG.format(configure.card_ban_time, configure.card_ban_time),
                show_alert=True
            )
            return SERVICE_ROUTES

    user_data = json.loads(user_model.data)
    user_data.update({'amount': amount})
    user_model.data = json.dumps(user_data)
    user_model.save(update_fields=['data'])

    await query.edit_message_text(
        text=DEPOSIT_CARD_FACTOR_MSG.format(
            int(amount),
            configure.card_number
        ),
        parse_mode='html'
    )

    markup = ReplyKeyboardMarkup(
        BACK_KEYBOARD_MSG, one_time_keyboard=False,
        resize_keyboard=True
    )

    await context.bot.send_message(
        chat_id=query.from_user.id,
        text=DEPOSIT_CARD_HELP_MSG,
        reply_markup=markup,
    )

    return DEPOSIT_CARD_VALIDATION_ROUTES


async def card_validation_transaction_handler(update, context):
    user = update.message.from_user
    data_transaction = str(update.message.text)

    user_model = UserModel.objects.get(telegram_id=user.id)

    try:
        configure = SiteConfiguration.get_solo()

        user_data = json.loads(user_model.data)
        amount = user_data['amount']

        current_date = date.today()
        try:
            user_time = datetime.strptime(data_transaction, "%H:%M")
        except:
            await update.message.reply_text("لطفا در این قسمت فقط ساعت واریزی رو به فرمت خواسته شده ارسال کنید.")
            return DEPOSIT_CARD_VALIDATION_ROUTES

        full_datetime = datetime(
            current_date.year, current_date.month, current_date.day, user_time.hour, user_time.minute
        )

        start_time = full_datetime - timedelta(minutes=configure.validate_card_time)
        end_time = full_datetime + timedelta(minutes=configure.validate_card_time)

        transactions = Transaction.objects.filter(
            amount=amount,
            published__gte=start_time,
            published__lte=end_time,
            status="pending",
            type='card',
        )

        if transactions:
            item = transactions[0]
            markup = ReplyKeyboardMarkup(START_KEYBOARD_MSG, one_time_keyboard=False)
            await context.bot.send_message(
                chat_id=user.id,
                text=DEPOSIT_CARD_W_MSG,
                reply_markup=markup
            )

            item.user_id = user_model
            item.track_id = random.randint(10000000, 99999999)
            item.status = 'payed'
            item.save()

            user_model.balance = user_model.balance + item.amount
            user_model.alarm_count = 0
            user_model.alarm_date = None
            user_model.save(update_fields=['alarm_count', 'alarm_date', 'balance'])

            markup = InlineKeyboardMarkup(
                deposit_confirm_card_inline_keyboard(item.id),
            )
            await context.bot.send_message(
                chat_id=user.id,
                text=DEPOSIT_CARD_ACCEPT_FACTOR_MSG.format(
                    item.amount,
                    item.track_id
                ),
                reply_markup=markup,
                parse_mode='html'
            )
            return START_ROUTES
        else:
            user_model.alarm_count = user_model.alarm_count + 1
            user_model.alarm_date = timezone.now()
            user_model.save(update_fields=['alarm_count', 'alarm_date'])

            if user_model.alarm_count == 1:
                await context.bot.send_message(
                    chat_id=user.id,
                    text=DEPOSIT_BAN_ALARM_MSG,
                    parse_mode='html'
                )
            elif user_model.alarm_count > 2:
                markup = ReplyKeyboardMarkup(START_KEYBOARD_MSG, one_time_keyboard=False)
                await context.bot.send_message(
                    chat_id=user.id,
                    text=DEPOSIT_BANED_MSG,
                    parse_mode='html',
                    reply_markup=markup,
                )
                return SERVICE_ROUTES

            await context.bot.send_message(
                chat_id=user.id,
                text=NO_TRS_CARD_MSG,
                parse_mode='html'
            )

            return DEPOSIT_CARD_VALIDATION_ROUTES

    except:
        if user_model.alarm_count == 1:
            await context.bot.send_message(
                chat_id=user.id,
                text=DEPOSIT_BAN_ALARM_MSG,
                parse_mode='html'
            )

        user_model.alarm_count = user_model.alarm_count + 1
        user_model.alarm_date = timezone.now()
        user_model.save(update_fields=['alarm_count', 'alarm_date'])

        if user_model.alarm_count > 2:
            markup = ReplyKeyboardMarkup(START_KEYBOARD_MSG, one_time_keyboard=False)
            await context.bot.send_message(
                chat_id=user.id,
                text=DEPOSIT_BANED_MSG,
                parse_mode='html',
                reply_markup=markup,
            )
            return SERVICE_ROUTES

        await context.bot.send_message(
            chat_id=user.id,
            text=BAD_DATA_CARD_MSG,
            parse_mode='html'
        )
        return DEPOSIT_CARD_VALIDATION_ROUTES


async def card_deposit_confirmed_handler(update, context):
    query = update.callback_query
    transaction_id = str(query.data).replace('payment_confirmed_card_', '')
    referral_amount, user_referral = 0, None
    await query.delete_message()

    transaction_model = Transaction.objects.get(id=transaction_id)

    is_direct_pay = False

    if transaction_model.user.data:
        data = json.loads(transaction_model.user.data)
        if 'service_id' in data:
            user_model = UserModel.objects.get(id=transaction_model.user.id)
            user_model.data = json.dumps({})
            user_model.save(update_fields=['data'])

            service_model = Service.objects.get(id=data['service_id'])

            discount_model = None

            base_price = service_model.price
            if data['count'] > 1:
                base_price = base_price - ((base_price * service_model.price_multi_discount) / 100)

            if 'discount' in data:
                try:
                    discount_model = Discount.objects.get(id=data['discount'])
                    base_price = base_price - ((base_price * discount_model.amount) / 100)
                except Discount.DoesNotExist:
                    discount_model = None

            full_price = (base_price * int(data['count']))
            is_direct_pay = True

            if user_model.balance >= full_price:
                for item in range(0, int(data['count'])):
                    order_model = Order.objects.create(
                        price=base_price,
                        service_id=service_model.id,
                        user_id=transaction_model.user.id,
                    )
                    config_url = order_model.create_config()
                    if config_url:
                        if discount_model:
                            order_model.discount_id = discount_model.id
                        user_model.balance -= base_price
                        user_model.save(update_fields=['balance'])
                        await context.bot.send_message(
                            chat_id=order_model.user.telegram_id,
                            text=ORDER_CONFIG_MSG.format(order_model.id, config_url),
                            parse_mode='html'
                        )
                    else:
                        await context.bot.send_message(
                            chat_id=order_model.user.telegram_id,
                            text=ORDER_CANCELED_MSG.format(order_model.id),
                            parse_mode='html'
                        )
                        order_model.delete()
                        return START_ROUTES

                    if order_model.user.parent:
                        configure = SiteConfiguration.get_solo()

                        user_referral = UserModel.objects.get(telegram_id=order_model.user.parent)
                        referral_amount += (configure.referral_count * service_model.price) / 100

                if referral_amount > 0 and user_referral:
                    trs_referral = Transaction.objects.create(
                        user=user_referral,
                        card_id="درآمد زیرمجموعه",
                        amount=referral_amount,
                        status='payed',
                        type='referral'
                    )
                    user_referral.balance += trs_referral.amount
                    user_referral.refal_income += trs_referral.amount
                    user_referral.save(update_fields=['balance', 'refal_income'])

                    await context.bot.send_message(
                        chat_id=user_referral.telegram_id,
                        text=INCOME_REFERRAL_MSG.format(trs_referral.amount),
                        parse_mode='html'
                    )

            else:
                await context.bot.send_message(chat_id=transaction_model.user.telegram_id, text=ORDER_UNDER_PAY_MSG)

            user_model.data = json.dumps({})
            user_model.save(update_fields=['data'])

    text = DEPOSIT_CRYPTO_CONFIRMED_MSG
    if is_direct_pay:
        text = "سفارش شما با موفقیت ایجاد گردید، در صورت واریز مبلغ اضافی، باقی آن به کیف پول شما اضافه خواهد شد."

    markup = ReplyKeyboardMarkup(START_KEYBOARD_MSG, one_time_keyboard=False)
    await context.bot.send_message(
        chat_id=query.from_user.id,
        text=text,
        reply_markup=markup,
    )
    return START_ROUTES


async def referral_link_inline_handler(update, context):
    query = update.callback_query

    configure = SiteConfiguration.get_solo()

    user_model = UserModel.objects.get(telegram_id=query.from_user.id)
    await context.bot.sendPhoto(
        chat_id=query.from_user.id,
        photo="https://surfshark.com/wp-content/uploads/2022/05/things_to_do_with_VPN_hero.png",
        caption=REFERRAL_BANNER_TEXT_MSG.format(
            int(configure.referral_count),
            f"https://t.me/v2rayarmybot?start={user_model.telegram_id}"
        ),
        parse_mode='html'
    )
    return SERVICE_ROUTES
