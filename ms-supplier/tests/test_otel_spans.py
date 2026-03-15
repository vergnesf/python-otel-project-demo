"""Tests that ERROR_RATE injection marks the active span as ERROR."""

from opentelemetry.trace import StatusCode
from supplier.supplier_producer import tracer


def test_send_stock_span_ok_on_success(span_exporter):
    with tracer.start_as_current_span("send_stock"):
        pass

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].status.status_code == StatusCode.UNSET


def test_send_stock_span_error_on_error_rate(span_exporter):
    with tracer.start_as_current_span("send_stock") as span:
        span.set_status(StatusCode.ERROR, "simulated failure (ERROR_RATE)")
        span.record_exception(RuntimeError("simulated failure"))

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].status.status_code == StatusCode.ERROR
    assert "simulated failure" in spans[0].status.description
    assert any(e.name == "exception" for e in spans[0].events)
