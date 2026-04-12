# Story 5.1: ms-dispatch — Beer Order Dispatch Consumer

Status: review

## Story

As a brewery system operator,
I want a Kafka consumer that processes retail beer orders from the `beer-orders` topic and calls `ms-beerstock` to ship them,
so that the full brewery lifecycle trace is observable end-to-end in Tempo (retailer → dispatch → beerstock).

## Acceptance Criteria

1. Consumes the `beer-orders` Kafka topic (consumer group: `dispatch-group`) and calls `POST /beerstock/ship` on `ms-beerstock` for each message.
2. On HTTP 200 from `/beerstock/ship`: logs "shipment confirmed", increments `beer_orders.dispatched` metric, sets span attribute `dispatch.status = "shipped"`.
3. On HTTP 400 from `/beerstock/ship` (insufficient stock): logs "backorder", increments `beer_orders.backorder` metric, sets span attribute `dispatch.status = "backorder"`. Does NOT crash or raise.
4. On any other HTTP error or exception: logs error, increments `beer_orders.dispatch_errors` metric, sets span status to ERROR.
5. Span `"process beer-orders"` with `SpanKind.CONSUMER`, W3C span link to the upstream retailer span, and attributes: `retailer.name`, `dispatch.status`, plus standard `messaging.*` semconv attributes.
6. `OTEL_SERVICE_NAME=dispatch` configured in Docker.
7. `uv run pytest` passes (smoke tests: consumer initialized, API URL correct, consume_messages callable).
8. `task test-lint` and `task test-unit` pass (service added to `KEEPER_SERVICES`).
9. `task typecheck` passes (pyright clean).
10. `ms-dispatch` added to `PROJECTS` in `Taskfile.yml`.
11. Service added to `docker-compose-apps.yml` with all required env vars.

## Tasks / Subtasks

- [x] Create `ms-dispatch/` directory structure (AC: 1, 7, 8, 9, 10, 11)
  - [x] `ms-dispatch/dispatch/__init__.py` (empty)
  - [x] `ms-dispatch/dispatch/dispatch_consumer.py` (main module)
  - [x] `ms-dispatch/tests/__init__.py` (empty)
  - [x] `ms-dispatch/tests/conftest.py` (empty or minimal)
  - [x] `ms-dispatch/tests/test_smoke.py`
  - [x] `ms-dispatch/pyproject.toml`
  - [x] `ms-dispatch/Dockerfile`
  - [x] `ms-dispatch/README.md`
  - [x] `ms-dispatch/CLAUDE.md`
- [x] Implement `dispatch_consumer.py` (AC: 1, 2, 3, 4, 5)
  - [x] Module-level: logger, tracer, meter, consumer, `_kafka_server_address`, `API_URL_BEERSTOCK`
  - [x] `_process_message(msg, error_rate)`: extract W3C context → span link → span `"process beer-orders"` → parse BeerOrder → call `/beerstock/ship` → handle 200/400/other
  - [x] `running = True` + `_shutdown` at module level (not inside function)
  - [x] `consume_messages()` with `consumer.subscribe(["beer-orders"])`, `while running:`, `consumer.poll(1.0)`, KafkaError handling
  - [x] `if __name__ == "__main__":` guard: fail-fast on missing `KAFKA_BOOTSTRAP_SERVERS`, signal handlers, call `consume_messages()`
  - [x] ERROR_RATE: ValueError-safe parsing + clamp [0.0, 1.0]
- [x] Add `ms-dispatch` to `Taskfile.yml` `KEEPER_SERVICES` and `PROJECTS` (AC: 8, 10)
- [x] Add service to `docker-compose/docker-compose-apps.yml` (AC: 6, 11)

## Dev Notes

### Critical: Signal Handler Scope

All existing consumers (`ms-brewcheck`, `ms-ingredientcheck`, `ms-quality-control`) define `running` and `_shutdown` at **module level** (directly inside `if __name__ == "__main__":`, which does NOT create a new Python scope). This means `global running` inside `_shutdown` correctly references the module global. Do NOT nest `_shutdown` inside a `def main()` function — this would require `nonlocal` instead of `global`. Follow the existing pattern exactly.

```python
running = True

def _shutdown(signum, frame):
    global running
    logger.info("Received signal %s, shutting down", signum)
    running = False

def consume_messages():
    consumer.subscribe(["beer-orders"])
    ...
    while running:
        ...

if __name__ == "__main__":
    if not os.environ.get("KAFKA_BOOTSTRAP_SERVERS"):
        logger.error("KAFKA_BOOTSTRAP_SERVERS is not set — cannot connect to Kafka. Exiting.")
        sys.exit(1)
    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)
    logger.info("Dispatch service starting")
    consume_messages()
```

### Message Format (from ms-retailer producer)

`beer-orders` topic messages are JSON-serialized `BeerOrder` Pydantic models:
```json
{"brew_style": "lager", "quantity": 5, "retailer_name": "Bar du Port"}
```
W3C trace context is injected in Kafka **headers** (not payload) by ms-retailer via `opentelemetry.propagate.inject(headers)`.

