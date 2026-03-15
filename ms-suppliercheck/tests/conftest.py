import os

import pytest

# Set up TracerProvider at module level — BEFORE any import that calls trace.get_tracer().
# This avoids the "Overriding of current TracerProvider is not allowed" warning.
from opentelemetry import trace
from opentelemetry.propagate import set_global_textmap
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

os.environ.setdefault("ERROR_RATE", "0")

# Register W3C propagator so inject/extract work in tests (not set up by opentelemetry-instrument in unit tests)
set_global_textmap(TraceContextTextMapPropagator())

_exporter = InMemorySpanExporter()
_provider = TracerProvider()
_provider.add_span_processor(SimpleSpanProcessor(_exporter))
trace.set_tracer_provider(_provider)


@pytest.fixture()
def span_exporter():
    """Yield the shared InMemorySpanExporter, cleared before each test."""
    _exporter.clear()
    yield _exporter
