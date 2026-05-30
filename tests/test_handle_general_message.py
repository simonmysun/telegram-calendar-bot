"""Tests for handle_general_message."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from datetime import datetime, timedelta


SIMPLE_TEMPLATE = 'You are a calendar assistant. Output only JSON.'

VALID_LLM_JSON = '{"text": "Meeting with John", "location": "Office", "start": "2024-01-15T10:00:00", "duration": "0d0h40m"}'


async def _fake_complete_ok(user_content: str, system_prompt: str = ''):
    yield VALID_LLM_JSON


async def _fake_complete_empty(user_content: str, system_prompt: str = ''):
    # yields nothing
    return
    yield  # make it a generator


async def _fake_complete_raises(user_content: str, system_prompt: str = ''):
    raise RuntimeError('API unreachable')
    yield  # make it a generator


async def _fake_complete_bad_json(user_content: str, system_prompt: str = ''):
    yield 'not valid json at all'


@pytest.fixture(autouse=True)
def patch_throttle():
    """Replace Throttle.call() with an instant no-op for all tests in this module."""
    with patch('message_handler.handle_general_message.throttle') as mock_throttle:
        mock_throttle.call = AsyncMock()
        yield mock_throttle


@pytest.fixture(autouse=True)
def patch_prompt_template():
    """Return a simple template without touching the filesystem."""
    with patch(
        'message_handler.handle_general_message._load_prompt_template',
        return_value=SIMPLE_TEMPLATE,
    ):
        yield


# ---------- happy-path ----------

@pytest.mark.asyncio
async def test_valid_text_message_produces_calendar_url(make_update, mock_context):
    update = make_update(text='tomorrow 10am meeting with John for 40 minutes')
    with patch('message_handler.handle_general_message.complete', _fake_complete_ok):
        from message_handler.handle_general_message import handle_general_message
        await handle_general_message(update, mock_context)

    reply_msg = update.message.reply_text.return_value
    reply_msg.edit_text.assert_called_once()
    final_text: str = reply_msg.edit_text.call_args[0][0]
    assert 'google.com/calendar' in final_text
    assert 'Meeting with John' in final_text


@pytest.mark.asyncio
async def test_calendar_url_dates_are_start_to_end(make_update, mock_context):
    """start_time must be the JSON 'start' value; end_time = start + duration."""
    update = make_update(text='test event')
    with patch('message_handler.handle_general_message.complete', _fake_complete_ok):
        from message_handler.handle_general_message import handle_general_message
        await handle_general_message(update, mock_context)

    final_text: str = update.message.reply_text.return_value.edit_text.call_args[0][0]
    # start: 2024-01-15T10:00:00, duration 40 min → end: 2024-01-15T10:40:00
    assert '20240115T100000Z/20240115T104000Z' in final_text


@pytest.mark.asyncio
async def test_caption_only_message_is_handled(make_update, mock_context):
    """A message with only a caption (e.g. image) must still be processed."""
    update = make_update(text=None, caption='dinner tonight at 7pm')
    with patch('message_handler.handle_general_message.complete', _fake_complete_ok):
        from message_handler.handle_general_message import handle_general_message
        await handle_general_message(update, mock_context)

    reply_msg = update.message.reply_text.return_value
    reply_msg.edit_text.assert_called_once()
    assert 'google.com/calendar' in reply_msg.edit_text.call_args[0][0]


@pytest.mark.asyncio
async def test_reply_to_message_text_is_prepended(make_update, mock_context):
    """When the message is a reply, the replied-to text must be prepended."""
    update = make_update(text='that was 2 hours')
    update.message.reply_to_message = MagicMock()
    update.message.reply_to_message.text = 'I was working on project X'

    captured_prompts: list[str] = []

    async def capture_complete(user_content: str, system_prompt: str = ''):
        captured_prompts.append(user_content)
        yield VALID_LLM_JSON

    with patch('message_handler.handle_general_message.complete', capture_complete):
        from message_handler.handle_general_message import handle_general_message
        await handle_general_message(update, mock_context)

    assert len(captured_prompts) == 1
    assert 'I was working on project X' in captured_prompts[0]
    assert 'that was 2 hours' in captured_prompts[0]


# ---------- error paths ----------

@pytest.mark.asyncio
async def test_empty_message_returns_error(make_update, mock_context):
    update = make_update(text='   ')
    with patch('message_handler.handle_general_message.complete', _fake_complete_ok):
        from message_handler.handle_general_message import handle_general_message
        await handle_general_message(update, mock_context)

    reply_msg = update.message.reply_text.return_value
    reply_msg.edit_text.assert_called_once()
    assert 'ERROR' in reply_msg.edit_text.call_args[0][0]


@pytest.mark.asyncio
async def test_none_text_and_none_caption_returns_error(make_update, mock_context):
    update = make_update(text=None, caption=None)
    with patch('message_handler.handle_general_message.complete', _fake_complete_ok):
        from message_handler.handle_general_message import handle_general_message
        await handle_general_message(update, mock_context)

    assert 'ERROR' in update.message.reply_text.return_value.edit_text.call_args[0][0]


@pytest.mark.asyncio
async def test_llm_api_failure_returns_error(make_update, mock_context):
    update = make_update(text='test event')
    with patch('message_handler.handle_general_message.complete', _fake_complete_raises):
        from message_handler.handle_general_message import handle_general_message
        await handle_general_message(update, mock_context)

    final_text = update.message.reply_text.return_value.edit_text.call_args[0][0]
    assert 'ERROR' in final_text


@pytest.mark.asyncio
async def test_bad_json_from_llm_returns_error(make_update, mock_context):
    update = make_update(text='test event')
    with patch('message_handler.handle_general_message.complete', _fake_complete_bad_json):
        from message_handler.handle_general_message import handle_general_message
        await handle_general_message(update, mock_context)

    final_text = update.message.reply_text.return_value.edit_text.call_args[0][0]
    assert 'ERROR' in final_text


@pytest.mark.asyncio
async def test_input_truncated_to_max_length(make_update, mock_context):
    """Content longer than MAX_INPUT_LENGTH must be truncated before LLM call."""
    import message_handler.handle_general_message as mod
    original_max = mod.MAX_INPUT_LENGTH
    mod.MAX_INPUT_LENGTH = 10

    captured: list[str] = []

    async def capture_complete(user_content: str, system_prompt: str = ''):
        captured.append(user_content)
        yield VALID_LLM_JSON

    update = make_update(text='A' * 100)
    with patch('message_handler.handle_general_message.complete', capture_complete):
        from message_handler.handle_general_message import handle_general_message
        await handle_general_message(update, mock_context)

    mod.MAX_INPUT_LENGTH = original_max
    assert len(captured) == 1
    # The truncated content (10 'A's) must appear in the prompt.
    assert 'A' * 10 in captured[0]
    assert 'A' * 11 not in captured[0]
