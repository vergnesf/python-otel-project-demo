"""Smoke tests for ingredientcheck consumer — verify consumer initializes correctly."""

from confluent_kafka import Consumer
from ingredientcheck.ingredientcheck_consumer import API_URL, consume_messages, consumer


def test_consumer_is_initialized():
    assert isinstance(consumer, Consumer)


def test_api_url_has_ingredients_path():
    assert API_URL.endswith("/ingredients")


def test_consume_messages_is_callable():
    assert callable(consume_messages)
