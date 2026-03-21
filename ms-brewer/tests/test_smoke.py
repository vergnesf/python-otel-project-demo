"""Smoke tests for brewer service — verify producer initializes and config loads."""

from brewer.brewer_producer import delivery_report, producer
from confluent_kafka import Producer


class _FakeMsg:
    def topic(self):
        return "test-topic"

    def partition(self):
        return 0


def test_producer_is_initialized():
    assert isinstance(producer, Producer)


def test_delivery_report_handles_error():
    delivery_report(Exception("simulated failure"), _FakeMsg())  # must not raise


def test_delivery_report_handles_success():
    delivery_report(None, _FakeMsg())  # must not raise
