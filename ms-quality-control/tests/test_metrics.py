"""Tests for business metrics counters in ms-quality-control."""

import json
from unittest.mock import MagicMock, patch

from quality_control.quality_consumer import _process_message


def _make_msg(payload=None):
    msg = MagicMock()
    msg.headers.return_value = []
    msg.offset.return_value = 42
    msg.value.return_value = json.dumps(payload or {"id": 1, "brew_style": "ipa", "brew_status": "ready"}).encode()
    return msg


def _get_counter_value(metric_reader, metric_name, attributes=None):
    data = metric_reader.get_metrics_data()
    if data is None:
        return 0
    for rm in data.resource_metrics:
        for sm in rm.scope_metrics:
            for metric in sm.metrics:
                if metric.name == metric_name:
                    total = 0
                    for dp in metric.data.data_points:
                        if attributes is None or all(dp.attributes.get(k) == v for k, v in attributes.items()):
                            total += dp.value
                    return total
    return 0


def test_quality_checked_increments_on_approved(metric_reader):
    before = _get_counter_value(metric_reader, "brews.quality_checked")
    with patch("quality_control.quality_consumer.requests.put") as mock_put:
        mock_put.return_value.status_code = 200
        _process_message(_make_msg(), reject_rate=0.0, error_rate=0.0)
    after = _get_counter_value(metric_reader, "brews.quality_checked")
    assert after - before == 1


def test_quality_rejected_increments_on_rejected(metric_reader):
    before = _get_counter_value(metric_reader, "brews.quality_rejected")
    with patch("quality_control.quality_consumer.requests.put") as mock_put:
        mock_put.return_value.status_code = 200
        _process_message(_make_msg(), reject_rate=1.0, error_rate=0.0)
    after = _get_counter_value(metric_reader, "brews.quality_rejected")
    assert after - before == 1


def test_quality_errors_increments_on_error_rate(metric_reader):
    before = _get_counter_value(metric_reader, "brews.quality_errors")
    _process_message(_make_msg(), reject_rate=0.0, error_rate=1.0)
    after = _get_counter_value(metric_reader, "brews.quality_errors")
    assert after - before == 1


def test_quality_errors_increments_on_malformed_message(metric_reader):
    msg = MagicMock()
    msg.headers.return_value = []
    msg.offset.return_value = 0
    msg.value.return_value = b"not valid json {"
    before = _get_counter_value(metric_reader, "brews.quality_errors")
    _process_message(msg, reject_rate=0.0, error_rate=0.0)
    after = _get_counter_value(metric_reader, "brews.quality_errors")
    assert after - before == 1
