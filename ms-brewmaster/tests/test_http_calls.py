"""Tests for brewmaster HTTP logic with patched requests.

All three HTTP functions (fetch_registered_brews, consume_ingredients, update_brew_status)
and the orchestrator (process_registered_brew) are tested directly — no loop to drive.

requests.get / .post / .put are patched at module level.
random.random is patched to 0.5 when testing happy paths so ERROR_RATE (default 0.1)
never triggers. For error-injection tests, random.random is forced to 0.0 (< any rate).
"""

from unittest.mock import MagicMock, patch

import pytest
import requests
from lib_models.models import BrewStatus

BREW = {"id": 1, "ingredient_type": "malt", "quantity": 5, "brew_style": "lager"}
BREWS_LIST = [BREW]


# ---------------------------------------------------------------------------
# fetch_registered_brews
# ---------------------------------------------------------------------------


def test_fetch_brews_returns_list_on_success():
    mock_resp = MagicMock()
    mock_resp.json.return_value = BREWS_LIST
    with patch("brewmaster.brewmaster.requests.get", return_value=mock_resp) as mock_get:
        mock_resp.raise_for_status = MagicMock()
        from brewmaster.brewmaster import fetch_registered_brews

        result = fetch_registered_brews()

    mock_get.assert_called_once()
    called_url = mock_get.call_args.args[0]
    assert called_url.endswith("/brews/status/registered")
    assert result == BREWS_LIST


def test_fetch_brews_returns_empty_list_on_request_exception():
    with patch("brewmaster.brewmaster.requests.get", side_effect=requests.RequestException("down")):
        from brewmaster.brewmaster import fetch_registered_brews

        result = fetch_registered_brews()

    assert result == []


# ---------------------------------------------------------------------------
# consume_ingredients
# ---------------------------------------------------------------------------


def test_consume_ingredients_calls_post_with_correct_payload():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {}
    mock_resp.raise_for_status = MagicMock()
    with patch("brewmaster.brewmaster.requests.post", return_value=mock_resp) as mock_post:
        from brewmaster.brewmaster import consume_ingredients

        consume_ingredients(BREW)

    mock_post.assert_called_once()
    payload = mock_post.call_args.kwargs["json"]
    assert payload["ingredient_type"] == BREW["ingredient_type"]
    assert payload["quantity"] == BREW["quantity"]


def test_consume_ingredients_raises_on_400():
    mock_resp = MagicMock()
    mock_resp.status_code = 400
    with patch("brewmaster.brewmaster.requests.post", return_value=mock_resp):
        from brewmaster.brewmaster import consume_ingredients

        with pytest.raises(Exception, match="Insufficient"):
            consume_ingredients(BREW)


def test_consume_ingredients_raises_on_404():
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    with patch("brewmaster.brewmaster.requests.post", return_value=mock_resp):
        from brewmaster.brewmaster import consume_ingredients

        with pytest.raises(Exception, match="Ingredient not found"):
            consume_ingredients(BREW)


# ---------------------------------------------------------------------------
# update_brew_status
# ---------------------------------------------------------------------------


def test_update_brew_status_calls_put_with_correct_payload():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {}
    mock_resp.raise_for_status = MagicMock()
    with patch("brewmaster.brewmaster.requests.put", return_value=mock_resp) as mock_put:
        from brewmaster.brewmaster import update_brew_status

        update_brew_status(1, BrewStatus.READY)

    mock_put.assert_called_once()
    assert mock_put.call_args.kwargs["json"] == {"brew_status": "ready"}


def test_update_brew_status_raises_on_request_exception():
    with patch("brewmaster.brewmaster.requests.put", side_effect=requests.RequestException("timeout")):
        from brewmaster.brewmaster import update_brew_status

        with pytest.raises(requests.RequestException):
            update_brew_status(1, BrewStatus.READY)


# ---------------------------------------------------------------------------
# process_registered_brew
# ---------------------------------------------------------------------------


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


def test_process_happy_path_updates_status_to_ready():
    with (
        patch("brewmaster.brewmaster.requests.get", return_value=_mock_get_response(BREWS_LIST)),
        patch("brewmaster.brewmaster.requests.post", return_value=_mock_post_response(200)),
        patch("brewmaster.brewmaster.requests.put", return_value=_mock_put_response()) as mock_put,
        patch("brewmaster.brewmaster.random.random", return_value=0.5),
    ):
        from brewmaster.brewmaster import process_registered_brew

        process_registered_brew(0.1)

    mock_put.assert_called_once()
    assert mock_put.call_args.kwargs["json"] == {"brew_status": "ready"}


def test_process_insufficient_ingredients_marks_brew_blocked():
    insufficient_resp = MagicMock()
    insufficient_resp.status_code = 400

    with (
        patch("brewmaster.brewmaster.requests.get", return_value=_mock_get_response(BREWS_LIST)),
        patch("brewmaster.brewmaster.requests.post", return_value=insufficient_resp),
        patch("brewmaster.brewmaster.requests.put", return_value=_mock_put_response()) as mock_put,
        patch("brewmaster.brewmaster.random.random", return_value=0.5),
    ):
        from brewmaster.brewmaster import process_registered_brew

        process_registered_brew(0.1)

    mock_put.assert_called_once()
    assert mock_put.call_args.kwargs["json"] == {"brew_status": "blocked"}


def test_process_no_brews_does_not_call_post_or_put():
    with (
        patch("brewmaster.brewmaster.requests.get", return_value=_mock_get_response([])),
        patch("brewmaster.brewmaster.requests.post") as mock_post,
        patch("brewmaster.brewmaster.requests.put") as mock_put,
    ):
        from brewmaster.brewmaster import process_registered_brew

        process_registered_brew(0.1)

    mock_post.assert_not_called()
    mock_put.assert_not_called()


def test_process_error_rate_100_skips_consume_and_marks_blocked():
    """ERROR_RATE=1.0 injects error on every cycle.

    The error path raises an exception before consume_ingredients() is called,
    so requests.post must NOT be called. The except block then calls
    update_brew_status(BLOCKED), so requests.put MUST be called with BLOCKED.
    """
    with (
        patch("brewmaster.brewmaster.requests.get", return_value=_mock_get_response(BREWS_LIST)),
        patch("brewmaster.brewmaster.requests.post") as mock_post,
        patch("brewmaster.brewmaster.requests.put", return_value=_mock_put_response()) as mock_put,
        patch("brewmaster.brewmaster.random.random", return_value=0.0),
    ):
        from brewmaster.brewmaster import process_registered_brew

        process_registered_brew(1.0)

    mock_post.assert_not_called()
    mock_put.assert_called_once()
    assert mock_put.call_args.kwargs["json"] == {"brew_status": "blocked"}
