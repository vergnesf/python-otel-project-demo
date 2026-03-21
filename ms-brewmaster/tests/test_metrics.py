"""Tests for business metrics counters in ms-brewmaster.

Counters are cumulative — tests use delta checks (value before vs after).
"""

from unittest.mock import MagicMock, patch

from brewmaster.brewmaster import process_registered_brew

BREW = {"id": 1, "ingredient_type": "malt", "quantity": 5, "brew_style": "lager"}


def _mock_get_response(brews):
    mock_resp = MagicMock()
    mock_resp.json.return_value = brews
    mock_resp.raise_for_status = MagicMock()
    return mock_resp


def _mock_post_response(status_code=200):
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.json.return_value = {}
    mock_resp.raise_for_status = MagicMock()
    return mock_resp


def _mock_put_response():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {}
    mock_resp.raise_for_status = MagicMock()
    return mock_resp


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


def test_brews_managed_ready_increments_on_success(metric_reader):
    before = _get_counter_value(metric_reader, "brews.managed", {"result": "ready"})
    with (
        patch("brewmaster.brewmaster.requests.get", return_value=_mock_get_response([BREW])),
        patch("brewmaster.brewmaster.requests.post", return_value=_mock_post_response(200)),
        patch("brewmaster.brewmaster.requests.put", return_value=_mock_put_response()),
        patch("brewmaster.brewmaster.random.random", return_value=0.5),
    ):
        process_registered_brew()
    after = _get_counter_value(metric_reader, "brews.managed", {"result": "ready"})
    assert after - before == 1


def test_brews_managed_error_increments_on_error_rate(metric_reader):
    """ERROR_RATE raises RuntimeError → result=error (not a business-rule block)."""
    before = _get_counter_value(metric_reader, "brews.managed", {"result": "error"})
    with (
        patch("brewmaster.brewmaster.requests.get", return_value=_mock_get_response([BREW])),
        patch("brewmaster.brewmaster.requests.post") as mock_post,
        patch("brewmaster.brewmaster.requests.put", return_value=_mock_put_response()),
        patch("brewmaster.brewmaster.random.random", return_value=0.0),
        patch.dict("os.environ", {"ERROR_RATE": "1.0"}),
    ):
        mock_post.return_value.status_code = 200
        process_registered_brew()
    after = _get_counter_value(metric_reader, "brews.managed", {"result": "error"})
    assert after - before == 1


def test_brews_managed_blocked_increments_on_insufficient_ingredients(metric_reader):
    """InsufficientIngredientError → result=blocked (real business failure)."""
    insufficient_resp = MagicMock()
    insufficient_resp.status_code = 400
    before = _get_counter_value(metric_reader, "brews.managed", {"result": "blocked"})
    with (
        patch("brewmaster.brewmaster.requests.get", return_value=_mock_get_response([BREW])),
        patch("brewmaster.brewmaster.requests.post", return_value=insufficient_resp),
        patch("brewmaster.brewmaster.requests.put", return_value=_mock_put_response()),
        patch("brewmaster.brewmaster.random.random", return_value=0.5),
    ):
        process_registered_brew()
    after = _get_counter_value(metric_reader, "brews.managed", {"result": "blocked"})
    assert after - before == 1
