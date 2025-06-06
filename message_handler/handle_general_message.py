import logging
logger = logging.getLogger(__name__)

import typing
if typing.TYPE_CHECKING:
    import telegram
    
import json
import os
import urllib.parse

from telegram import constants

from .llm_api import complete
from .throttle import Throttle
from datetime import datetime, timedelta

MAX_INPUT_LENGTH = int(os.getenv('MAX_INPUT_LENGTH'))

throttle = Throttle()

prompt_template = ''
with open('prompt_template.txt', 'r') as f_prompt_template:
  prompt_template = f_prompt_template.read()
  
def parse_duration(duration_str: str) -> timedelta:
  days, hours, minutes = 0, 0, 0
  current_num = ''
  for char in duration_str:
    if char.isdigit():
      current_num += char
    else:
      if char == 'd':
        days = int(current_num)
      elif char == 'h':
        hours = int(current_num)
      elif char == 'm':
        minutes = int(current_num)
      current_num = ''
  return timedelta(days=days, hours=hours, minutes=minutes)

day_of_week = [
  'Sunday',
  'Monday',
  'Tuesday',
  'Wednesday',
  'Thursday',
  'Friday',
  'Saturday'
]

async def handle_general_message(update: 'telegram.Update', context: 'telegram.ext.CallbackContext') -> None:
  throttle.call()
  replyMessage = await update.message.reply_text('Processing...')
  content = ''
  if update.message.reply_to_message:
    content += update.message.reply_to_message.text
  content += update.message.text
  logger.info(f'Processing: <{content}>')
  if len([line for line in content.split('\n') if line.strip()]) == 0:
    logger.error(f'Empty input. Task aborted.')
    throttle.call()
    await replyMessage.edit_text('ERROR: No input. Task aborted.')
    return
  prompt = prompt_template.format(**{
    'content': content,
    'now': datetime.now().isoformat(timespec='seconds') + ' ' + day_of_week[datetime.now().weekday()],
  })
  message = ''
  result = []
  try:
    async for token in complete(prompt):
      result.append(token)
  except Exception as e:
    logger.error(f'ERROR: {repr(e)}')
    message += f'{''.join(result)}\n{'ERROR: LLM API request failed: '}{repr(e)}'
  if len(result) == 0:
    logger.error('No result returned.')
    message += f'{'ERROR: No result returned.'}\n'
  else:
    json_result = ''.join(result)
    # remove before the first occurrence of '{' and after the last occurrence of '}'
    start = json_result.find('{')
    end = json_result.rfind('}') + 1
    if start != -1 and end != -1:
      json_result = json_result[start:end]
    message += json_result
    json_result = json.loads(json_result)
    logger.info(f'Result: {json_result}')
    end_time = datetime.fromisoformat(json_result['start'])
    duration = parse_duration(json_result['duration'])
    start_time = end_time - duration
    dates_param = f'{start_time.strftime('%Y%m%dT%H%M%S')}Z/{end_time.strftime('%Y%m%dT%H%M%S')}Z'
    message += f'https://www.google.com/calendar/render?action=TEMPLATE&text={urllib.parse.quote(json_result["text"])}&dates={dates_param}&details={urllib.parse.quote(content[:200] + '\n\n' + 'generated by llm')}&location={urllib.parse.quote(json_result["location"])}&sf=true&output=xml'
    logger.info(f'Message: {message}')
  await replyMessage.edit_text(message)
