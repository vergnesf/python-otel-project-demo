"""Smoke tests for ordercheck service — verify consumer initializes and config loads."""

from urllib.parse import urlparse

from confluent_kafka import Consumer
from ordercheck.ordercheck_consumer import API_URL, consumer

# All imports are at module level: a collection-time ImportError is more diagnostic
# than a runtime ImportError buried inside a test function.
# Note: importing `consumer` triggers consumer.subscribe(["orders"]) at module level.
# confluent_kafka.Consumer.subscribe() is lazy — no Kafka connection until poll().
#
# Scope limitation: consumer group ID, bootstrap servers, topic assignment, and ERROR_RATE
# validity cannot be verified without a running Kafka broker. These tests confirm the module
# loads correctly and the API URL is well-formed, not that the service is fully configured.


def test_consumer_is_initialized():
    assert isinstance(consumer, Consumer)


def test_api_url_targets_orders_endpoint():
    parsed = urlparse(API_URL)
    assert parsed.scheme in ("http", "https")
    assert parsed.path == "/orders"
