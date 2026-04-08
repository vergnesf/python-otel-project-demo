# Deferred Work

## Deferred from: code review (2026-04-08)

- **500 after committed transaction — no rollback path** [`ms-beerstock/routes/beerstock.py:236`, `ms-cellar/routes/cellar.py:243`] — Si le guard `if None` se déclenche après un `db.commit()`, la transaction est déjà committée mais le client reçoit un 500. Branche théoriquement inatteignable (invariant de la couche CRUD), mais si elle se déclenche l'état DB est incohérent sans action compensatoire. Préexistant.

- **Double-commit / stale read dans `ship_beer_stock`** [`ms-beerstock/beerstock/crud.py`] — `ship_beer_stock` appelle `db.commit()` en interne, puis la route le rappelle. Le `get_beer_stock_by_style` suivant lit depuis la même session sans `db.refresh()`, ce qui peut renvoyer un objet stale en cas d'écriture concurrente. Préexistant.

- **`REJECT_RATE` non validé dans `ms-quality-control`** [`ms-quality-control/quality_control/quality_consumer.py`] — `ERROR_RATE` et `REJECT_RATE` ne sont ni clampés ni validés (contrairement aux services pairs qui clampent `ERROR_RATE` à `[0.0, 1.0]`). Une valeur hors plage passera silencieusement. Préexistant.

- **Pas de retry/backoff sur erreurs Kafka transitoires** [`ms-brewcheck`, `ms-ingredientcheck`, `ms-quality-control`] — Une erreur Kafka transitoire (ex. `_ALL_BROKERS_DOWN`, `_TRANSPORT`) lève une `KafkaException` qui remonte jusqu'au `finally: consumer.close()` et tue le process définitivement. Aucun retry/backoff n'est implémenté — le service repart uniquement si Docker le redémarre via `restart: unless-stopped`. Préexistant, commun aux trois consumers.
