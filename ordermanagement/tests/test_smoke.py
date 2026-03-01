"""Smoke tests for ordermanagement service — verify module imports and URL constants are correct."""

# The package and module share the same name (ordermanagement.ordermanagement) — this is
# a design choice in the original service structure, not a typo.
#
# Scope limitation: INTERVAL_SECONDS validity, ERROR_RATE range, and the worker loop behaviour
# cannot be verified without running Order and Stock APIs. These tests confirm the module
# loads correctly and the URL constants are well-formed, not that the service is fully configured.

from urllib.parse import urlparse

from ordermanagement.ordermanagement import (
    API_URL_ORDERS_REGISTERED,
    API_URL_ORDERS_UPDATE,
    API_URL_STOCKS_DECREASE,
    HEADERS_JSON,
)


def test_api_url_registered_endpoint():
    parsed = urlparse(API_URL_ORDERS_REGISTERED)
    assert parsed.scheme in ("http", "https")
    assert parsed.path == "/orders/status/registered"  # exact path — base host comes from API_URL_ORDERS env var


def test_api_url_orders_update_endpoint():
    parsed = urlparse(API_URL_ORDERS_UPDATE)
    assert parsed.scheme in ("http", "https")
    assert parsed.path == "/orders"  # exact path — base host comes from API_URL_ORDERS env var


def test_api_url_stocks_decrease_endpoint():
    parsed = urlparse(API_URL_STOCKS_DECREASE)
    assert parsed.scheme in ("http", "https")
    assert parsed.path == "/stocks/decrease"  # exact path — base host comes from API_URL_STOCKS env var


def test_headers_json():
    assert HEADERS_JSON == {"Content-Type": "application/json"}
