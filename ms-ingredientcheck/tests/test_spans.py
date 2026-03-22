"""Tests for span attributes in ms-ingredientcheck (semconv compliance)."""

import json
from unittest.mock import MagicMock, patch

from ingredientcheck.ingredientcheck_consumer import _process_message


def _make_msg(payload=None):
    msg = MagicMock()
    msg.headers.return_value = []
    msg.offset.return_value = 42
    msg.value.return_value = json.dumps(payload or {"ingredient_type": "malt", "quantity": 10}).encode()
    return msg


def _get_span(span_exporter, name):
    spans = [s for s in span_exporter.get_finished_spans() if s.name == name]
    assert spans, f"No span named '{name}' found"
    return spans[-1]


def test_consumer_span_has_server_address(span_exporter):
    with patch("ingredientcheck.ingredientcheck_consumer.requests.post") as mock_post:
        mock_post.return_value.status_code = 201
        _process_message(_make_msg(), 0.0)
    span = _get_span(span_exporter, "process ingredient-deliveries")
    assert "server.address" in span.attributes
    assert isinstance(span.attributes["server.address"], str)
    assert span.attributes["server.address"] != ""


def test_consumer_span_has_kafka_message_offset(span_exporter):
    with patch("ingredientcheck.ingredientcheck_consumer.requests.post") as mock_post:
        mock_post.return_value.status_code = 201
        _process_message(_make_msg(), 0.0)
    span = _get_span(span_exporter, "process ingredient-deliveries")
    assert span.attributes.get("messaging.kafka.message.offset") == 42
