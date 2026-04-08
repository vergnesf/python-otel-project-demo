# Deferred Work

## Deferred from: code review (2026-04-08)

- **500 after committed transaction — no rollback path** [`ms-beerstock/routes/beerstock.py:236`, `ms-cellar/routes/cellar.py:243`] — If the `if None` guard fires after `db.commit()`, the transaction is already committed but the client receives a 500. Branch is theoretically unreachable (CRUD layer invariant), but if triggered the DB state is inconsistent with no compensating action. Pre-existing.

- **Double-commit / stale read in `ship_beer_stock`** [`ms-beerstock/beerstock/crud.py`] — `ship_beer_stock` calls `db.commit()` internally, then the route calls it again. The subsequent `get_beer_stock_by_style` reads from the same session without `db.refresh()`, which may return a stale object under concurrent writes. Pre-existing.

- **`REJECT_RATE` not validated in `ms-quality-control`** [`ms-quality-control/quality_control/quality_consumer.py`] — Resolved in PR #150 (ValueError handling + range clamping added). Item closed.

- **No retry/backoff on transient Kafka errors** [`ms-brewcheck`, `ms-ingredientcheck`, `ms-quality-control`] — A transient Kafka error (e.g. `_ALL_BROKERS_DOWN`, `_TRANSPORT`) raises a `KafkaException` that propagates to `finally: consumer.close()` and kills the process permanently. No retry/backoff implemented — service restarts only if Docker revives it via `restart: unless-stopped`. Pre-existing, common to all three consumers.

- **`sys.exit(1)` without OTEL telemetry flush** [`ms-brewer`, `ms-supplier`, `ms-retailer`, `ms-brewcheck`, `ms-ingredientcheck`, `ms-quality-control`] — On missing `KAFKA_BOOTSTRAP_SERVERS`, `sys.exit(1)` is called before the OpenTelemetry SDK has a chance to flush buffered spans/logs. The `opentelemetry-instrument` wrapper may handle shutdown hooks, but this is not guaranteed. Pre-existing learning-lab trade-off.

- **`time.sleep(interval_seconds)` not interruptible on SIGTERM** [`ms-brewmaster`, `ms-brewer`, `ms-supplier`] — After `_shutdown` sets `running = False`, the main loop may be blocked in `time.sleep()` (up to 60s default). Docker's stop timeout is 10s before SIGKILL, so graceful shutdown is rarely achieved at long intervals. In docker-compose the interval is set to 5s, mitigating the issue in practice. Pre-existing.

- **`ms-fermentation` still uses `while True` with no signal handler** [`ms-fermentation/fermentation/fermentation_worker.py`] — Other workers (ms-brewer, ms-supplier, ms-brewmaster) register a `running` flag + `_shutdown` handler, but ms-fermentation does not. SIGTERM from Docker causes a dirty shutdown. Pre-existing.
