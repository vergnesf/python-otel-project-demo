"""Tests for UNKNOWN_TOPIC_OR_PART retry behaviour in brewcheck consumer.

When Kafka reports UNKNOWN_TOPIC_OR_PART, consume_messages() must log a warning,
sleep briefly, and continue polling instead of raising KafkaException and crashing.
"""

from unittest.mock import MagicMock, patch

import pytest
from brewcheck.brewcheck_consumer import consume_messages
from confluent_kafka import KafkaError


class _FakeKafkaError:
    """Minimal KafkaError interface."""

    def __init__(self, code):
        self._code = code

    def code(self):
        return self._code

    def __bool__(self):
        return True


class _FakeErrMsg:
    """Fake Kafka message carrying an error."""

    def __init__(self, error_code):
        self._error = _FakeKafkaError(error_code)

    def error(self):
        return self._error


def test_unknown_topic_does_not_crash_loop():
    """UNKNOWN_TOPIC_OR_PART must not raise — loop retries after sleep."""
    unknown_topic_msg = _FakeErrMsg(KafkaError.UNKNOWN_TOPIC_OR_PART)
    mock_consumer = MagicMock()
    mock_consumer.poll.side_effect = [unknown_topic_msg, KeyboardInterrupt()]

    with (
        patch("brewcheck.brewcheck_consumer.consumer", mock_consumer),
        patch("brewcheck.brewcheck_consumer.time.sleep") as mock_sleep,
    ):
        consume_messages()

    mock_sleep.assert_called_once_with(5)


def test_unknown_topic_logs_warning():
    """A warning must be logged when UNKNOWN_TOPIC_OR_PART is received."""
    unknown_topic_msg = _FakeErrMsg(KafkaError.UNKNOWN_TOPIC_OR_PART)
    mock_consumer = MagicMock()
    mock_consumer.poll.side_effect = [unknown_topic_msg, KeyboardInterrupt()]

    with (
        patch("brewcheck.brewcheck_consumer.consumer", mock_consumer),
        patch("brewcheck.brewcheck_consumer.time.sleep"),
        patch("brewcheck.brewcheck_consumer.logger") as mock_logger,
    ):
        consume_messages()

    mock_logger.warning.assert_called_once()
    assert "retry" in mock_logger.warning.call_args.args[0].lower()


def test_other_kafka_error_still_raises():
    """Non-UNKNOWN_TOPIC errors must still raise KafkaException."""
    from confluent_kafka import KafkaException

    other_err_msg = _FakeErrMsg(KafkaError.BROKER_NOT_AVAILABLE)
    mock_consumer = MagicMock()
    mock_consumer.poll.side_effect = [other_err_msg]

    with (
        patch("brewcheck.brewcheck_consumer.consumer", mock_consumer),
        patch("brewcheck.brewcheck_consumer.time.sleep"),
        pytest.raises(KafkaException),
    ):
        consume_messages()
