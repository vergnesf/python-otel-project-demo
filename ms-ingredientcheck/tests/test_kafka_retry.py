"""Tests for UNKNOWN_TOPIC_OR_PART retry behaviour in ingredientcheck consumer."""

from unittest.mock import MagicMock, patch

import pytest
from confluent_kafka import KafkaError
from ingredientcheck.ingredientcheck_consumer import consume_messages


class _FakeKafkaError:
    def __init__(self, code):
        self._code = code

    def code(self):
        return self._code

    def __bool__(self):
        return True


class _FakeErrMsg:
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
        patch("ingredientcheck.ingredientcheck_consumer.consumer", mock_consumer),
        patch("ingredientcheck.ingredientcheck_consumer.time.sleep") as mock_sleep,
    ):
        consume_messages()

    mock_sleep.assert_called_once_with(5)


def test_unknown_topic_logs_warning():
    unknown_topic_msg = _FakeErrMsg(KafkaError.UNKNOWN_TOPIC_OR_PART)
    mock_consumer = MagicMock()
    mock_consumer.poll.side_effect = [unknown_topic_msg, KeyboardInterrupt()]

    with (
        patch("ingredientcheck.ingredientcheck_consumer.consumer", mock_consumer),
        patch("ingredientcheck.ingredientcheck_consumer.time.sleep"),
        patch("ingredientcheck.ingredientcheck_consumer.logger") as mock_logger,
    ):
        consume_messages()

    mock_logger.warning.assert_called_once()
    assert "retry" in mock_logger.warning.call_args.args[0].lower()


def test_other_kafka_error_still_raises():
    from confluent_kafka import KafkaException

    other_err_msg = _FakeErrMsg(KafkaError.BROKER_NOT_AVAILABLE)
    mock_consumer = MagicMock()
    mock_consumer.poll.side_effect = [other_err_msg]

    with (
        patch("ingredientcheck.ingredientcheck_consumer.consumer", mock_consumer),
        patch("ingredientcheck.ingredientcheck_consumer.time.sleep"),
        pytest.raises(KafkaException),
    ):
        consume_messages()
