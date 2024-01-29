from telegram import InlineKeyboardButton

from bot.context.messages import BACK_BTN_MSG, PAY_WITH_WALLET_MSG, PAY_WITH_CART_MSG, TEST_ACCOUNT_MSG, BACK_MSG, \
    BUY_SERVICE_MSG, DIRECT_PAY_MSG, DEPOSIT_MSG, DISCOUNT_MSG, DISCOUNT_BTN, MULTI_BUY_MSG


def get_multi_country_list_inline_keyboard():
    from models.service.models import Country

    keyboard = []
    countries_model = Country.objects.filter(is_active=True)
    for i in range(0, len(countries_model), 2):
        try:
            keyboard.append([
                InlineKeyboardButton(countries_model[i].name,
                                     callback_data=str(f"country_multi_{countries_model[i].key}")),
                InlineKeyboardButton(countries_model[i + 1].name,
                                     callback_data=str(f"country_multi_{countries_model[i + 1].key}"))
            ])
        except:
            keyboard.append([
                InlineKeyboardButton(countries_model[i].name,
                                     callback_data=str(f"country_multi_{countries_model[i].key}"))
            ])
    return keyboard


def get_multi_service_list_inline_keyboard(data):
    from models.service.models import Service

    period_id, country_key = str(data).replace('period_multi_', '').split('_')

    services_model = Service.objects.filter(country__key=country_key, periods_id=period_id, is_test=False)
    services = [
        [
            InlineKeyboardButton(
                f"{item.get_count()} {item.user_count} کاربر {item.h_toman() - ((item.h_toman() * item.price_multi_discount) / 100)} هزار تومان",
                callback_data=str(f"service_multi_{item.id}")
            )
        ] for item in services_model
    ]
    services.append([InlineKeyboardButton(BACK_BTN_MSG, callback_data=str(f"country_multi_{country_key}"))])

    return services


def get_multi_period_inline_keyboard(data):
    from models.service.models import Service

    country_key = str(data).replace('country_multi_', '')

    services_model = Service.objects.filter(country__key=country_key)

    periods = []
    services = []
    for item in services_model:
        if item.periods.name not in periods:
            periods.append(item.periods.name)
            services.append([
                InlineKeyboardButton(item.periods.name,
                                     callback_data=str(f"period_multi_{item.periods_id}_{country_key}"))
            ])

    services.append([InlineKeyboardButton(BACK_BTN_MSG, callback_data=str(MULTI_BUY_MSG))])
    return services


def get_multi_count_inline_keyboard(data):
    from models.service.models import Service
    services_model = Service.objects.get(id=data)

    count_list = [
        [
            InlineKeyboardButton("10 عدد", callback_data=str(f"count_multi_{services_model.id}_10")),
            InlineKeyboardButton("15 عدد", callback_data=str(f"count_multi_{services_model.id}_15")),
        ],
        [
            InlineKeyboardButton("20 عدد", callback_data=str(f"count_multi_{services_model.id}_20")),
            InlineKeyboardButton("25 عدد", callback_data=str(f"count_multi_{services_model.id}_25")),
        ],
        [
            InlineKeyboardButton("30 عدد", callback_data=str(f"count_multi_{services_model.id}_30")),
            InlineKeyboardButton("35 عدد", callback_data=str(f"count_multi_{services_model.id}_35")),
        ],
        [
            InlineKeyboardButton("40 عدد", callback_data=str(f"count_multi_{services_model.id}_40")),
            InlineKeyboardButton("45 عدد", callback_data=str(f"count_multi_{services_model.id}_45")),
        ],
        [
            InlineKeyboardButton("50 عدد", callback_data=str(f"count_multi_{services_model.id}_50")),
        ],

    ]

    count_list.append([InlineKeyboardButton(BACK_BTN_MSG, callback_data=str(
        f"period_multi_{services_model.periods.id}_{services_model.country.key}"))])
    return count_list


def get_multi_factor_paying_inline_keyboard(data, count):
    return [
        [
            InlineKeyboardButton(PAY_WITH_WALLET_MSG, callback_data=str(f"pay_multi_wallet_{data.id}_{count}")),
            InlineKeyboardButton(DIRECT_PAY_MSG, callback_data=str(f"direct_pay_multi_{data.id}_{count}"))
        ],
        [
            InlineKeyboardButton(DEPOSIT_MSG, callback_data=str("account_deposit"))
        ],
        [
            InlineKeyboardButton(BACK_BTN_MSG, callback_data=str(f"service_multi_{data.id}"))
        ]
    ]
