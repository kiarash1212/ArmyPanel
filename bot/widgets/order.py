from telegram import InlineKeyboardButton

from bot.context.messages import BACK_MSG, ORDER_EXTENSION_BTN_MSG, ORDER_LINK_BTN_MSG, BACK_BTN_MSG, \
    DEPOSIT_CRYPTO_NEXT_MSG, ORDER_QRCODE_MSG, ORDER_EXTENSION_IP_BTN_MSG


def get_order_list_inline_keyboard(orders, offset=0, subject=None):
    keyboard = []
    base_callback = "order_details_"

    # For ticket page
    if subject:
        base_callback = f"ticket_request_{subject}_"
        filter_orders = orders
    else:
        filter_orders = orders[offset:offset + 10]

    for i in filter_orders:
        name = f"{i.service.country.key.upper()}_{i.service.periods.value}D_{i.service.user_count}U_{i.service.count}G_ID{i.id}"
        if i.is_test_config:
            name = f"{name}_TEST"
        keyboard.append([
            InlineKeyboardButton(
                name,
                callback_data=str(f"{base_callback}{i.id}")
            ),
        ])

    if not subject:
        if len(filter_orders) >= 10:
            keyboard.append([
                InlineKeyboardButton(
                    f"بیشتر",
                    callback_data=str(f"order_list_{offset + 10}")
                ),
            ])
        if offset >= 10:
            keyboard.append([
                InlineKeyboardButton(
                    f"بازگشت",
                    callback_data=str(f"order_list_{offset - 10}")
                ),
            ])

    return keyboard


def get_order_details_inline_keyboard(order):
    keyboard = [
        [
            InlineKeyboardButton(ORDER_LINK_BTN_MSG, callback_data=str(f"order_link_{order.id}")),
        ],
        [
            InlineKeyboardButton(ORDER_EXTENSION_IP_BTN_MSG, callback_data=str(f"order_extension_ip_{order.id}")),
            InlineKeyboardButton(ORDER_EXTENSION_BTN_MSG, callback_data=str(f"order_extension_{order.id}"))
        ],
        [InlineKeyboardButton(BACK_BTN_MSG, callback_data=str("order_list_0"))]
    ]
    return keyboard


def get_order_back_inline_keyboard(order, callback_accept):
    return [
        [InlineKeyboardButton(DEPOSIT_CRYPTO_NEXT_MSG, callback_data=str(f"{callback_accept}{order.id}"))],
        [InlineKeyboardButton(BACK_BTN_MSG, callback_data=str(f"order_details_{order.id}"))]
    ]
def get_order_link_inline_keyboard(order):
    return [
        [InlineKeyboardButton(BACK_BTN_MSG, callback_data=str(f"order_details_{order.id}"))]
    ]
