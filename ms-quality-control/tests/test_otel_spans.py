"""Tests for OTEL span status and W3C trace context propagation in ms-quality-control."""

import json
from unittest.mock import MagicMock, patch

from opentelemetry.trace import StatusCode
from quality_control.quality_consumer import _process_message


def _make_msg(headers=None, payload=None):
    msg = MagicMock()
    msg.headers.return_value = headers or []
    msg.offset.return_value = 42
    msg.value.return_value = json.dumps(payload or {"id": 1, "brew_style": "ipa", "brew_status": "ready"}).encode()
    return msg


def test_span_name_and_kind(span_exporter):
    with patch("quality_control.quality_consumer.requests.put") as mock_put:
        mock_put.return_value.status_code = 200
        _process_message(_make_msg(), reject_rate=0.0, error_rate=0.0)

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == "process brews-ready"


def test_span_messaging_attributes(span_exporter):
    from quality_control.quality_consumer import _kafka_server_address

    with patch("quality_control.quality_consumer.requests.put") as mock_put:
        mock_put.return_value.status_code = 200
        _process_message(_make_msg(), reject_rate=0.0, error_rate=0.0)

    spans = span_exporter.get_finished_spans()
    assert spans[0].attributes["messaging.system"] == "kafka"
    assert spans[0].attributes["messaging.operation.name"] == "process"
    assert spans[0].attributes["messaging.destination.name"] == "brews-ready"
    assert spans[0].attributes["messaging.consumer.group.name"] == "quality-control-group"
    assert spans[0].attributes["server.address"] == _kafka_server_address
    assert spans[0].attributes["messaging.kafka.message.offset"] == 42


def test_approved_span_has_quality_passed_true(span_exporter):
    with patch("quality_control.quality_consumer.requests.put") as mock_put:
        mock_put.return_value.status_code = 200
        _process_message(_make_msg(), reject_rate=0.0, error_rate=0.0)

    spans = span_exporter.get_finished_spans()
    assert spans[0].attributes["quality.check.passed"] is True
    assert "quality.reject_reason" not in spans[0].attributes


def test_rejected_span_has_quality_passed_false_and_reason(span_exporter):
    with patch("quality_control.quality_consumer.requests.put") as mock_put:
        mock_put.return_value.status_code = 200
        _process_message(_make_msg(), reject_rate=1.0, error_rate=0.0)

    spans = span_exporter.get_finished_spans()
    assert spans[0].attributes["quality.check.passed"] is False
    assert spans[0].attributes["quality.reject_reason"] in ["color_off", "bitterness_high", "clarity_poor"]


def test_error_rate_sets_span_error(span_exporter):
    _process_message(_make_msg(), reject_rate=0.0, error_rate=1.0)

    spans = span_exporter.get_finished_spans()
    assert spans[0].status.status_code == StatusCode.ERROR
    assert spans[0].attributes["error.type"] == "RuntimeError"


def test_span_status_ok_on_success(span_exporter):
    with patch("quality_control.quality_consumer.requests.put") as mock_put:
        mock_put.return_value.status_code = 200
        _process_message(_make_msg(), reject_rate=0.0, error_rate=0.0)

    spans = span_exporter.get_finished_spans()
    assert spans[0].status.status_code == StatusCode.UNSET


def test_span_links_to_producer_trace(span_exporter):
    """process brews-ready span has a link to the producer span context via W3C headers."""
    trace_id = 0x4BF92F3577B34DA6A3CE929D0E0E4736
    span_id = 0xA3CE929D0E0E4736
    traceparent = f"00-{trace_id:032x}-{span_id:016x}-01"

    msg = _make_msg(headers=[("traceparent", traceparent.encode())])

    with patch("quality_control.quality_consumer.requests.put") as mock_put:
        mock_put.return_value.status_code = 200
        _process_message(msg, reject_rate=0.0, error_rate=0.0)

    spans = span_exporter.get_finished_spans()
    process_span = next((s for s in spans if s.name == "process brews-ready"), None)
    assert process_span is not None
    assert process_span.context.trace_id != trace_id
    assert len(process_span.links) == 1
    assert process_span.links[0].context.trace_id == trace_id


def test_malformed_json_sets_span_error(span_exporter):
    msg = MagicMock()
    msg.headers.return_value = []
    msg.offset.return_value = 0
    msg.value.return_value = b"not valid json {"

    _process_message(msg, reject_rate=0.0, error_rate=0.0)

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].status.status_code == StatusCode.ERROR
