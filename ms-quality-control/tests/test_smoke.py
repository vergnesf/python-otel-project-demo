"""Smoke test — verify the quality_consumer module imports correctly."""

from quality_control.quality_consumer import API_URL, _process_message, consume_messages


def test_imports():
    assert callable(consume_messages)
    assert callable(_process_message)
    assert API_URL.endswith("/brews")
