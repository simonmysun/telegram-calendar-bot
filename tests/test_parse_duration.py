"""Tests for the parse_duration() helper in handle_general_message."""

import pytest
from datetime import timedelta

from message_handler.handle_general_message import parse_duration


@pytest.mark.parametrize('s, expected', [
    ('0d0h0m',   timedelta(0)),
    ('1d',        timedelta(days=1)),
    ('2h',        timedelta(hours=2)),
    ('45m',       timedelta(minutes=45)),
    ('1d3h12m',   timedelta(days=1, hours=3, minutes=12)),
    ('0d0h45m',   timedelta(minutes=45)),
    ('10d',       timedelta(days=10)),
    ('',          timedelta(0)),   # empty string → zero duration
])
def test_parse_duration(s: str, expected: timedelta):
    assert parse_duration(s) == expected
