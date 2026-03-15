"""Tests that ERROR_RATE injection marks the active span as ERROR.

Uses InMemorySpanExporter — no OTEL collector or Kafka broker needed.
"""

from unittest.mock import patch

from customer.customer_producer import _run_once
from opentelemetry.trace import StatusCode


def test_send_order_span_ok_on_success(span_exporter):
    with patch("customer.customer_producer.send_order"):
        with patch("customer.customer_producer.random.random", return_value=0.5):
            _run_once(0.0)

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].status.status_code == StatusCode.UNSET


def test_send_order_span_error_on_error_rate(span_exporter):
    _run_once(1.0)

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].status.status_code == StatusCode.ERROR
    assert "simulated failure" in spans[0].status.description
    # Exception event recorded
    events = spans[0].events
    assert any(e.name == "exception" for e in events)