### ms-beerstock Ship Endpoint

- URL: `POST http://ms-beerstock:5002/beerstock/ship`
- Body: `{"brew_style": "lager", "quantity": 5}` — `brew_style` is a plain string, `quantity` is int > 0
- 200: success, returns updated stock object
- 400: insufficient stock OR brew_style not found → log as "backorder", do NOT raise
- Other status codes → treat as error

[Source: ms-beerstock/CLAUDE.md, ms-beerstock/beerstock/schemas.py, ms-beerstock/beerstock/routes/beerstock.py:183]

### OTEL Span Pattern

Follow `ms-quality-control` exactly for the W3C span link extraction pattern:

```python
from opentelemetry.propagate import extract
from opentelemetry.trace import SpanKind, StatusCode

raw_headers = msg.headers() or []
carrier = {k: v.decode() if isinstance(v, bytes) else v for k, v in raw_headers}
remote_ctx = extract(carrier)
remote_span_ctx = trace.get_current_span(remote_ctx).get_span_context()
links = [trace.Link(remote_span_ctx)] if remote_span_ctx.is_valid else []

with tracer.start_as_current_span("process beer-orders", links=links, kind=SpanKind.CONSUMER) as span:
    span.set_attribute("messaging.system", "kafka")
    span.set_attribute("messaging.operation.name", "process")
    span.set_attribute("messaging.operation.type", "process")
    span.set_attribute("messaging.destination.name", "beer-orders")
    span.set_attribute("messaging.consumer.group.name", "dispatch-group")
    span.set_attribute("server.address", _kafka_server_address)
    span.set_attribute("messaging.kafka.message.offset", msg.offset())
    # business attributes
    span.set_attribute("retailer.name", beer_order.retailer_name)
    span.set_attribute("dispatch.status", "shipped" | "backorder")
```

[Source: ms-brewcheck/brewcheck/brewcheck_consumer.py:42-97, ms-quality-control/quality_control/quality_consumer.py:46-119]

### Metrics

```python
beer_orders_dispatched = meter.create_counter("beer_orders.dispatched", description="Beer orders successfully shipped")
beer_orders_backorder  = meter.create_counter("beer_orders.backorder",   description="Beer orders in backorder (insufficient stock)")
beer_orders_errors     = meter.create_counter("beer_orders.dispatch_errors", description="Beer orders with processing errors")
```

### Kafka Consumer Init Pattern

```python
_kafka_bootstrap = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
_kafka_server_address = _kafka_bootstrap.split(",")[0].split(":")[0]
consumer = Consumer({
    "bootstrap.servers": _kafka_bootstrap,
    "group.id": "dispatch-group",
    "auto.offset.reset": "earliest",
})
API_URL_BEERSTOCK = os.environ.get("API_URL_BEERSTOCK", "http://ms-beerstock:5002") + "/beerstock/ship"
```

[Source: ms-brewcheck/brewcheck/brewcheck_consumer.py:29-39, ms-quality-control/quality_control/quality_consumer.py:31-39]

### pyproject.toml (copy from ms-ingredientcheck, adjust)

```toml
[project]
name = "dispatch"
version = "0.1.0"
requires-python = ">=3.14"
dependencies = [
    "confluent-kafka>=2.13.2",
    "lib-models",
    "opentelemetry-distro>=0.61b0",
    "opentelemetry-exporter-otlp>=1.40.0",
    "requests>=2.32.5",
]

[dependency-groups]
dev = ["ruff", "pyright", "pytest>=8"]

[tool.uv.sources]
lib-models = { path = "../lib-models", editable = true }

[tool.pyright]
venv = ".venv"
venvPath = "."
pythonVersion = "3.14"
typeCheckingMode = "basic"
extraPaths = ["../lib-models"]
exclude = ["**/.venv", "**/__pycache__"]
```

Note: `pydantic` is NOT needed — use `json.loads()` + dict access to parse the message (same as ms-brewcheck), or use `BeerOrder(**json.loads(...))` if importing from lib-models. The `lib-models` dep covers pydantic transitively.

### Dockerfile Pattern (copy from ms-brewcheck Dockerfile exactly)

The Dockerfile is built with `context: ..` (repo root), so COPY paths are relative to the repo root:

```dockerfile
ARG DOCKER_REGISTRY
ARG IMG_PYTHON

FROM ${DOCKER_REGISTRY}${IMG_PYTHON}

RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

ENV PYTHON_JIT=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN groupadd -r appuser && useradd -r -g appuser appuser -m

COPY ms-dispatch/pyproject.toml /app/ms-dispatch/
COPY lib-models /app/lib-models/

WORKDIR /app/ms-dispatch

RUN pip install --no-cache-dir uv && \
    uv run --no-dev python -m ensurepip && \
    uv run --no-dev opentelemetry-bootstrap -a install

COPY ms-dispatch/dispatch /app/ms-dispatch/dispatch/

RUN chown -R appuser:appuser /app

USER appuser

CMD ["uv", "run", "--no-dev", "opentelemetry-instrument", "python", "dispatch/dispatch_consumer.py"]
```

