import logging
logger = logging.getLogger(__name__)

import asyncio
import time

class Throttle:
  # https://core.telegram.org/bots/faq#my-bot-is-hitting-limits-how-do-i-avoid-this
  # When sending messages inside a particular chat, avoid sending more than one message per second.
  # Also note that your bot will not be able to send more than 20 messages per minute to the same group.
  #
  # --> 1 message per second, 19 messages per rolling 60-second window

  def __init__(self):
    self.queue: list[float] = []
    self._lock: asyncio.Lock | None = None

  def _get_lock(self) -> asyncio.Lock:
    if self._lock is None:
      self._lock = asyncio.Lock()
    return self._lock

  async def call(self) -> None:
    async with self._get_lock():
      await self.__wait()
      self.queue.append(time.time())

  def busy(self) -> bool:
    self.__update()
    return len(self.queue) >= 19 or (len(self.queue) > 0 and time.time() - self.queue[-1] < 1)

  def __update(self) -> None:
    now = time.time()
    self.queue = [timestamp for timestamp in self.queue if timestamp > now - 60]

  async def __wait(self) -> None:
    while True:
      self.__update()
      now = time.time()
      if len(self.queue) >= 19:
        wait_time = 60.5 - (now - self.queue[0])
        if wait_time > 0:
          logger.info(f'length of queue = {len(self.queue)}, waiting {wait_time:.1f}s to dequeue. Throttling...')
          await asyncio.sleep(wait_time)
          continue
      elif len(self.queue) > 0 and now - self.queue[-1] < 1:
        wait_time = 1.5 - (now - self.queue[-1])
        if wait_time > 0:
          logger.info(f'last sent {(now - self.queue[-1]):.2f}s ago. Throttling...')
          await asyncio.sleep(wait_time)
          continue
      break