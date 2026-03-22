"""Tests for quality-control HTTP forwarding logic with patched requests."""

import json
from unittest.mock import MagicMock, patch

import requests
from quality_control.quality_consumer import API_URL, consume_messages

BREW_READY_PAYLOAD = {"id": 1, "brew_style": "ipa", "brew_status": "ready"}


class _FakeMsg:
    """Minimum confluent_kafka Message interface for consume_messages() tests."""

    def __init__(self, payload: dict):
        self._value = json.dumps(payload).encode("utf-8")

    def value(self):
        return self._value

    def error(self):
        return None

    def headers(self):
        return []

    def offset(self):
        return 0


def _run_one_cycle(mock_response=None, put_side_effect=None, reject_rate=0.0):
    """Drive consume_messages() through exactly one message cycle then exit cleanly."""
    fake_msg = _FakeMsg(BREW_READY_PAYLOAD)
    mock_consumer = MagicMock()
    mock_consumer.poll.side_effect = [fake_msg, KeyboardInterrupt()]

    mock_put = MagicMock()
    if put_side_effect is not None:
        mock_put.side_effect = put_side_effect
    else:
        mock_put.return_value = mock_response

    with (
        patch("quality_control.quality_consumer.consumer", mock_consumer),
        patch("quality_control.quality_consumer.requests.put", mock_put),
        patch("quality_control.quality_consumer.random.random", return_value=0.5),
        patch.dict("os.environ", {"REJECT_RATE": str(reject_rate), "ERROR_RATE": "0"}),
    ):
        consume_messages()

    return mock_put


def test_approved_path_calls_put_with_approved_status():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_put = _run_one_cycle(mock_response=mock_resp, reject_rate=0.0)
    mock_put.assert_called_once()
    assert mock_put.call_args.kwargs["json"]["brew_status"] == "approved"


def test_rejected_path_calls_put_with_rejected_status():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_put = _run_one_cycle(mock_response=mock_resp, reject_rate=1.0)
    mock_put.assert_called_once()
    assert mock_put.call_args.kwargs["json"]["brew_status"] == "rejected"


def test_put_uses_correct_api_url():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_put = _run_one_cycle(mock_response=mock_resp, reject_rate=0.0)
    called_url = mock_put.call_args.args[0]
    assert called_url == f"{API_URL}/{BREW_READY_PAYLOAD['id']}"


def test_timeout_does_not_crash_loop():
    _run_one_cycle(put_side_effect=requests.Timeout())


def test_request_exception_does_not_crash_loop():
    _run_one_cycle(put_side_effect=requests.RequestException("network error"))


def test_non_200_response_does_not_raise():
    mock_resp = MagicMock()
    mock_resp.status_code = 500
    mock_resp.text = "Internal Server Error"
    _run_one_cycle(mock_response=mock_resp)


class _MalformedMsg:
    """Fake Kafka message with invalid JSON payload."""

    def value(self):
        return b"not valid json {"

    def error(self):
        return None

    def headers(self):
        return []

    def offset(self):
        return 0


def test_malformed_json_does_not_crash_loop():
    mock_consumer = MagicMock()
    mock_consumer.poll.side_effect = [_MalformedMsg(), KeyboardInterrupt()]
    mock_put = MagicMock()

    with (
        patch("quality_control.quality_consumer.consumer", mock_consumer),
        patch("quality_control.quality_consumer.requests.put", mock_put),
        patch("quality_control.quality_consumer.random.random", return_value=0.5),
    ):
        consume_messages()

    mock_put.assert_not_called()
