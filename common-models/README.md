# Common Models

> **Status:** `KEEPER` — Stable service. Expected to stay functional and tested.

Shared business models used by all microservices.

## Contents

- `WoodType`: Enum for wood types (OAK, MAPLE, BIRCH, ELM, PINE)
- `OrderStatus`: Enum for order statuses
- `Stock`: Stock model with wood_type and quantity
- `Order`: Order model
- `OrderTracking`: Order tracking model

## Dependencies

- pydantic>=2.9.2

## 🐳 Podman Compose (rebuild a service)

To force the rebuild of a service without restarting the entire stack:

```bash
podman compose up -d --build --force-recreate --no-deps <service>
```

To ensure a rebuild without cache:

```bash
podman compose build --no-cache <service>
podman compose up -d --force-recreate --no-deps <service>
```
