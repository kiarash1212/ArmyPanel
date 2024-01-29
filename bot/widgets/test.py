from telegram import InlineKeyboardButton

from bot.context.messages import BACK_BTN_MSG, PAY_WITH_WALLET_MSG, PAY_WITH_CART_MSG, TEST_ACCOUNT_MSG, BACK_MSG, \
    BUY_SERVICE_MSG, DIRECT_PAY_MSG, TEST_SERVICE_MSG, GET_TEST_ACC_MSG


def get_test_country_list_inline_keyboard():
    from models.service.models import Country

    keyboard = []
    countries_model = Country.objects.filter(is_active=True)
    for i in range(0, len(countries_model), 2):
        try:
            keyboard.append([
                InlineKeyboardButton(countries_model[i].name,
                                     callback_data=str(f"test_country_{countries_model[i].id}")),
                InlineKeyboardButton(countries_model[i + 1].name,
                                     callback_data=str(f"test_country_{countries_model[i + 1].id}"))
            ])
        except:
            keyboard.append([
                InlineKeyboardButton(countries_model[i].name,
                                     callback_data=str(f"test_country_{countries_model[i].id}"))
            ])

    return keyboard


def get_test_factor_paying_inline_keyboard(data):
    return [
        [
            InlineKeyboardButton(GET_TEST_ACC_MSG, callback_data=str(f"test_get_{data.id}")),
        ],
        [
            InlineKeyboardButton(BACK_BTN_MSG, callback_data=str(TEST_SERVICE_MSG))
        ]
    ]



def get_test_back_inline_keyboard():
    return [
        [
            InlineKeyboardButton(BACK_BTN_MSG, callback_data=str(TEST_SERVICE_MSG)),
        ]
    ]


