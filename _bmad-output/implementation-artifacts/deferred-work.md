# Deferred Work

## Deferred from: code review (2026-04-08)

- **500 after committed transaction — no rollback path** [`ms-beerstock/routes/beerstock.py:236`, `ms-cellar/routes/cellar.py:243`] — If the `if None` guard fires after `db.commit()`, the transaction is already committed but the client receives a 500. Branch is theoretically unreachable (CRUD layer invariant), but if triggered the DB state is inconsistent with no compensating action. Pre-existing.

- **Double-commit / stale read in `ship_beer_stock`** [`ms-beerstock/beerstock/crud.py`] — `ship_beer_stock` calls `db.commit()` internally, then the route calls it again. The subsequent `get_beer_stock_by_style` reads from the same session without `db.refresh()`, which may return a stale object under concurrent writes. Pre-existing.

- **`REJECT_RATE` not validated in `ms-quality-control`** [`ms-quality-control/quality_control/quality_consumer.py`] — Resolved in PR #150 (ValueError handling + range clamping added). Item closed.

- **No retry/backoff on transient Kafka errors** [`ms-brewcheck`, `ms-ingredientcheck`, `ms-quality-control`] — A transient Kafka error (e.g. `_ALL_BROKERS_DOWN`, `_TRANSPORT`) raises a `KafkaException` that propagates to `finally: consumer.close()` and kills the process permanently. No retry/backoff implemented — service restarts only if Docker revives it via `restart: unless-stopped`. Pre-existing, common to all three consumers.

- **`sys.exit(1)` without OTEL telemetry flush** [`ms-brewer`, `ms-supplier`, `ms-retailer`, `ms-brewcheck`, `ms-ingredientcheck`, `ms-quality-control`] — On missing `KAFKA_BOOTSTRAP_SERVERS`, `sys.exit(1)` is called before the OpenTelemetry SDK has a chance to flush buffered spans/logs. The `opentelemetry-instrument` wrapper may handle shutdown hooks, but this is not guaranteed. Pre-existing learning-lab trade-off.

- **`time.sleep(interval_seconds)` not interruptible on SIGTERM** [`ms-brewmaster`, `ms-brewer`, `ms-supplier`] — After `_shutdown` sets `running = False`, the main loop may be blocked in `time.sleep()` (up to 60s default). Docker's stop timeout is 10s before SIGKILL, so graceful shutdown is rarely achieved at long intervals. In docker-compose the interval is set to 5s, mitigating the issue in practice. Pre-existing.

- **`ms-fermentation` still uses `while True` with no signal handler** — ✅ Resolved in PR #150.

## Deferred from: code review of PR #150 (2026-04-12)

- **KAFKA_BOOTSTRAP_SERVERS guard placed after module-level Producer instantiation** [`ms-brewer`, `ms-retailer`, `ms-supplier`] — `producer = Producer(...)` est instancié au niveau module avec le fallback `"localhost:9092"` avant que le `sys.exit(1)` dans `__main__` soit atteint. Design trade-off intentionnel : le guard dans `__main__` empêche l'exécution de la boucle principale mais ne prévient pas la création du Producer. Documenté dans la description PR #150 ("check placé dans `__main__` pour ne pas casser les imports de test"). Pre-existing.

- **`$RUNTIME inspect` utilise le service name comme container name** [`Taskfile.yml`] — La boucle `for svc in {{.HEALTHCHECK_SERVICES}}` passe le nom du service directement à `$RUNTIME inspect "$svc"`. Si le container a un nom avec prefix projet (ex: `myproject_ms-brewery_1`), `inspect` échoue silencieusement et `any_running` reste `false`, sautant les checks même si les containers sont up. Pre-existing, dépend de la convention de nommage de l'environnement.

- **`podman inspect` retourne `"null"` au lieu de `""` pour containers sans HEALTHCHECK** [`Taskfile.yml`] — `docker inspect --format '{{.State.Health.Status}}'` retourne une chaîne vide pour un container sans `HEALTHCHECK` (correctement rattrapée par `${status:-unknown}`), mais `podman inspect` peut retourner `"null"` — la substitution ne se déclenche pas et le branch `else` affiche `✗ null` au lieu du message descriptif `✗ unknown`. Cosmétique. Pre-existing.
