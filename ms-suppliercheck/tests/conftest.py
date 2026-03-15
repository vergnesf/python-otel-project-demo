import os

import pytest

# Set up TracerProvider at module level — BEFORE any import that calls trace.get_tracer().
# This avoids the "Overriding of current TracerProvider is not allowed" warning.
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

os.environ.setdefault("ERROR_RATE", "0")

_exporter = InMemorySpanExporter()
_provider = TracerProvider()
_provider.add_span_processor(SimpleSpanProcessor(_exporter))
trace.set_tracer_provider(_provider)


@pytest.fixture()
def span_exporter():
    """Yield the shared InMemorySpanExporter, cleared before each test."""
    _exporter.clear()
    yield _exporter
