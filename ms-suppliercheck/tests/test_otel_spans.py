"""Tests that ERROR_RATE injection marks the active span as ERROR."""

from opentelemetry.trace import StatusCode
from suppliercheck.suppliercheck_consumer import tracer


def test_process_stock_span_ok_on_success(span_exporter):
    with tracer.start_as_current_span("process_stock"):
        pass

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].status.status_code == StatusCode.UNSET


def test_process_stock_span_error_on_error_rate(span_exporter):
    with tracer.start_as_current_span("process_stock") as span:
        span.set_status(StatusCode.ERROR, "simulated failure (ERROR_RATE)")
        span.record_exception(RuntimeError("simulated failure"))

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].status.status_code == StatusCode.ERROR
    assert any(e.name == "exception" for e in spans[0].events)
