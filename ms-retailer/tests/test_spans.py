"""Tests for span attributes in ms-retailer (semconv compliance)."""

from unittest.mock import patch

from retailer.retailer_producer import _run_once


def _get_span(span_exporter, name):
    spans = [s for s in span_exporter.get_finished_spans() if s.name == name]
    assert spans, f"No span named '{name}' found"
    return spans[-1]


def test_producer_span_has_server_address(span_exporter):
    from retailer.retailer_producer import _kafka_server_address

    with patch("retailer.retailer_producer.send_beer_order"):
        _run_once(0.0)
    span = _get_span(span_exporter, "send beer-order")
    assert span.attributes.get("server.address") == _kafka_server_address


def test_producer_span_has_retailer_name(span_exporter):
    with patch("retailer.retailer_producer.send_beer_order"):
        _run_once(0.0)
    span = _get_span(span_exporter, "send beer-order")
    assert "retailer.name" in span.attributes


def test_producer_span_has_brew_style(span_exporter):
    with patch("retailer.retailer_producer.send_beer_order"):
        _run_once(0.0)
    span = _get_span(span_exporter, "send beer-order")
    assert "brew.style" in span.attributes
