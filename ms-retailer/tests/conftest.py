import os

import pytest
from opentelemetry import metrics, trace
from opentelemetry.propagate import set_global_textmap
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

os.environ.setdefault("ERROR_RATE", "0")

set_global_textmap(TraceContextTextMapPropagator())

_exporter = InMemorySpanExporter()
_provider = TracerProvider()
_provider.add_span_processor(SimpleSpanProcessor(_exporter))
trace.set_tracer_provider(_provider)

_metric_reader = InMemoryMetricReader()
_meter_provider = MeterProvider(metric_readers=[_metric_reader])
metrics.set_meter_provider(_meter_provider)


@pytest.fixture()
def span_exporter():
    _exporter.clear()
    yield _exporter


@pytest.fixture()
def metric_reader():
    # InMemoryMetricReader has no public reset() — counters are cumulative across tests.
    # Always use delta checks (value after - value before) in metric tests, never absolute values.
    yield _metric_reader
