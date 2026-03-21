"""Tests for business metrics counters in ms-supplier.

Counters are cumulative — tests use delta checks (value before vs after).
"""

from unittest.mock import patch

from supplier.supplier_producer import _run_once


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


def test_ingredient_deliveries_failed_increments_on_error_rate(metric_reader):
    before = _get_counter_value(metric_reader, "ingredient_deliveries.failed")
    _run_once(1.0)
    after = _get_counter_value(metric_reader, "ingredient_deliveries.failed")
    assert after - before == 1


def test_ingredient_deliveries_created_increments_on_success(metric_reader):
    before = _get_counter_value(metric_reader, "ingredient_deliveries.created")
    with patch("supplier.supplier_producer.send_ingredient"):
        _run_once(0.0)
    after = _get_counter_value(metric_reader, "ingredient_deliveries.created")
    assert after - before == 1
