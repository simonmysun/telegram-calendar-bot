import logging
logger = logging.getLogger(__name__)

import typing
if typing.TYPE_CHECKING:
    import telegram

import os

_admin_ids_raw = os.getenv('ADMIN_USER_IDS', '')
ADMIN_USER_IDS = list(map(int, _admin_ids_raw.split(','))) if _admin_ids_raw.strip() else []

async def handle_help_message(update: 'telegram.Update', context: 'telegram.ext.CallbackContext') -> None:
  userId = update.message.from_user.id
  logger.info(f'user<{userId}>: {update.message.text}')
  await context.bot.set_my_commands([
    ('start', 'Start the bot'),
    ('help', 'Show this help message')
  ])
  logger.info(await context.bot.get_my_commands())
  await update.message.reply_text('I give you Google Calendar links')
  if userId in ADMIN_USER_IDS:
    await update.message.reply_text('Admin commands are available.')