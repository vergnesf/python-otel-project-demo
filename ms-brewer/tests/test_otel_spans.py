"""Tests for OTEL span status and W3C trace context propagation in ms-brewer.

Uses InMemorySpanExporter — no OTEL collector or Kafka broker needed.
"""

from unittest.mock import patch

from brewer.brewer_producer import _run_once
from opentelemetry.trace import StatusCode


def test_send_brew_order_span_ok_on_success(span_exporter):
    with patch("brewer.brewer_producer.send_brew_order"):
        with patch("brewer.brewer_producer.random.random", return_value=0.5):
            _run_once(0.0)

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == "send brew-orders"
    assert spans[0].status.status_code == StatusCode.UNSET
    assert spans[0].attributes["messaging.system"] == "kafka"
    assert spans[0].attributes["messaging.operation.name"] == "send"
    assert spans[0].attributes["messaging.destination.name"] == "brew-orders"


def test_send_brew_order_span_error_on_error_rate(span_exporter):
    _run_once(1.0)

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].status.status_code == StatusCode.ERROR
    assert "simulated failure" in spans[0].status.description
    assert any(e.name == "exception" for e in spans[0].events)
    assert spans[0].attributes["error.type"] == "RuntimeError"


def test_send_brew_order_injects_traceparent_header(span_exporter):
    """W3C traceparent header is injected into Kafka message headers."""
    captured_headers: list | None = None

    def capture_produce(topic, value=None, headers=None, callback=None):
        nonlocal captured_headers
        captured_headers = headers

    with patch("brewer.brewer_producer.producer") as mock_producer:
        mock_producer.produce.side_effect = capture_produce
        mock_producer.poll.return_value = None
        with patch("brewer.brewer_producer.random.random", return_value=0.5):
            _run_once(0.0)

    assert captured_headers is not None
    header_keys = [k for k, _ in captured_headers]
    assert "traceparent" in header_keys
