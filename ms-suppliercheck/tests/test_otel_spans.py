"""Tests for OTEL span status and W3C trace context propagation in ms-suppliercheck."""

import json
from unittest.mock import MagicMock, patch

from opentelemetry.trace import StatusCode
from suppliercheck.suppliercheck_consumer import _process_message


def _make_msg(headers=None, payload=None):
    msg = MagicMock()
    msg.headers.return_value = headers or []
    msg.value.return_value = json.dumps(payload or {"wood_type": "oak", "quantity": 5}).encode()
    return msg


def test_process_stock_span_ok_on_success(span_exporter):
    with patch("suppliercheck.suppliercheck_consumer.requests.post") as mock_post:
        mock_post.return_value.status_code = 201
        _process_message(_make_msg(), 0.0)

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == "process stocks"
    assert spans[0].status.status_code == StatusCode.UNSET
    assert spans[0].attributes["messaging.system"] == "kafka"
    assert spans[0].attributes["messaging.destination.name"] == "stocks"
    assert spans[0].attributes["messaging.consumer.group.name"] == "stock-check-group"


def test_process_stock_span_error_on_error_rate(span_exporter):
    _process_message(_make_msg(), 1.0)

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].status.status_code == StatusCode.ERROR
    assert any(e.name == "exception" for e in spans[0].events)
    assert spans[0].attributes["error.type"] == "RuntimeError"


def test_process_stock_links_to_producer_trace(span_exporter):
    """process_stock span has a link to the producer span context via W3C headers.

    Per OTEL messaging spec, consumers use span links (not parent-child) to
    correlate with the producer trace.
    """
    trace_id = 0x4BF92F3577B34DA6A3CE929D0E0E4736
    span_id = 0xA3CE929D0E0E4736
    traceparent = f"00-{trace_id:032x}-{span_id:016x}-01"

    msg = _make_msg(headers=[("traceparent", traceparent.encode())])

    with patch("suppliercheck.suppliercheck_consumer.requests.post") as mock_post:
        mock_post.return_value.status_code = 201
        _process_message(msg, 0.0)

    spans = span_exporter.get_finished_spans()
    process_span = next((s for s in spans if s.name == "process stocks"), None)
    assert process_span is not None
    # Consumer span has its own trace_id (not the producer's)
    assert process_span.context.trace_id != trace_id
    # Producer trace is referenced via a link
    assert len(process_span.links) == 1
    assert process_span.links[0].context.trace_id == trace_id
