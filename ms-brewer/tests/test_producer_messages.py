"""Tests for brewer producer message construction and Kafka send behaviour.

Strategy: patch the module-level `producer` instance with a MagicMock — confluent_kafka's
Producer is a C extension (cimpl.Producer) whose methods are read-only and cannot be
targeted by patch.object. Replacing the whole instance avoids this limitation and keeps
tests fully offline (no broker needed).

Verifies:
- Correct topic ("brew-orders")
- Message value is valid JSON
- Payload contains expected fields with correct values
- delivery_report callback is wired on every send
"""

import json
from unittest.mock import MagicMock, patch

from brewer.brewer_producer import delivery_report, send_brew_order
from lib_models.models import BrewOrder, BrewStyle, IngredientType


def _make_mock_producer():
    """Return a fresh MagicMock with the same interface as confluent_kafka.Producer."""
    return MagicMock()


def test_send_brew_order_calls_produce_with_correct_topic():
    order = BrewOrder(ingredient_type=IngredientType.MALT, quantity=10, brew_style=BrewStyle.IPA)
    mock_producer = _make_mock_producer()
    with patch("brewer.brewer_producer.producer", mock_producer):
        send_brew_order(order)
    mock_producer.produce.assert_called_once()
    topic = mock_producer.produce.call_args.args[0]
    assert topic == "brew-orders"


def test_send_brew_order_message_is_valid_json():
    order = BrewOrder(ingredient_type=IngredientType.HOPS, quantity=5, brew_style=BrewStyle.LAGER)
    mock_producer = _make_mock_producer()
    with patch("brewer.brewer_producer.producer", mock_producer):
        send_brew_order(order)
    raw = mock_producer.produce.call_args.kwargs["value"]
    payload = json.loads(raw)
    assert isinstance(payload, dict)


def test_send_brew_order_message_contains_expected_fields():
    order = BrewOrder(ingredient_type=IngredientType.YEAST, quantity=42, brew_style=BrewStyle.STOUT)
    mock_producer = _make_mock_producer()
    with patch("brewer.brewer_producer.producer", mock_producer):
        send_brew_order(order)
    payload = json.loads(mock_producer.produce.call_args.kwargs["value"])
    assert payload["ingredient_type"] == IngredientType.YEAST.value
    assert payload["quantity"] == 42
    assert payload["brew_style"] == BrewStyle.STOUT.value


def test_send_brew_order_payload_matches_model():
    order = BrewOrder(ingredient_type=IngredientType.WHEAT, quantity=7, brew_style=BrewStyle.WHEAT_BEER)
    mock_producer = _make_mock_producer()
    with patch("brewer.brewer_producer.producer", mock_producer):
        send_brew_order(order)
    payload = json.loads(mock_producer.produce.call_args.kwargs["value"])
    assert payload == order.model_dump()


def test_send_brew_order_wires_delivery_report_callback():
    order = BrewOrder(ingredient_type=IngredientType.BARLEY, quantity=1, brew_style=BrewStyle.IPA)
    mock_producer = _make_mock_producer()
    with patch("brewer.brewer_producer.producer", mock_producer):
        send_brew_order(order)
    assert mock_producer.produce.call_args.kwargs["callback"] is delivery_report
