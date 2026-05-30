import logging
logger = logging.getLogger(__name__)

import os
import typing
if typing.TYPE_CHECKING:
    import telegram

import telegram
from telegram.ext import ApplicationHandlerStop

_admin_ids_raw = os.getenv('ADMIN_USER_IDS', '')
ADMIN_USER_IDS = list(map(int, _admin_ids_raw.split(','))) if _admin_ids_raw.strip() else []

_allowed_ids_raw = os.getenv('ALLOWED_TELEGRAM_USER_IDS', '')
ALLOWED_TELEGRAM_USER_IDS = list(map(int, _allowed_ids_raw.split(','))) if _allowed_ids_raw.strip() else []

async def handle_permission_check(update: 'telegram.Update', context: 'telegram.ext.CallbackContext') -> None:
  user_id = update.message.from_user.id
  chat_id = update.message.chat.id
  if update.message.chat.type not in [
    telegram.constants.ChatType.GROUP, telegram.constants.ChatType.SUPERGROUP
    ] and user_id not in ADMIN_USER_IDS and user_id not in ALLOWED_TELEGRAM_USER_IDS:
    logger.info(f'user<{user_id}>@chat<{chat_id}>: Permission denied')
    await update.message.reply_text('Permission denied')
    raise ApplicationHandlerStop()
  else:
    logger.info(f'user<{user_id}>@chat<{chat_id}>: Permission granted')