"""Smoke tests for brewmaster service — verify module imports and URL constants are correct."""

from urllib.parse import urlparse

from brewmaster.brewmaster import (
    API_URL_BREWS_REGISTERED,
    API_URL_BREWS_UPDATE,
    API_URL_CELLAR_CONSUME,
    HEADERS_JSON,
)


def test_api_url_brews_registered_endpoint():
    parsed = urlparse(API_URL_BREWS_REGISTERED)
    assert parsed.scheme in ("http", "https")
    assert parsed.path == "/brews/status/registered"


def test_api_url_brews_update_endpoint():
    parsed = urlparse(API_URL_BREWS_UPDATE)
    assert parsed.scheme in ("http", "https")
    assert parsed.path == "/brews"


def test_api_url_cellar_consume_endpoint():
    parsed = urlparse(API_URL_CELLAR_CONSUME)
    assert parsed.scheme in ("http", "https")
    assert parsed.path == "/ingredients/decrease"


def test_headers_json():
    assert HEADERS_JSON == {"Content-Type": "application/json"}
