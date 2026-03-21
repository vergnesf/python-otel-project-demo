"""Tests for business metrics counters in ms-ingredientcheck.

Counters are cumulative — tests use delta checks (value before vs after).
"""

import json
from unittest.mock import MagicMock, patch

from ingredientcheck.ingredientcheck_consumer import _process_message


def _make_msg(payload=None):
    msg = MagicMock()
    msg.headers.return_value = []
    msg.value.return_value = json.dumps(payload or {"ingredient_type": "malt", "quantity": 10}).encode()
    return msg


def _get_counter_value(metric_reader, metric_name, attributes=None):
    """Return cumulative counter value for a metric, optionally filtered by attributes."""
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


def test_ingredient_deliveries_processing_errors_increments_on_error_rate(metric_reader):
    before = _get_counter_value(metric_reader, "ingredient_deliveries.processing_errors")
    _process_message(_make_msg(), 1.0)
    after = _get_counter_value(metric_reader, "ingredient_deliveries.processing_errors")
    assert after - before == 1


def test_ingredient_deliveries_processed_increments_on_success(metric_reader):
    before = _get_counter_value(metric_reader, "ingredient_deliveries.processed")
    with patch("ingredientcheck.ingredientcheck_consumer.requests.post") as mock_post:
        mock_post.return_value.status_code = 201
        _process_message(_make_msg(), 0.0)
    after = _get_counter_value(metric_reader, "ingredient_deliveries.processed")
    assert after - before == 1


def test_ingredient_deliveries_processing_errors_increments_on_malformed_message(metric_reader):
    msg = MagicMock()
    msg.headers.return_value = []
    msg.value.return_value = b"not valid json {"
    before = _get_counter_value(metric_reader, "ingredient_deliveries.processing_errors")
    _process_message(msg, 0.0)
    after = _get_counter_value(metric_reader, "ingredient_deliveries.processing_errors")
    assert after - before == 1
