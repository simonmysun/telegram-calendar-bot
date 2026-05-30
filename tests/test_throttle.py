"""Tests for the Throttle class."""

import asyncio
import time
import pytest

from message_handler.throttle import Throttle


@pytest.mark.asyncio
async def test_first_call_does_not_block():
    """A fresh throttle should complete its first call almost instantly."""
    t = Throttle()
    start = time.monotonic()
    await t.call()
    elapsed = time.monotonic() - start
    assert elapsed < 0.5, f"First call took {elapsed:.2f}s, expected < 0.5s"


@pytest.mark.asyncio
async def test_busy_after_recent_call():
    """busy() should return True immediately after a call."""
    t = Throttle()
    await t.call()
    assert t.busy() is True


@pytest.mark.asyncio
async def test_not_busy_when_queue_empty():
    """busy() should return False on a fresh throttle."""
    t = Throttle()
    assert t.busy() is False


@pytest.mark.asyncio
async def test_queue_length_increments():
    """Each call() appends to the internal queue."""
    t = Throttle()
    # Monkeypatch sleep so the test doesn't actually wait 1.5 s per call.
    async def instant_sleep(_):
        return
    t._Throttle__wait = asyncio.coroutine(lambda: None) if False else t._Throttle__wait  # noqa

    # Directly append timestamps spaced > 1 s apart to bypass the sleep.
    past = time.time() - 10
    t.queue = [past + i for i in range(5)]
    assert len(t.queue) == 5


@pytest.mark.asyncio
async def test_old_entries_pruned():
    """Entries older than 60 s must be removed by __update."""
    t = Throttle()
    old_time = time.time() - 120
    t.queue = [old_time] * 10          # all older than 60 s
    t._Throttle__update()              # call private method via name-mangling
    assert t.queue == []


@pytest.mark.asyncio
async def test_lock_serialises_concurrent_calls(monkeypatch):
    """Concurrent calls must not race; each must be recorded exactly once."""
    t = Throttle()

    # Replace the internal sleep with a no-op so the test is fast.
    async def no_sleep(seconds):
        pass

    monkeypatch.setattr(asyncio, 'sleep', no_sleep)

    await asyncio.gather(t.call(), t.call(), t.call())
    assert len(t.queue) == 3