[Source: ms-brewcheck/Dockerfile]

### Taskfile.yml Changes

Two lines to update:
1. `PROJECTS:` — append `ms-dispatch`
2. `KEEPER_SERVICES:` — append `ms-dispatch`

Do NOT add to `HEALTHCHECK_SERVICES` — no HEALTHCHECK instruction in docker-compose for this service.

[Source: Taskfile.yml:13-21]

### docker-compose-apps.yml

Exact format to use (modeled on `ms-quality-control` block):

```yaml
  ms-dispatch:
    build:
      context: ..
      dockerfile: ms-dispatch/Dockerfile
      args:
        DOCKER_REGISTRY: ${DOCKER_REGISTRY:-}
        IMG_PYTHON: ${IMG_PYTHON_BASE}
    container_name: ms-dispatch
    environment:
      <<: *common-apps-env
      OTEL_SERVICE_NAME: ms-dispatch
      KAFKA_BOOTSTRAP_SERVERS: broker:29092
      API_URL_BEERSTOCK: http://ms-beerstock:5002
    depends_on:
      ms-beerstock:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - otel-network
```

Key points:
- `<<: *common-apps-env` merges the common OTEL env vars (OTLP endpoint, exporters, ERROR_RATE, LOG_LEVEL) — do NOT redeclare them
- `KAFKA_BOOTSTRAP_SERVERS: broker:29092` (not `kafka:9092`) — this is the internal broker hostname
- `ms-beerstock` has a healthcheck defined → `condition: service_healthy` is valid
- `API_URL_BEERSTOCK` is used instead of `API_URL` to avoid ambiguity (ms-dispatch calls beerstock, not brewery)

[Source: docker-compose/docker-compose-apps.yml — ms-quality-control block]

### Smoke Test Pattern (from ms-brewcheck)

```python
from dispatch.dispatch_consumer import API_URL_BEERSTOCK, consume_messages, consumer
from confluent_kafka import Consumer

def test_consumer_is_initialized():
    assert isinstance(consumer, Consumer)

def test_api_url_has_beerstock_path():
    assert "/beerstock/ship" in API_URL_BEERSTOCK

def test_consume_messages_is_callable():
    assert callable(consume_messages)
```

[Source: ms-brewcheck/tests/test_smoke.py]

### Pre-PR Checklist

Run from repo root before opening PR:
```bash
task test        # test-lint (ruff) + test-unit (pytest) — must pass
task typecheck   # pyright on all KEEPER services — must pass
```

Also verify:
- `CLAUDE.md` KEEPER Services table updated to include `ms-dispatch`
- `docs/architecture.md` services table updated
- `README.md` Project Structure section updated
- `ms-dispatch/README.md` exists

### Project Structure Notes

- New service directory: `ms-dispatch/` at repo root (same level as `ms-brewcheck/`, `ms-quality-control/`)
- Python package: `dispatch/` (lowercase, no hyphen)
- Entry module: `dispatch/dispatch_consumer.py`
- Consumer group: `dispatch-group` (follows `{service-name}-group` convention)

### References

- [Source: ms-brewcheck/brewcheck/brewcheck_consumer.py] — base consumer pattern
- [Source: ms-quality-control/quality_control/quality_consumer.py] — REJECT_RATE + dual-outcome pattern
- [Source: ms-retailer/retailer/retailer_producer.py] — message format + W3C inject
- [Source: ms-beerstock/CLAUDE.md] — ship endpoint spec
- [Source: ms-beerstock/beerstock/schemas.py] — BeerStockShip schema
- [Source: ms-ingredientcheck/pyproject.toml] — pyproject.toml template
- [Source: lib-models/lib_models/models.py] — BeerOrder, BeerStyle, InsufficientBeerStockError
- [Source: Taskfile.yml:11-26] — KEEPER_SERVICES, PROJECTS, HEALTHCHECK_SERVICES

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

- Implemented `ms-dispatch` Kafka consumer following ms-brewcheck/ms-quality-control patterns exactly.
- W3C span link pattern from ms-quality-control used verbatim for cross-pipeline traceability.
- `running`/`_shutdown` at module level (not inside a function) — `global running` is correct here.
- Smoke tests: 3 passed. test-lint: all clean. test-unit: 189 tests (12 services) passed. typecheck: all green.
- CLAUDE.md, docs/architecture.md, README.md updated with ms-dispatch entry.
- Ruff I001 fix: removed blank line between stdlib and local imports in test_smoke.py.

### File List

- ms-dispatch/dispatch/__init__.py
- ms-dispatch/dispatch/dispatch_consumer.py
- ms-dispatch/tests/__init__.py
- ms-dispatch/tests/conftest.py
- ms-dispatch/tests/test_smoke.py
- ms-dispatch/pyproject.toml
- ms-dispatch/Dockerfile
- ms-dispatch/README.md
- ms-dispatch/CLAUDE.md
- Taskfile.yml
- docker-compose/docker-compose-apps.yml
- CLAUDE.md
- docs/architecture.md
- README.md
