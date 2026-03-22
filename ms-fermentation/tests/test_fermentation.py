"""Tests for ms-fermentation worker — polling loop, span events, and state transitions."""

import time
from unittest.mock import patch

import pytest
import requests
from fermentation.fermentation_worker import _fermentation_start, fetch_brewing_brews, process_brewing_brews
from lib_models.models import BrewStatus
from opentelemetry.trace import StatusCode

BREW = {"id": 1, "brew_style": "ipa", "ingredient_type": "malt", "quantity": 10, "brew_status": "brewing"}


@pytest.fixture(autouse=True)
def clear_state():
    """Reset in-memory fermentation tracking between tests."""
    _fermentation_start.clear()
    yield
    _fermentation_start.clear()


def _get_span(span_exporter):
    spans = span_exporter.get_finished_spans()
    assert spans, "Expected at least one span"
    return spans[0]


# --- First-poll behaviour ---


def test_first_poll_tracks_brew(span_exporter):
    with patch("fermentation.fermentation_worker.fetch_brewing_brews", return_value=[BREW]):
        with patch("fermentation.fermentation_worker.update_brew_status") as mock_update:
            process_brewing_brews(fermentation_seconds=30.0, error_rate=0.0)
    assert 1 in _fermentation_start
    mock_update.assert_not_called()


def test_first_poll_emits_started_event(span_exporter):
    with patch("fermentation.fermentation_worker.fetch_brewing_brews", return_value=[BREW]):
        with patch("fermentation.fermentation_worker.update_brew_status"):
            process_brewing_brews(fermentation_seconds=30.0, error_rate=0.0)
    span = _get_span(span_exporter)
    assert "fermentation.started" in [e.name for e in span.events]


# --- In-progress span attributes ---


def test_in_progress_span_has_brew_attributes(span_exporter):
    with patch("fermentation.fermentation_worker.fetch_brewing_brews", return_value=[BREW]):
        with patch("fermentation.fermentation_worker.update_brew_status"):
            process_brewing_brews(fermentation_seconds=30.0, error_rate=0.0)
    span = _get_span(span_exporter)
    assert span.name == "ferment brew"
    assert span.attributes["brew.style"] == "ipa"
    assert span.attributes["brew.ingredient_type"] == "malt"


def test_in_progress_span_has_progress_pct(span_exporter):
    with patch("fermentation.fermentation_worker.fetch_brewing_brews", return_value=[BREW]):
        with patch("fermentation.fermentation_worker.update_brew_status"):
            process_brewing_brews(fermentation_seconds=30.0, error_rate=0.0)
    span = _get_span(span_exporter)
    assert "fermentation.progress_pct" in span.attributes
    assert 0.0 <= span.attributes["fermentation.progress_pct"] <= 100.0


# --- Fermentation complete ---


def test_complete_brew_transitions_to_ready(span_exporter):
    _fermentation_start[1] = time.monotonic() - 999.0
    with patch("fermentation.fermentation_worker.fetch_brewing_brews", return_value=[BREW]):
        with patch("fermentation.fermentation_worker.update_brew_status") as mock_update:
            process_brewing_brews(fermentation_seconds=30.0, error_rate=0.0)
    mock_update.assert_called_once_with(1, BrewStatus.READY)
    assert 1 not in _fermentation_start


def test_complete_span_has_complete_event_and_full_progress(span_exporter):
    _fermentation_start[1] = time.monotonic() - 999.0
    with patch("fermentation.fermentation_worker.fetch_brewing_brews", return_value=[BREW]):
        with patch("fermentation.fermentation_worker.update_brew_status"):
            process_brewing_brews(fermentation_seconds=30.0, error_rate=0.0)
    span = _get_span(span_exporter)
    assert "fermentation.complete" in [e.name for e in span.events]
    assert span.attributes["fermentation.progress_pct"] == 100.0


# --- Error injection ---


def test_error_rate_on_completion_sets_span_error(span_exporter):
    _fermentation_start[1] = time.monotonic() - 999.0
    with patch("fermentation.fermentation_worker.fetch_brewing_brews", return_value=[BREW]):
        with patch("fermentation.fermentation_worker.update_brew_status"):
            process_brewing_brews(fermentation_seconds=30.0, error_rate=1.0)
    span = _get_span(span_exporter)
    assert span.status.status_code == StatusCode.ERROR
    assert span.attributes.get("error.type") == "RuntimeError"


def test_error_rate_on_completion_keeps_tracking(span_exporter):
    _fermentation_start[1] = time.monotonic() - 999.0
    with patch("fermentation.fermentation_worker.fetch_brewing_brews", return_value=[BREW]):
        with patch("fermentation.fermentation_worker.update_brew_status"):
            process_brewing_brews(fermentation_seconds=30.0, error_rate=1.0)
    # Brew remains tracked so it will be retried on next poll
    assert 1 in _fermentation_start


# --- No brews ---


def test_empty_brews_does_nothing(span_exporter):
    with patch("fermentation.fermentation_worker.fetch_brewing_brews", return_value=[]):
        with patch("fermentation.fermentation_worker.update_brew_status") as mock_update:
            process_brewing_brews(fermentation_seconds=30.0, error_rate=0.0)
    mock_update.assert_not_called()
    assert len(span_exporter.get_finished_spans()) == 0


# --- Stale state cleanup (L1) ---


def test_stale_brew_removed_when_no_longer_brewing(span_exporter):
    # Brew 1 was tracked but is no longer in BREWING status (e.g., moved to BLOCKED)
    _fermentation_start[1] = time.monotonic() - 10.0
    with patch("fermentation.fermentation_worker.fetch_brewing_brews", return_value=[]):
        with patch("fermentation.fermentation_worker.update_brew_status"):
            process_brewing_brews(fermentation_seconds=30.0, error_rate=0.0)
    assert 1 not in _fermentation_start


def test_only_stale_brew_removed_active_brew_kept(span_exporter):
    _fermentation_start[1] = time.monotonic() - 10.0  # stale — not in current BREWING list
    with patch("fermentation.fermentation_worker.fetch_brewing_brews", return_value=[BREW]):
        with patch("fermentation.fermentation_worker.update_brew_status"):
            process_brewing_brews(fermentation_seconds=30.0, error_rate=0.0)
    # BREW (id=1) is in current list, so it should NOT be removed
    assert 1 in _fermentation_start


# --- Fetch error tracing (L3) ---


def test_fetch_failure_creates_error_span(span_exporter):
    with patch("fermentation.fermentation_worker.requests.get", side_effect=requests.ConnectionError("broker down")):
        fetch_brewing_brews()
    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == "fetch brewing brews"
    assert spans[0].status.status_code == StatusCode.ERROR
    assert spans[0].attributes.get("error.type") == "ConnectionError"


def test_fetch_failure_returns_empty_list(span_exporter):
    with patch("fermentation.fermentation_worker.requests.get", side_effect=requests.ConnectionError("broker down")):
        result = fetch_brewing_brews()
    assert result == []
