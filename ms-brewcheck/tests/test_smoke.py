"""Smoke tests for brewcheck consumer — verify consumer initializes correctly."""

from brewcheck.brewcheck_consumer import API_URL, consume_messages, consumer
from confluent_kafka import Consumer


def test_consumer_is_initialized():
    assert isinstance(consumer, Consumer)


def test_api_url_has_brews_path():
    assert API_URL.endswith("/brews")


def test_consume_messages_is_callable():
    assert callable(consume_messages)
