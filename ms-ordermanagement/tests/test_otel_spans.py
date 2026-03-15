"""Tests that ERROR_RATE and real exceptions mark the process_order span as ERROR."""

from unittest.mock import MagicMock, patch

from opentelemetry.trace import StatusCode
from ordermanagement.ordermanagement import process_registered_order


def test_process_order_span_ok_on_success(span_exporter):
    mock_resp = MagicMock()
    mock_resp.json.return_value = [{"id": 1, "wood_type": "oak", "quantity": 5}]
    mock_resp.raise_for_status = MagicMock()
    mock_put = MagicMock()
    mock_put.raise_for_status = MagicMock()
    mock_put.json.return_value = {}

    with (
        patch("ordermanagement.ordermanagement.requests.get", return_value=mock_resp),
        patch("ordermanagement.ordermanagement.requests.post", return_value=MagicMock(status_code=200, json=lambda: {})),
        patch("ordermanagement.ordermanagement.requests.put", return_value=mock_put),
        patch("ordermanagement.ordermanagement.random.random", return_value=0.5),
    ):
        process_registered_order()

    spans = span_exporter.get_finished_spans()
    order_spans = [s for s in spans if s.name == "process order"]
    assert len(order_spans) == 1
    assert order_spans[0].status.status_code == StatusCode.UNSET


def test_process_order_span_error_on_error_rate(span_exporter):
    mock_resp = MagicMock()
    mock_resp.json.return_value = [{"id": 1, "wood_type": "oak", "quantity": 5}]
    mock_resp.raise_for_status = MagicMock()
    mock_put = MagicMock()
    mock_put.raise_for_status = MagicMock()
    mock_put.json.return_value = {}

    with (
        patch("ordermanagement.ordermanagement.requests.get", return_value=mock_resp),
        patch("ordermanagement.ordermanagement.requests.put", return_value=mock_put),
        patch("ordermanagement.ordermanagement.random.random", return_value=0.0),
    ):
        process_registered_order()

    spans = span_exporter.get_finished_spans()
    order_spans = [s for s in spans if s.name == "process order"]
    assert len(order_spans) == 1
    assert order_spans[0].status.status_code == StatusCode.ERROR
    assert any(e.name == "exception" for e in order_spans[0].events)
