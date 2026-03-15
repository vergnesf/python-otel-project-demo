"""Tests for ordercheck HTTP forwarding logic with patched requests.

Drive strategy: consumer.poll() side_effect chain drives consume_messages():
  - Call 1: return a fake Kafka message (valid payload)
  - Call 2: raise KeyboardInterrupt → exits consume_messages() cleanly via except block

random.random is forced to 0.5 so ERROR_RATE injection (default 0.1) never triggers,
ensuring the HTTP call block is always reached in happy-path tests.
"""

import json
from unittest.mock import MagicMock, patch

import requests

ORDER_PAYLOAD = {"wood_type": "oak", "quantity": 5}


class _FakeMsg:
    """Minimum confluent_kafka Message interface for consume_messages() tests."""

    def __init__(self, payload: dict):
        self._value = json.dumps(payload).encode("utf-8")

    def value(self):
        return self._value

    def error(self):
        return None


def _run_one_cycle(mock_response=None, post_side_effect=None):
    """Drive consume_messages() through exactly one message cycle then exit cleanly.

    consumer.poll returns a real message on call 1, then KeyboardInterrupt on call 2.
    KeyboardInterrupt is caught by consume_messages() and triggers clean shutdown.
    Returns the mock requests.post for assertion.
    """
    fake_msg = _FakeMsg(ORDER_PAYLOAD)
    mock_consumer = MagicMock()
    mock_consumer.poll.side_effect = [fake_msg, KeyboardInterrupt()]

    mock_post = MagicMock()
    if post_side_effect is not None:
        mock_post.side_effect = post_side_effect
    else:
        mock_post.return_value = mock_response

    with (
        patch("ordercheck.ordercheck_consumer.consumer", mock_consumer),
        patch("ordercheck.ordercheck_consumer.requests.post", mock_post),
        patch("ordercheck.ordercheck_consumer.random.random", return_value=0.5),
    ):
        from ordercheck.ordercheck_consumer import consume_messages

        consume_messages()

    return mock_post


def test_happy_path_calls_post_with_correct_payload():
    mock_resp = MagicMock()
    mock_resp.status_code = 201
    mock_post = _run_one_cycle(mock_response=mock_resp)
    mock_post.assert_called_once()
    assert mock_post.call_args.kwargs["json"] == ORDER_PAYLOAD


def test_happy_path_uses_correct_api_url():
    mock_resp = MagicMock()
    mock_resp.status_code = 201
    mock_post = _run_one_cycle(mock_response=mock_resp)
    called_url = mock_post.call_args.args[0]
    assert called_url.endswith("/orders")


def test_non_201_response_does_not_raise():
    mock_resp = MagicMock()
    mock_resp.status_code = 500
    mock_resp.text = "Internal Server Error"
    # Must not raise — the loop should continue and exit on KeyboardInterrupt
    _run_one_cycle(mock_response=mock_resp)


def test_timeout_does_not_crash_loop():
    # requests.Timeout must be caught — loop continues to the next poll() call
    _run_one_cycle(post_side_effect=requests.Timeout())


def test_request_exception_does_not_crash_loop():
    _run_one_cycle(post_side_effect=requests.RequestException("network error"))
