"""Tests for supplier producer message construction and Kafka send behaviour.

Strategy: patch the module-level `producer` instance with a MagicMock — confluent_kafka's
Producer is a C extension (cimpl.Producer) whose methods are read-only and cannot be
targeted by patch.object. Replacing the whole instance avoids this limitation and keeps
tests fully offline (no broker needed).

Verifies:
- Correct topic ("stocks")
- Message value is valid JSON
- Payload contains expected fields with correct values
- delivery_report callback is wired on every send
"""

import json
from unittest.mock import MagicMock, patch

from lib_models.models import Stock, WoodType
from supplier.supplier_producer import delivery_report, send_stock


def _make_mock_producer():
    """Return a fresh MagicMock with the same interface as confluent_kafka.Producer."""
    return MagicMock()


def test_send_stock_calls_produce_with_correct_topic():
    stock = Stock(wood_type=WoodType.OAK, quantity=10)
    mock_producer = _make_mock_producer()
    with patch("supplier.supplier_producer.producer", mock_producer):
        send_stock(stock)
    mock_producer.produce.assert_called_once()
    topic = mock_producer.produce.call_args.args[0]
    assert topic == "stocks"


def test_send_stock_message_is_valid_json():
    stock = Stock(wood_type=WoodType.MAPLE, quantity=5)
    mock_producer = _make_mock_producer()
    with patch("supplier.supplier_producer.producer", mock_producer):
        send_stock(stock)
    raw = mock_producer.produce.call_args.kwargs["value"]
    payload = json.loads(raw)
    assert isinstance(payload, dict)


def test_send_stock_message_contains_expected_fields():
    stock = Stock(wood_type=WoodType.BIRCH, quantity=42)
    mock_producer = _make_mock_producer()
    with patch("supplier.supplier_producer.producer", mock_producer):
        send_stock(stock)
    payload = json.loads(mock_producer.produce.call_args.kwargs["value"])
    assert payload["wood_type"] == WoodType.BIRCH.value
    assert payload["quantity"] == 42


def test_send_stock_payload_matches_stock_model():
    stock = Stock(wood_type=WoodType.PINE, quantity=7)
    mock_producer = _make_mock_producer()
    with patch("supplier.supplier_producer.producer", mock_producer):
        send_stock(stock)
    payload = json.loads(mock_producer.produce.call_args.kwargs["value"])
    assert payload == stock.model_dump()


def test_send_stock_wires_delivery_report_callback():
    stock = Stock(wood_type=WoodType.ELM, quantity=1)
    mock_producer = _make_mock_producer()
    with patch("supplier.supplier_producer.producer", mock_producer):
        send_stock(stock)
    assert mock_producer.produce.call_args.kwargs["callback"] is delivery_report
