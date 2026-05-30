"""
Shared fixtures and environment setup for the test suite.

Environment variables are set here BEFORE any application module is imported
so that module-level os.getenv() calls in the source files never receive None.
"""

import os

# Provide all required env vars before any source module is imported.
os.environ.setdefault('TELEGRAM_BOT_TOKEN', 'test_token')
os.environ.setdefault('OPENAI_API_KEY', 'test_key')
os.environ.setdefault('LLM_MODEL', 'gpt-4o')
os.environ.setdefault('OPENAI_API_URL', 'http://localhost:11434/v1/')
os.environ.setdefault('ALLOWED_TELEGRAM_USER_IDS', '111,222')
os.environ.setdefault('ADMIN_USER_IDS', '999')
os.environ.setdefault('MAX_INPUT_LENGTH', '2000')

import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_reply_message():
    """A fake Telegram message object returned by reply_text()."""
    msg = MagicMock()
    msg.edit_text = AsyncMock()
    return msg


@pytest.fixture
def make_update(mock_reply_message):
    """Factory that builds a minimal telegram.Update mock."""

    def _make(
        text: str | None = 'hello',
        caption: str | None = None,
        user_id: int = 111,
        chat_type: str = 'private',
        reply_text_str: str | None = None,
    ):
        update = MagicMock()
        update.message.text = text
        update.message.caption = caption
        update.message.reply_to_message = None
        update.message.from_user.id = user_id
        update.message.chat.id = 42
        update.message.chat.type = chat_type
        update.message.reply_text = AsyncMock(return_value=mock_reply_message)
        return update

    return _make


@pytest.fixture
def mock_context():
    ctx = MagicMock()
    ctx.bot.set_my_commands = AsyncMock()
    ctx.bot.get_my_commands = AsyncMock(return_value=[])
    return ctx
