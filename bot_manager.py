import logging
import os

import django

from configbot.settings import TELEGRAM_TOKEN

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'configbot.settings')
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
django.setup()

from bot.pages.group import handle_group_messages
from bot.pages.discount import discount_set_handler, discount_validation_handler
from bot.pages.test import test_country_handler, test_factor_handler, test_country_inline_handler, test_create_handler
from bot.pages.help import help_handler, help_device_inline_handler, help_inline_handler, amoozesh_handler
from bot.pages.service import services_search_handler, services_search_send
from bot.pages.orders import order_list_handler, order_create_handler, order_details_handler, order_config_handler, \
    order_extension_handler, order_extension_accept_handler, order_list_inline_handler, order_qrcode_handler, \
    order_extension_ip_handler, order_extension_ip_accept_handler
from bot.pages.extension import extension_handler
from bot.pages.account import accounts_handler, account_deposit_handler, deposit_amount_handler, crypto_deposit_handler, \
    crypto_card_handler, crypto_validation_transaction_handler, crypto_deposit_confirmed_handler, \
    deposit_directed_handler, card_validation_transaction_handler, card_deposit_confirmed_handler, \
    referral_link_inline_handler
from bot.pages.multi_buy import multi_country_inline_handler, multi_period_handler, multi_service_handler, \
    multi_factor_handler, multi_country_handler, multi_count_handler

from bot.pages.ticket import ticket_subject_handler, ticket_subject_inline_handler, ticket_service_inline_handler, \
    ticket_request_handler, ticket_answer_handler, replying_query_handler

from bot.context.config import SERVICE_ROUTES, DEPOSIT_ROUTES, DEPOSIT_VALIDATION_ROUTES, TICKET_ROUTES, \
    DEPOSIT_CARD_VALIDATION_ROUTES, DISCOUNT_ROUTS, SEARCH_SERVICES_ROUTES, REPLY_TICKET_ROUTES

from bot.context.messages import BUY_SERVICE_MSG, BACK_MSG, ACCOUNT_MSG, MY_SERVICE_MSG, MULTI_BUY_MSG, CONTACTUS_MSG, \
    HELP_MSG, PRICE_LIST_MSG, REFERRAL_MSG, BACK_BTN_MSG, EXT_SERVICE_MSG, TEST_SERVICE_MSG, AMOOZESH_MSG, SEARCHING_SERVICES_MSG
from bot.pages.buy import period_handler, country_handler, service_handler, factor_handler, country_inline_handler, \
    price_list_handler, referral_handler
from bot.pages.start import start_handler, end_handler
from telegram import Bot
from telegram.request import HTTPXRequest
try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler, MessageHandler, filters,
)

import sentry_sdk

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


