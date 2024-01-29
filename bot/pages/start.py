import logging


from telegram import ReplyKeyboardMarkup, Update, InlineKeyboardMarkup, InlineKeyboardButton, ChatMemberLeft
from telegram.ext import ContextTypes

from bot.context.config import START_ROUTES
from bot.context.messages import WELLCOME_MSG, START_KEYBOARD_MSG, REFERRAL_USER_REGISTER_MSG, JOIN_CHANNELS_MSG
from models.user.models import UserModel
from models.configure.models import SiteConfiguration
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    referral_user = None

    join_channels = [i for i in (SiteConfiguration.get_solo().join_channels or "").split('\n') if i]
    not_joined = []
    for row in join_channels:
        channelLink, channelId = row.split(',')
        print(channelLink, channelId)
        try:
            status = await context.bot.get_chat_member(int(f"-100{channelId}"), user.id)
            if isinstance(status, ChatMemberLeft):
                not_joined.append(channelLink)
        except Exception as e:print(e)
    if not_joined:
        await update.message.reply_text(
            JOIN_CHANNELS_MSG,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(text=f'کانال {i+1}', url=j)] for i,j in enumerate(not_joined)]),
        )
        return START_ROUTES



    if context.args:
        referral_id = str(context.args[-1])
        try:
            referral_user = UserModel.objects.get(telegram_id=referral_id)
        except UserModel.DoesNotExist:
            pass

    user_model, is_created = UserModel.objects.get_or_create(
        telegram_id=user.id,
        username=user.id,
    )

    if is_created:
        user_model.telegram_username = user.username,
        user_model.first_name = user.first_name
        user_model.last_name = user.last_name

        if referral_user and not user_model.parent and referral_user.id != user_model.id:
            user_model.parent = referral_user.telegram_id
            referral_user.refal_count += 1
            referral_user.save(update_fields=['refal_count'])
            await context.bot.send_message(chat_id=referral_user.telegram_id, text=REFERRAL_USER_REGISTER_MSG)
        user_model.save(update_fields=['first_name', 'last_name', 'telegram_username', 'parent'])

    markup = ReplyKeyboardMarkup(START_KEYBOARD_MSG, one_time_keyboard=False)
    await update.message.reply_text(
        WELLCOME_MSG,
        reply_markup=markup,
    )
    return START_ROUTES


async def end_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query

    await query.answer()
    await query.edit_message_text(text=WELLCOME_MSG)
    return START_ROUTES
