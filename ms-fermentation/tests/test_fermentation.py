"""Tests for ms-fermentation worker — polling loop, span events, and state transitions."""

import time
from unittest.mock import patch

import pytest
from fermentation.fermentation_worker import _fermentation_start, process_brewing_brews
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
