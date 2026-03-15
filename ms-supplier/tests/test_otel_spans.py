"""Tests that ERROR_RATE injection marks the active span as ERROR."""

from unittest.mock import patch

from opentelemetry.trace import StatusCode
from supplier.supplier_producer import _run_once


def test_send_stock_span_ok_on_success(span_exporter):
    with patch("supplier.supplier_producer.send_stock"):
        with patch("supplier.supplier_producer.random.random", return_value=0.5):
            _run_once(0.0)

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].status.status_code == StatusCode.UNSET


def test_send_stock_span_error_on_error_rate(span_exporter):
    _run_once(1.0)

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].status.status_code == StatusCode.ERROR
    assert "simulated failure" in spans[0].status.description
    assert any(e.name == "exception" for e in spans[0].events)
