"""Smoke tests for dispatch consumer — verify consumer initializes correctly."""

from confluent_kafka import Consumer
from dispatch.dispatch_consumer import API_URL_BEERSTOCK, consume_messages, consumer


def test_consumer_is_initialized():
    assert isinstance(consumer, Consumer)


def test_api_url_has_beerstock_ship_path():
    assert API_URL_BEERSTOCK.endswith("/beerstock/ship")


def test_consume_messages_is_callable():
    assert callable(consume_messages)
