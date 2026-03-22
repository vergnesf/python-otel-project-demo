"""Tests for span attributes in ms-supplier (semconv compliance)."""

from unittest.mock import patch

from supplier.supplier_producer import _run_once


def _get_span(span_exporter, name):
    spans = [s for s in span_exporter.get_finished_spans() if s.name == name]
    assert spans, f"No span named '{name}' found"
    return spans[-1]


def test_producer_span_has_server_address(span_exporter):
    with patch("supplier.supplier_producer.send_ingredient"):
        _run_once(0.0)
    span = _get_span(span_exporter, "send ingredient-deliveries")
    assert "server.address" in span.attributes
    assert isinstance(span.attributes["server.address"], str)
    assert span.attributes["server.address"] != ""
