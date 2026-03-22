"""Tests for span attributes in ms-brewer (semconv compliance)."""

from unittest.mock import patch

from brewer.brewer_producer import _run_once


def _get_span(span_exporter, name):
    spans = [s for s in span_exporter.get_finished_spans() if s.name == name]
    assert spans, f"No span named '{name}' found"
    return spans[-1]


def test_producer_span_has_server_address(span_exporter):
    from brewer.brewer_producer import _kafka_server_address

    with patch("brewer.brewer_producer.send_brew_order"):
        _run_once(0.0)
    span = _get_span(span_exporter, "send brew-orders")
    assert span.attributes.get("server.address") == _kafka_server_address
