"""Tests for the LLM API wrapper (llm_api.complete)."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


def _make_chunk(content: str | None):
    """Build a minimal mock chunk resembling openai.types.chat.ChatCompletionChunk."""
    chunk = MagicMock()
    chunk.choices = [MagicMock()]
    chunk.choices[0].delta.content = content
    return chunk


class _AsyncIteratorMock:
    """Wraps a list of items as an async iterator."""

    def __init__(self, items):
        self._items = iter(items)

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return next(self._items)
        except StopIteration:
            raise StopAsyncIteration


@pytest.mark.asyncio
async def test_complete_yields_content_tokens():
    chunks = [
        _make_chunk('{"text":'),
        _make_chunk(' "Meeting"}'),
    ]

    mock_stream = _AsyncIteratorMock(chunks)

    with patch('message_handler.llm_api.client') as mock_client:
        mock_client.chat.completions.create = AsyncMock(return_value=mock_stream)

        from message_handler.llm_api import complete
        tokens = [t async for t in complete('some prompt')]

    assert tokens == ['{"text":', ' "Meeting"}']


@pytest.mark.asyncio
async def test_complete_skips_empty_content_chunks():
    """Chunks with None content (e.g. the final [DONE] marker) must be silently skipped."""
    chunks = [
        _make_chunk('hello'),
        _make_chunk(None),   # should be skipped
        _make_chunk(' world'),
    ]
    mock_stream = _AsyncIteratorMock(chunks)

    with patch('message_handler.llm_api.client') as mock_client:
        mock_client.chat.completions.create = AsyncMock(return_value=mock_stream)

        from message_handler.llm_api import complete
        tokens = [t async for t in complete('prompt')]

    assert tokens == ['hello', ' world']


@pytest.mark.asyncio
async def test_complete_propagates_api_error():
    """If the API call itself raises, the exception must propagate to the caller."""
    with patch('message_handler.llm_api.client') as mock_client:
        mock_client.chat.completions.create = AsyncMock(
            side_effect=RuntimeError('connection refused')
        )

        from message_handler.llm_api import complete
        with pytest.raises(RuntimeError, match='connection refused'):
            async for _ in complete('prompt'):
                pass


@pytest.mark.asyncio
async def test_complete_uses_system_role():
    """The messages list must contain a 'system' role entry (not 'developer')."""
    mock_stream = _AsyncIteratorMock([])

    with patch('message_handler.llm_api.client') as mock_client:
        mock_client.chat.completions.create = AsyncMock(return_value=mock_stream)

        from message_handler.llm_api import complete
        async for _ in complete('test'):
            pass

        call_kwargs = mock_client.chat.completions.create.call_args
        messages = call_kwargs.kwargs.get('messages') or call_kwargs[1].get('messages') or call_kwargs[0][1]
        roles = [m['role'] for m in messages]
        assert 'system' in roles
        assert 'developer' not in roles
