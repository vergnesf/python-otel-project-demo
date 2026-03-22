"""conftest.py for fermentation/tests."""

import os

import pytest

# Set up TracerProvider and MeterProvider at module level — BEFORE any import that calls
# trace.get_tracer() or metrics.get_meter(). This avoids provider override warnings.
from opentelemetry import metrics, trace
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

os.environ.setdefault("ERROR_RATE", "0")

_exporter = InMemorySpanExporter()
_provider = TracerProvider()
_provider.add_span_processor(SimpleSpanProcessor(_exporter))
trace.set_tracer_provider(_provider)

_metric_reader = InMemoryMetricReader()
_meter_provider = MeterProvider(metric_readers=[_metric_reader])
metrics.set_meter_provider(_meter_provider)


@pytest.fixture()
def span_exporter():
    """Yield the shared InMemorySpanExporter, cleared before each test."""
    _exporter.clear()
    yield _exporter
