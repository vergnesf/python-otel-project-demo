"""Smoke tests for fermentation service — verify module imports and URL constants are correct."""

from urllib.parse import urlparse

from fermentation.fermentation_worker import (
    API_URL_BREWS_BREWING,
    API_URL_BREWS_UPDATE,
    HEADERS_JSON,
)


def test_api_url_brews_brewing_endpoint():
    parsed = urlparse(API_URL_BREWS_BREWING)
    assert parsed.scheme in ("http", "https")
    assert parsed.path == "/brews/status/brewing"


def test_api_url_brews_update_endpoint():
    parsed = urlparse(API_URL_BREWS_UPDATE)
    assert parsed.scheme in ("http", "https")
    assert parsed.path == "/brews"


def test_headers_json():
    assert HEADERS_JSON == {"Content-Type": "application/json"}
