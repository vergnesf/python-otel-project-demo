"""Tests that ERROR_RATE and real exceptions mark the process_brew span as ERROR."""

from unittest.mock import MagicMock, patch

from brewmaster.brewmaster import process_registered_brew
from opentelemetry.trace import StatusCode

BREW = {"id": 1, "ingredient_type": "malt", "quantity": 5, "brew_style": "lager"}


def test_process_brew_span_ok_on_success(span_exporter):
    mock_resp = MagicMock()
    mock_resp.json.return_value = [BREW]
    mock_resp.raise_for_status = MagicMock()
    mock_put = MagicMock()
    mock_put.raise_for_status = MagicMock()
    mock_put.json.return_value = {}

    with (
        patch("brewmaster.brewmaster.requests.get", return_value=mock_resp),
        patch("brewmaster.brewmaster.requests.post", return_value=MagicMock(status_code=200, json=lambda: {})),
        patch("brewmaster.brewmaster.requests.put", return_value=mock_put),
        patch("brewmaster.brewmaster.random.random", return_value=0.5),
    ):
        process_registered_brew(0.1)

    spans = span_exporter.get_finished_spans()
    brew_spans = [s for s in spans if s.name == "process brew"]
    assert len(brew_spans) == 1
    assert brew_spans[0].status.status_code == StatusCode.UNSET
    # Verify brew.style attribute is set from the brew dict
    assert brew_spans[0].attributes.get("brew.style") == BREW["brew_style"]


def test_process_brew_span_error_on_error_rate(span_exporter):
    mock_resp = MagicMock()
    mock_resp.json.return_value = [BREW]
    mock_resp.raise_for_status = MagicMock()
    mock_put = MagicMock()
    mock_put.raise_for_status = MagicMock()
    mock_put.json.return_value = {}

    with (
        patch("brewmaster.brewmaster.requests.get", return_value=mock_resp),
        patch("brewmaster.brewmaster.requests.put", return_value=mock_put),
        patch("brewmaster.brewmaster.random.random", return_value=0.0),
    ):
        process_registered_brew(0.1)

    spans = span_exporter.get_finished_spans()
    brew_spans = [s for s in spans if s.name == "process brew"]
    assert len(brew_spans) == 1
    assert brew_spans[0].status.status_code == StatusCode.ERROR
    assert any(e.name == "exception" for e in brew_spans[0].events)
