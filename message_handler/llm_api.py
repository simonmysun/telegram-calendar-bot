import logging
logger = logging.getLogger(__name__)

import os
from typing import AsyncIterator

from openai import AsyncOpenAI

LLM_MODEL = os.getenv('LLM_MODEL')
SYSTEM_PROMPT = 'You are a helpful assistant.'

client = AsyncOpenAI(
  api_key=os.getenv('OPENAI_API_KEY'),
  base_url=os.getenv('OPENAI_API_URL') or 'https://api.openai.com/v1/',
)

async def complete(user_content: str, system_prompt: str = SYSTEM_PROMPT) -> AsyncIterator[str]:
  stream = await client.chat.completions.create(
    model=LLM_MODEL,
    messages=[
      {"role": "system", "content": system_prompt},
      {"role": "user", "content": user_content}
    ],
    stream=True
  )
  async for chunk in stream:
    if chunk.choices and chunk.choices[0].delta.content:
      yield chunk.choices[0].delta.content
    else:
      logger.debug(f'Skipping empty chunk: {chunk}')