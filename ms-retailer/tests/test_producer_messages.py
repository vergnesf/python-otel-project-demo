"""Tests for retailer producer message construction and Kafka send behaviour."""

import json
from unittest.mock import MagicMock, patch

from lib_models.models import BeerOrder, BrewStyle
from retailer.retailer_producer import delivery_report, send_beer_order


def _make_mock_producer():
    return MagicMock()


def test_send_beer_order_calls_produce_with_correct_topic():
    order = BeerOrder(brew_style=BrewStyle.IPA, quantity=5, retailer_name="Bar du Port")
    mock_producer = _make_mock_producer()
    with patch("retailer.retailer_producer.producer", mock_producer):
        send_beer_order(order)
    mock_producer.produce.assert_called_once()
    topic = mock_producer.produce.call_args.args[0]
    assert topic == "beer-orders"


def test_send_beer_order_message_is_valid_json():
    order = BeerOrder(brew_style=BrewStyle.LAGER, quantity=10, retailer_name="Cave Martin")
    mock_producer = _make_mock_producer()
    with patch("retailer.retailer_producer.producer", mock_producer):
        send_beer_order(order)
    raw = mock_producer.produce.call_args.kwargs["value"]
    payload = json.loads(raw)
    assert isinstance(payload, dict)


def test_send_beer_order_message_contains_expected_fields():
    order = BeerOrder(brew_style=BrewStyle.STOUT, quantity=3, retailer_name="Le Zinc")
    mock_producer = _make_mock_producer()
    with patch("retailer.retailer_producer.producer", mock_producer):
        send_beer_order(order)
    payload = json.loads(mock_producer.produce.call_args.kwargs["value"])
    assert payload["brew_style"] == BrewStyle.STOUT.value
    assert payload["quantity"] == 3
    assert payload["retailer_name"] == "Le Zinc"


def test_send_beer_order_payload_matches_model():
    order = BeerOrder(brew_style=BrewStyle.WHEAT_BEER, quantity=7, retailer_name="Bistrot des Halles")
    mock_producer = _make_mock_producer()
    with patch("retailer.retailer_producer.producer", mock_producer):
        send_beer_order(order)
    payload = json.loads(mock_producer.produce.call_args.kwargs["value"])
    assert payload == order.model_dump()


def test_send_beer_order_wires_delivery_report_callback():
    order = BeerOrder(brew_style=BrewStyle.IPA, quantity=1, retailer_name="Brasserie du Centre")
    mock_producer = _make_mock_producer()
    with patch("retailer.retailer_producer.producer", mock_producer):
        send_beer_order(order)
    assert mock_producer.produce.call_args.kwargs["callback"] is delivery_report