def telegram_main() -> None:
    bot = Bot(token=TELEGRAM_TOKEN,request=HTTPXRequest(), get_updates_request=HTTPXRequest())
    application = Application.builder().bot(bot).build()
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start_handler),
            MessageHandler(filters.ChatType.GROUPS | filters.ChatType.CHANNEL, handle_group_messages),
            # CallbackQueryHandler(pattern="^replyTicket")
        ],
        states={
            SERVICE_ROUTES: [
                MessageHandler(
                    filters.Regex(f"^{BUY_SERVICE_MSG}$"), country_handler
                ),
                MessageHandler(
                    filters.Regex(f"^{ACCOUNT_MSG}$"), accounts_handler
                ),
                MessageHandler(
                    filters.Regex(f"^{PRICE_LIST_MSG}$"), price_list_handler
                ),
                MessageHandler(
                    filters.Regex(f"^{TEST_SERVICE_MSG}$"), test_country_handler
                ),
                MessageHandler(
                    filters.Regex(f"^{REFERRAL_MSG}$"), referral_handler
                ),
                MessageHandler(
                    filters.Regex(f"^{MY_SERVICE_MSG}$"), order_list_handler
                ),
                MessageHandler(
                    filters.Regex(f"^{MULTI_BUY_MSG}$"), multi_country_handler
                ),
                MessageHandler(
                    filters.Regex(f"^{CONTACTUS_MSG}$"), ticket_subject_handler
                ),
                MessageHandler(
                    filters.Regex(f"^{HELP_MSG}$"), help_handler
                ),
                MessageHandler(
                    filters.Regex(f"^{AMOOZESH_MSG}$"), amoozesh_handler
                ),
                MessageHandler(
                    filters.Regex(f"^{EXT_SERVICE_MSG}$"), extension_handler
                ),
                MessageHandler(
                    filters.Regex(f"^{SEARCHING_SERVICES_MSG}$"), services_search_handler
                ),

                MessageHandler(
                    filters.Regex(f"^{BACK_BTN_MSG}$"), start_handler
                ),

                MessageHandler(filters.ALL & ~filters.COMMAND & filters.REPLY, ticket_answer_handler),

                # Callback query handlers
                #
                CallbackQueryHandler(replying_query_handler, pattern="^replyTicket_(?P<pk>[0-9]+)$"),

                # TEEST
                CallbackQueryHandler(test_factor_handler, pattern="^test_country_(?P<country>[a-zA-Z0-9]+)$"),
                CallbackQueryHandler(test_create_handler, pattern="^test_get_(?P<service_id>[a-zA-Z0-9]+)$"),
                CallbackQueryHandler(test_country_inline_handler, pattern=f"^{TEST_SERVICE_MSG}$"),

                # Service queries
                CallbackQueryHandler(country_inline_handler, pattern=f"^{BUY_SERVICE_MSG}$"),
                CallbackQueryHandler(period_handler, pattern="^country_(?P<country>[a-zA-Z]{2})$"),
                CallbackQueryHandler(
                    service_handler,
                    pattern="^period_(?P<period>[a-zA-Z0-9]+)_(?P<country>[a-zA-Z]{2})$"
                ),
                CallbackQueryHandler(factor_handler, pattern="^service_(?P<period>[a-zA-Z0-9]+)$"),
                CallbackQueryHandler(end_handler, pattern="^" + str(BACK_MSG) + "$"),

                # Multi Service queries
                CallbackQueryHandler(multi_country_inline_handler, pattern=f"^{MULTI_BUY_MSG}$"),
                CallbackQueryHandler(multi_period_handler, pattern="^country_multi_(?P<country>[a-zA-Z]{2})$"),
                CallbackQueryHandler(
                    multi_service_handler,
                    pattern="^period_multi_(?P<period>[a-zA-Z0-9]+)_(?P<country>[a-zA-Z]{2})$"
                ),
                CallbackQueryHandler(multi_count_handler, pattern="^service_multi_(?P<period>[a-zA-Z0-9]+)$"),
                CallbackQueryHandler(
                    multi_factor_handler,
                    pattern="^count_multi_(?P<service_id>[a-zA-Z0-9]+)_(?P<count>[a-zA-Z0-9]+)$"
                ),
                CallbackQueryHandler(end_handler, pattern="^" + str(BACK_MSG) + "$"),

                # Account queries
                CallbackQueryHandler(account_deposit_handler, pattern="^account_deposit$"),
                CallbackQueryHandler(deposit_directed_handler, pattern="^direct_pay_(?P<amount>[a-zA-Z0-9]+)$"),
                CallbackQueryHandler(deposit_directed_handler, pattern="^direct_pay_multi_(.*)$"),
                CallbackQueryHandler(discount_set_handler, pattern="^discount_set$"),

                CallbackQueryHandler(crypto_deposit_handler, pattern="^payment_crypto_(.*)$"),
                CallbackQueryHandler(crypto_card_handler, pattern="^payment_card_(.*)$"),

                CallbackQueryHandler(
                    card_deposit_confirmed_handler,
                    pattern="^payment_confirmed_card_(?P<trs_id>[a-zA-Z0-9]+)$"
                ),

                # Help queries
                CallbackQueryHandler(help_device_inline_handler, pattern="^device_(?P<period>[a-zA-Z0-9]+)$"),
                CallbackQueryHandler(help_inline_handler, pattern=f"^help_back$"),

                # Order queries
                CallbackQueryHandler(
                    order_create_handler,
                    pattern="^pay_wallet_(?P<service_id>[a-zA-Z0-9]+)$"
                ),
                CallbackQueryHandler(
                    order_create_handler,
                    pattern="^pay_multi_wallet_(?P<service_id>[a-zA-Z0-9]+)_(?P<count>[a-zA-Z0-9]+)$"
                ),
                CallbackQueryHandler(
                    order_details_handler,
                    pattern="^order_details_(?P<order_id>[a-zA-Z0-9]+)$"
                ),
                CallbackQueryHandler(
                    order_config_handler,
                    pattern="^order_link_(?P<order_id>[a-zA-Z0-9]+)$"
                ),
                CallbackQueryHandler(
                    order_extension_handler,
                    pattern="^order_extension_(?P<order_id>[a-zA-Z0-9]+)$"
                ),
                CallbackQueryHandler(
                    order_extension_accept_handler,
                    pattern="^order_accept_extension_(?P<order_id>[a-zA-Z0-9]+)$"
                ),
                CallbackQueryHandler(
                    order_extension_ip_handler,
                    pattern="^order_extension_ip_(?P<order_id>[a-zA-Z0-9]+)$"
                ),
                CallbackQueryHandler(
                    order_extension_ip_accept_handler,
                    pattern="^order_accept_extension_ip_(?P<order_id>[a-zA-Z0-9]+)$"
                ),

                CallbackQueryHandler(
                    order_list_inline_handler,
                    pattern="^order_list_(?P<offset>[a-zA-Z0-9]+)$"
                ),
                CallbackQueryHandler(
                    order_qrcode_handler,
                    pattern="^order_qrcode_(?P<order_id>[a-zA-Z0-9]+)$"
                ),

                # Referral queries
                CallbackQueryHandler(
                    referral_link_inline_handler,
                    pattern="^referral_link$"
                ),

                CallbackQueryHandler(
                    referral_link_inline_handler,
                    pattern="^referral_banner$"
                ),

                # Ticket

                CallbackQueryHandler(
                    ticket_service_inline_handler,
                    pattern="^ticket_subject_(?P<subject>[a-zA-Z]+)$"
                ),
                CallbackQueryHandler(
                    ticket_subject_inline_handler,
                    pattern="^ticket_request_(.*)$"
                ),

            ],

            REPLY_TICKET_ROUTES: [
                MessageHandler(
                    filters.ALL, ticket_answer_handler
                ),
            ],
            TICKET_ROUTES: [
                MessageHandler(
                    filters.Regex(f"^{BACK_BTN_MSG}$"), start_handler
                ),
                MessageHandler(
                    filters.ALL, ticket_request_handler
                ),
            ],
            DEPOSIT_ROUTES: [
                MessageHandler(
                    filters.Regex(
                        "([1-9]|[1-9][0-9]|[1-9][0-9][0-9]|[1-9][0-9][0-9][0-9])"),
                    deposit_amount_handler
                ),

                CallbackQueryHandler(crypto_deposit_handler, pattern="^payment_crypto_(.*)$"),
                CallbackQueryHandler(crypto_card_handler, pattern="^payment_card_(.*)$"),
                MessageHandler(
                    filters.Regex(f"^{BACK_BTN_MSG}$"), start_handler
                ),
            ],
            DEPOSIT_VALIDATION_ROUTES: [
                MessageHandler(
                    filters.Regex("^[a-fA-F0-9]{64}$"),
                    crypto_validation_transaction_handler
                ),
                CallbackQueryHandler(
                    crypto_deposit_confirmed_handler,
                    pattern="^payment_crypto_confirmed_(?P<trs_id>[a-zA-Z0-9]+)$"
                ),
                MessageHandler(
                    filters.Regex(f"^{BACK_BTN_MSG}$"), start_handler
                ),
            ],
            DEPOSIT_CARD_VALIDATION_ROUTES: [
                MessageHandler(
                    filters.Regex(f"^{BACK_BTN_MSG}$"), start_handler
                ),
                CallbackQueryHandler(
                    card_deposit_confirmed_handler,
                    pattern="^payment_confirmed_card_(?P<trs_id>[a-zA-Z0-9]+)$"
                ),
                MessageHandler(
                    filters.Regex(f"^(.*)$"), card_validation_transaction_handler
                ),

            ],
            DISCOUNT_ROUTS: [
                MessageHandler(
                    filters.Regex(f"^{BACK_BTN_MSG}$"), start_handler
                ),
                CallbackQueryHandler(
                    card_deposit_confirmed_handler,
                    pattern="^payment_confirmed_card_(?P<trs_id>[a-zA-Z0-9]+)$"
                ),
                MessageHandler(
                    filters.Regex(f"^(.*)$"), discount_validation_handler
                ),

            ],
            SEARCH_SERVICES_ROUTES :[
                MessageHandler(
                    filters.Regex(f"^{BACK_BTN_MSG}$"), start_handler
                ),
                MessageHandler(
                    filters.Regex(f"^vless://") or filters.Regex(f"^vless://"), services_search_send
                ),
            ]

        },
        fallbacks=[CommandHandler("start", start_handler)],
    )

    application.add_handler(conv_handler)
    application.run_polling(timeout=10)


if __name__ == "__main__":
    # sentry_sdk.init(
    #     dsn="https://84caa279cc1b5fcc3e18dc81572b4b21@o4504970381754369.ingest.sentry.io/4505839417884672",
    #     # Set traces_sample_rate to 1.0 to capture 100%
    #     # of transactions for performance monitoring.
    #     # We recommend adjusting this value in production.
    #     traces_sample_rate=1.0,
    #     # Set profiles_sample_rate to 1.0 to profile 100%
    #     # of sampled transactions.
    #     # We recommend adjusting this value in production.
    #     profiles_sample_rate=1.0,
    # )
    telegram_main()
