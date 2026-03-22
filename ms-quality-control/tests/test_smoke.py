"""Smoke test — verify the quality_consumer module imports correctly."""

from quality_control.quality_consumer import API_URL, consume_messages, _process_message


def test_imports():
    assert callable(consume_messages)
    assert callable(_process_message)
    assert API_URL.endswith("/brews")
