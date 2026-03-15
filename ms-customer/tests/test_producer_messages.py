"""Tests for customer producer message construction and Kafka send behaviour.

Strategy: patch the module-level `producer` instance with a MagicMock — confluent_kafka's
Producer is a C extension (cimpl.Producer) whose methods are read-only and cannot be
targeted by patch.object. Replacing the whole instance avoids this limitation and keeps
tests fully offline (no broker needed).

Verifies:
- Correct topic ("orders")
- Message value is valid JSON
- Payload contains expected fields with correct values
- delivery_report callback is wired on every send
"""

import json
from unittest.mock import MagicMock, patch

from customer.customer_producer import delivery_report, send_order
from lib_models.models import Order, WoodType


def _make_mock_producer():
    """Return a fresh MagicMock with the same interface as confluent_kafka.Producer."""
    return MagicMock()


def test_send_order_calls_produce_with_correct_topic():
    order = Order(wood_type=WoodType.OAK, quantity=10)
    mock_producer = _make_mock_producer()
    with patch("customer.customer_producer.producer", mock_producer):
        send_order(order)
    mock_producer.produce.assert_called_once()
    topic = mock_producer.produce.call_args.args[0]
    assert topic == "orders"


def test_send_order_message_is_valid_json():
    order = Order(wood_type=WoodType.MAPLE, quantity=5)
    mock_producer = _make_mock_producer()
    with patch("customer.customer_producer.producer", mock_producer):
        send_order(order)
    raw = mock_producer.produce.call_args.kwargs["value"]
    payload = json.loads(raw)
    assert isinstance(payload, dict)


def test_send_order_message_contains_expected_fields():
    order = Order(wood_type=WoodType.BIRCH, quantity=42)
    mock_producer = _make_mock_producer()
    with patch("customer.customer_producer.producer", mock_producer):
        send_order(order)
    payload = json.loads(mock_producer.produce.call_args.kwargs["value"])
    assert payload["wood_type"] == WoodType.BIRCH.value
    assert payload["quantity"] == 42


def test_send_order_payload_matches_order_model():
    order = Order(wood_type=WoodType.PINE, quantity=7)
    mock_producer = _make_mock_producer()
    with patch("customer.customer_producer.producer", mock_producer):
        send_order(order)
    payload = json.loads(mock_producer.produce.call_args.kwargs["value"])
    assert payload == order.model_dump()


def test_send_order_wires_delivery_report_callback():
    order = Order(wood_type=WoodType.ELM, quantity=1)
    mock_producer = _make_mock_producer()
    with patch("customer.customer_producer.producer", mock_producer):
        send_order(order)
    assert mock_producer.produce.call_args.kwargs["callback"] is delivery_report
