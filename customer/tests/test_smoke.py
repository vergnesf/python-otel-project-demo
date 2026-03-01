"""Smoke tests for customer service — verify producer initializes and config loads."""

from confluent_kafka import Producer
from customer.customer_producer import delivery_report, producer

# All imports are at module level: a collection-time ImportError is more diagnostic
# than a runtime ImportError buried inside a test function.
# _FakeMsg provides the minimum confluent_kafka Message interface (topic, partition)
# needed by delivery_report. The stub values are not asserted — the tests only verify
# that delivery_report does not raise on either code path.
# Note: _FakeMsg is intentionally duplicated across both producer service test files — both services
# share the same confluent_kafka Producer interface; there is no shared test infrastructure.


class _FakeMsg:
    def topic(self):
        return "test-topic"  # arbitrary stub value

    def partition(self):
        return 0  # arbitrary stub — not a real partition assertion


def test_producer_is_initialized():
    assert isinstance(producer, Producer)


def test_delivery_report_handles_error():
    delivery_report(Exception("simulated failure"), _FakeMsg())  # must not raise


def test_delivery_report_handles_success():
    delivery_report(None, _FakeMsg())  # must not raise
