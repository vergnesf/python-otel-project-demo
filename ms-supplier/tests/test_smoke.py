"""Smoke tests for supplier service — verify producer initializes and config loads."""

from confluent_kafka import Producer
from supplier.supplier_producer import delivery_report, producer


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
