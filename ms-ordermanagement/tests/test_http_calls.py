"""Tests for ordermanagement HTTP logic with patched requests.

All three HTTP functions (fetch_registered_orders, decrease_stock, update_order_status)
and the orchestrator (process_registered_order) are tested directly — no loop to drive.

requests.get / .post / .put are patched at module level.
random.random is patched to 0.5 when testing happy paths so ERROR_RATE (default 0.1)
never triggers. For error-injection tests, random.random is forced to 0.0 (< any rate).
"""

from unittest.mock import MagicMock, patch

import pytest
import requests
from lib_models.models import OrderStatus

ORDER = {"id": 1, "wood_type": "oak", "quantity": 5}
ORDERS_LIST = [ORDER]


# ---------------------------------------------------------------------------
# fetch_registered_orders
# ---------------------------------------------------------------------------


def test_fetch_orders_returns_list_on_success():
    mock_resp = MagicMock()
    mock_resp.json.return_value = ORDERS_LIST
    with patch("ordermanagement.ordermanagement.requests.get", return_value=mock_resp) as mock_get:
        mock_resp.raise_for_status = MagicMock()
        from ordermanagement.ordermanagement import fetch_registered_orders

        result = fetch_registered_orders()

    mock_get.assert_called_once()
    called_url = mock_get.call_args.args[0]
    assert called_url.endswith("/orders/status/registered")
    assert result == ORDERS_LIST


def test_fetch_orders_returns_empty_list_on_request_exception():
    with patch("ordermanagement.ordermanagement.requests.get", side_effect=requests.RequestException("down")):
        from ordermanagement.ordermanagement import fetch_registered_orders

        result = fetch_registered_orders()

    assert result == []


# ---------------------------------------------------------------------------
# decrease_stock
# ---------------------------------------------------------------------------


def test_decrease_stock_calls_post_with_correct_payload():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {}
    mock_resp.raise_for_status = MagicMock()
    with patch("ordermanagement.ordermanagement.requests.post", return_value=mock_resp) as mock_post:
        from ordermanagement.ordermanagement import decrease_stock

        decrease_stock(ORDER)

    mock_post.assert_called_once()
    payload = mock_post.call_args.kwargs["json"]
    assert payload["wood_type"] == ORDER["wood_type"]
    assert payload["quantity"] == ORDER["quantity"]


def test_decrease_stock_raises_on_400():
    mock_resp = MagicMock()
    mock_resp.status_code = 400
    with patch("ordermanagement.ordermanagement.requests.post", return_value=mock_resp):
        from ordermanagement.ordermanagement import decrease_stock

        with pytest.raises(Exception, match="Insufficient stock"):
            decrease_stock(ORDER)


def test_decrease_stock_raises_on_404():
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    with patch("ordermanagement.ordermanagement.requests.post", return_value=mock_resp):
        from ordermanagement.ordermanagement import decrease_stock

        with pytest.raises(Exception, match="Stock not found"):
            decrease_stock(ORDER)


# ---------------------------------------------------------------------------
# update_order_status
# ---------------------------------------------------------------------------


def test_update_order_status_calls_put_with_correct_payload():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {}
    mock_resp.raise_for_status = MagicMock()
    with patch("ordermanagement.ordermanagement.requests.put", return_value=mock_resp) as mock_put:
        from ordermanagement.ordermanagement import update_order_status

        update_order_status(1, OrderStatus.READY)

    mock_put.assert_called_once()
    assert mock_put.call_args.kwargs["json"] == {"order_status": "ready"}


def test_update_order_status_raises_on_request_exception():
    with patch("ordermanagement.ordermanagement.requests.put", side_effect=requests.RequestException("timeout")):
        from ordermanagement.ordermanagement import update_order_status

        with pytest.raises(requests.RequestException):
            update_order_status(1, OrderStatus.READY)


# ---------------------------------------------------------------------------
# process_registered_order
# ---------------------------------------------------------------------------


def _mock_get_response(orders):
    mock_resp = MagicMock()
    mock_resp.json.return_value = orders
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


def test_process_happy_path_updates_status_to_ready():
    with (
        patch("ordermanagement.ordermanagement.requests.get", return_value=_mock_get_response(ORDERS_LIST)),
        patch("ordermanagement.ordermanagement.requests.post", return_value=_mock_post_response(200)),
        patch("ordermanagement.ordermanagement.requests.put", return_value=_mock_put_response()) as mock_put,
        patch("ordermanagement.ordermanagement.random.random", return_value=0.5),
    ):
        from ordermanagement.ordermanagement import process_registered_order

        process_registered_order()

    mock_put.assert_called_once()
    assert mock_put.call_args.kwargs["json"] == {"order_status": "ready"}


def test_process_stock_failure_marks_order_blocked():
    insufficient_resp = MagicMock()
    insufficient_resp.status_code = 400

    with (
        patch("ordermanagement.ordermanagement.requests.get", return_value=_mock_get_response(ORDERS_LIST)),
        patch("ordermanagement.ordermanagement.requests.post", return_value=insufficient_resp),
        patch("ordermanagement.ordermanagement.requests.put", return_value=_mock_put_response()) as mock_put,
        patch("ordermanagement.ordermanagement.random.random", return_value=0.5),
    ):
        from ordermanagement.ordermanagement import process_registered_order

        process_registered_order()

    mock_put.assert_called_once()
    assert mock_put.call_args.kwargs["json"] == {"order_status": "blocked"}


def test_process_no_orders_does_not_call_post_or_put():
    with (
        patch("ordermanagement.ordermanagement.requests.get", return_value=_mock_get_response([])),
        patch("ordermanagement.ordermanagement.requests.post") as mock_post,
        patch("ordermanagement.ordermanagement.requests.put") as mock_put,
    ):
        from ordermanagement.ordermanagement import process_registered_order

        process_registered_order()

    mock_post.assert_not_called()
    mock_put.assert_not_called()


def test_process_error_rate_100_skips_stock_call_and_marks_blocked():
    """ERROR_RATE=1.0 injects error on every cycle.

    The error path raises an exception before decrease_stock() is called,
    so requests.post must NOT be called. The except block then calls
    update_order_status(BLOCKED), so requests.put MUST be called with BLOCKED.
    """
    with (
        patch("ordermanagement.ordermanagement.requests.get", return_value=_mock_get_response(ORDERS_LIST)),
        patch("ordermanagement.ordermanagement.requests.post") as mock_post,
        patch("ordermanagement.ordermanagement.requests.put", return_value=_mock_put_response()) as mock_put,
        patch("ordermanagement.ordermanagement.random.random", return_value=0.0),
        patch.dict("os.environ", {"ERROR_RATE": "1.0"}),
    ):
        from ordermanagement.ordermanagement import process_registered_order

        process_registered_order()

    mock_post.assert_not_called()
    mock_put.assert_called_once()
    assert mock_put.call_args.kwargs["json"] == {"order_status": "blocked"}
