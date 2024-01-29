from telegram import InlineKeyboardButton


def get_order_list_inline_keyboard(orders):
    keyboard = []
    for i in orders:
        keyboard.append([
            InlineKeyboardButton(
                f"{i.service.country.key.upper()}_{i.service.periods.value}D_{i.service.user_count}U_{i.service.count}G_ID{i.id}",
                callback_data=str(f"order_details_{i.id}")
            ),
        ])
    return keyboard

