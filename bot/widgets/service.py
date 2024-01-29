from telegram import InlineKeyboardButton
from django.db.models import Sum
from bot.context.messages import BACK_BTN_MSG, PAY_WITH_WALLET_MSG, PAY_WITH_CART_MSG, TEST_ACCOUNT_MSG, BACK_MSG, \
    BUY_SERVICE_MSG, DIRECT_PAY_MSG, DEPOSIT_MSG, DISCOUNT_MSG, DISCOUNT_BTN
from models.service.models import Country
from models.service.models import Service


def get_country_list_inline_keyboard():


    keyboard = []
    countries_model = Country.objects.filter(is_active=True)
    for i in range(0, len(countries_model), 2):
        try:
            keyboard.append([
                InlineKeyboardButton(countries_model[i].name, callback_data=str(f"country_{countries_model[i].key}")),
                InlineKeyboardButton(countries_model[i + 1].name,
                                     callback_data=str(f"country_{countries_model[i + 1].key}"))
            ])
        except:
            keyboard.append([
                InlineKeyboardButton(countries_model[i].name, callback_data=str(f"country_{countries_model[i].key}"))
            ])
    return keyboard


def get_service_list_inline_keyboard(data):

    period_id, country_key = str(data).replace('period_', '').split('_')
    country_capacity = Country.objects.get(key__exact=country_key).get_country_remaining_capacity()


    services_model = Service.objects.filter(country__key=country_key, periods_id=period_id, is_test=False, count__lte=country_capacity)
    services = [
        [
            InlineKeyboardButton(
                f"{item.get_count()} {item.user_count} کاربر {item.h_toman()} هزار تومان",
                callback_data=str(f"service_{item.id}")
            )
        ] for item in services_model
    ]
    services.append([InlineKeyboardButton(BACK_BTN_MSG, callback_data=str(f"country_{country_key}"))])

    return services


def get_factor_paying_inline_keyboard(data):
    return [
        [
            InlineKeyboardButton(PAY_WITH_WALLET_MSG, callback_data=str(f"pay_wallet_{data.id}")),
            InlineKeyboardButton(DIRECT_PAY_MSG, callback_data=str(f"direct_pay_{data.id}"))
        ],
        [
            InlineKeyboardButton(DEPOSIT_MSG, callback_data=str("account_deposit"))
        ],
        [
            InlineKeyboardButton(DISCOUNT_BTN, callback_data=str("discount_set"))
        ],
        [
            InlineKeyboardButton(BACK_BTN_MSG, callback_data=str(f"period_{data.periods_id}_{data.country.key}"))
        ]
    ]


def get_period_inline_keyboard(data):
    from models.service.models import Service

    country_key = str(data).replace('country_', '')

    services_model = Service.objects.filter(country__key=country_key)

    periods = []
    services = []
    for item in services_model:
        if item.periods.name not in periods:
            periods.append(item.periods.name)
            services.append([
                InlineKeyboardButton(item.periods.name, callback_data=str(f"period_{item.periods_id}_{country_key}"))
            ])

    services.append([InlineKeyboardButton(BACK_BTN_MSG, callback_data=str(BUY_SERVICE_MSG))])
    return services
