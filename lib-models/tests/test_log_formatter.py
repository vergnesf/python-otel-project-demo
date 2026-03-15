"""Unit tests for lib_models.log_formatter.OtelJsonFormatter."""

import json
import logging

from lib_models.log_formatter import OtelJsonFormatter


def _make_record(msg="test message", level=logging.INFO, exc_info=None):
    """Build a LogRecord with optional OTEL attributes."""
    record = logging.LogRecord(
        name="test.logger",
        level=level,
        pathname="",
        lineno=0,
        msg=msg,
        args=(),
        exc_info=exc_info,
    )
    return record


def test_output_is_valid_json():
    formatter = OtelJsonFormatter()
    record = _make_record()
    output = formatter.format(record)
    parsed = json.loads(output)
    assert isinstance(parsed, dict)


def test_required_fields_present():
    formatter = OtelJsonFormatter()
    record = _make_record("hello world")
    parsed = json.loads(formatter.format(record))
    assert parsed["message"] == "hello world"
    assert parsed["level"] == "INFO"
    assert parsed["logger"] == "test.logger"
    assert "timestamp" in parsed
    assert "trace_id" in parsed
    assert "span_id" in parsed


def test_trace_id_fallback_when_not_set():
    formatter = OtelJsonFormatter()
    record = _make_record()
    parsed = json.loads(formatter.format(record))
    assert parsed["trace_id"] == ""
    assert parsed["span_id"] == ""


def test_trace_id_extracted_from_otel_attributes():
    formatter = OtelJsonFormatter()
    record = _make_record()
    record.otelTraceID = "4bf92f3577b34da6a3ce929d0e0e4736"
    record.otelSpanID = "a3ce929d0e0e4736"
    parsed = json.loads(formatter.format(record))
    assert parsed["trace_id"] == "4bf92f3577b34da6a3ce929d0e0e4736"
    assert parsed["span_id"] == "a3ce929d0e0e4736"


def test_exception_field_present_on_exc_info():
    formatter = OtelJsonFormatter()
    try:
        raise ValueError("boom")
    except ValueError:
        import sys
        record = _make_record(exc_info=sys.exc_info())

    parsed = json.loads(formatter.format(record))
    assert "exception" in parsed
    assert "ValueError" in parsed["exception"]


def test_no_exception_field_without_exc_info():
    formatter = OtelJsonFormatter()
    record = _make_record()
    parsed = json.loads(formatter.format(record))
    assert "exception" not in parsed
