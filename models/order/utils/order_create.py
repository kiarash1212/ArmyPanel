from bot.context.messages import ORDER_CONFIG_MSG, ORDER_CANCELED_MSG, INCOME_REFERRAL_MSG, ORDER_SUCCESS_DETAILS_MSG
from models.configure.models import SiteConfiguration
from models.order.models import Order
from models.transactions.models import Transaction
from models.user.models import UserModel
from utils.telegram.message import send_message_telegram


def create_order(service_model, user_model, discount_model, count, referral_amount, price):
    print("creating order...:", (service_model, user_model, discount_model, count, referral_amount, price))
    for item in range(0, count):
        order_model = Order.objects.create(
            service_id=service_model.id,
            user_id=user_model.id,
            price=price / count
        )

        if discount_model:
            order_model.discount_id = discount_model.id
            order_model.save()

        config_url = order_model.create_config()

        if config_url:
            if order_model.user.parent:
                configure = SiteConfiguration.get_solo()

                user_referral = UserModel.objects.get(telegram_id=order_model.user.parent)
                referral_amount += (configure.referral_count * order_model.price) / 100

            user_model.balance -= order_model.price
            user_model.save(update_fields=['balance'])

            send_message_telegram(order_model.user.telegram_id, ORDER_CONFIG_MSG.format(order_model.id, config_url))
        else:
            order_model.delete()
            send_message_telegram(order_model.user.telegram_id, ORDER_CANCELED_MSG.format(order_model.id))
            return

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

        send_message_telegram(user_referral.telegram_id, INCOME_REFERRAL_MSG.format(trs_referral.amount))

    send_message_telegram(user_model.telegram_id, ORDER_SUCCESS_DETAILS_MSG)
