"""Tests for supplier producer message construction and Kafka send behaviour.

Verifies:
- Correct topic ("ingredient-deliveries")
- Message value is valid JSON
- Payload contains expected fields with correct values
- delivery_report callback is wired on every send
"""

import json
from unittest.mock import MagicMock, patch

from lib_models.models import IngredientStock, IngredientType
from supplier.supplier_producer import delivery_report, send_ingredient


def _make_mock_producer():
    return MagicMock()


def test_send_ingredient_calls_produce_with_correct_topic():
    ingredient = IngredientStock(ingredient_type=IngredientType.MALT, quantity=10)
    mock_producer = _make_mock_producer()
    with patch("supplier.supplier_producer.producer", mock_producer):
        send_ingredient(ingredient)
    mock_producer.produce.assert_called_once()
    topic = mock_producer.produce.call_args.args[0]
    assert topic == "ingredient-deliveries"


def test_send_ingredient_message_is_valid_json():
    ingredient = IngredientStock(ingredient_type=IngredientType.HOPS, quantity=5)
    mock_producer = _make_mock_producer()
    with patch("supplier.supplier_producer.producer", mock_producer):
        send_ingredient(ingredient)
    raw = mock_producer.produce.call_args.kwargs["value"]
    payload = json.loads(raw)
    assert isinstance(payload, dict)


def test_send_ingredient_message_contains_expected_fields():
    ingredient = IngredientStock(ingredient_type=IngredientType.YEAST, quantity=42)
    mock_producer = _make_mock_producer()
    with patch("supplier.supplier_producer.producer", mock_producer):
        send_ingredient(ingredient)
    payload = json.loads(mock_producer.produce.call_args.kwargs["value"])
    assert payload["ingredient_type"] == IngredientType.YEAST.value
    assert payload["quantity"] == 42


def test_send_ingredient_payload_matches_model():
    ingredient = IngredientStock(ingredient_type=IngredientType.WHEAT, quantity=7)
    mock_producer = _make_mock_producer()
    with patch("supplier.supplier_producer.producer", mock_producer):
        send_ingredient(ingredient)
    payload = json.loads(mock_producer.produce.call_args.kwargs["value"])
    assert payload == ingredient.model_dump()


def test_send_ingredient_wires_delivery_report_callback():
    ingredient = IngredientStock(ingredient_type=IngredientType.BARLEY, quantity=1)
    mock_producer = _make_mock_producer()
    with patch("supplier.supplier_producer.producer", mock_producer):
        send_ingredient(ingredient)
    assert mock_producer.produce.call_args.kwargs["callback"] is delivery_report
