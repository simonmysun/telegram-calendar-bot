"""Tests for handle_permission_check."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from telegram.ext import ApplicationHandlerStop

import telegram


@pytest.fixture(autouse=True)
def reset_module_state():
    """Reload permission module constants to match the conftest env vars."""
    import importlib
    import message_handler.handle_permission_check as mod
    importlib.reload(mod)
    yield


def _make_update(user_id: int, chat_type: str):
    update = MagicMock()
    update.message.from_user.id = user_id
    update.message.chat.id = 1000
    update.message.chat.type = chat_type
    update.message.reply_text = AsyncMock()
    return update


@pytest.mark.asyncio
async def test_allowed_user_in_private_chat_passes(mock_context):
    """An explicitly allowed user in a private chat must not be stopped."""
    from message_handler.handle_permission_check import handle_permission_check

    update = _make_update(user_id=111, chat_type=telegram.constants.ChatType.PRIVATE)
    # Should not raise ApplicationHandlerStop
    await handle_permission_check(update, mock_context)
    update.message.reply_text.assert_not_called()


@pytest.mark.asyncio
async def test_admin_user_in_private_chat_passes(mock_context):
    """An admin user in a private chat must not be stopped."""
    from message_handler.handle_permission_check import handle_permission_check

    update = _make_update(user_id=999, chat_type=telegram.constants.ChatType.PRIVATE)
    await handle_permission_check(update, mock_context)
    update.message.reply_text.assert_not_called()


@pytest.mark.asyncio
async def test_unknown_user_in_private_chat_denied(mock_context):
    """An unknown user in a private chat must receive a denial and stop propagation."""
    from message_handler.handle_permission_check import handle_permission_check

    update = _make_update(user_id=777, chat_type=telegram.constants.ChatType.PRIVATE)
    with pytest.raises(ApplicationHandlerStop):
        await handle_permission_check(update, mock_context)
    update.message.reply_text.assert_called_once_with('Permission denied')


@pytest.mark.asyncio
async def test_unknown_user_in_group_passes(mock_context):
    """Any user in a group chat must be permitted regardless of the whitelist."""
    from message_handler.handle_permission_check import handle_permission_check

    update = _make_update(user_id=777, chat_type=telegram.constants.ChatType.GROUP)
    await handle_permission_check(update, mock_context)
    update.message.reply_text.assert_not_called()


@pytest.mark.asyncio
async def test_unknown_user_in_supergroup_passes(mock_context):
    """Any user in a supergroup must be permitted."""
    from message_handler.handle_permission_check import handle_permission_check

    update = _make_update(user_id=777, chat_type=telegram.constants.ChatType.SUPERGROUP)
    await handle_permission_check(update, mock_context)
    update.message.reply_text.assert_not_called()
