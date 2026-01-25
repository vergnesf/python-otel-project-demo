# Podman deployment (dev) — quick guide

Contents:
- kube/*.yaml — pod manifests compatible with `podman play kube` (Kafka, Observability, DB, Agents, Apps)
- scripts/deploy-pods.sh — helper to create volume dirs, pull upstream images and run `podman play kube`
- scripts/teardown-pods.sh — remove pods

Quick steps:

1. Build local images for services that are in-repo (examples):

```bash
podman build -t project/customer:local -f customer/Dockerfile .
podman build -t project/order:local -f order/Dockerfile .
# repeat for other in-repo services (supplier, stock, ordercheck, suppliercheck, ordermanagement, agent-*)
```

2. Create required host directories (the deploy script does this for `/srv/podman/...`) or adjust manifests to point elsewhere.

3. Run deploy:

```bash
./scripts/deploy-pods.sh
```

4. Inspect pods:

```bash
podman pod ps
podman ps
podman logs <container>
```

5. Teardown:

```bash
./scripts/teardown-pods.sh
```

Notes and caveats:
- Manifests use hostPath volumes under `/srv/podman/python-otel-project-demo/*`. Change paths in the YAMLs if you prefer another location.
- Environment variables are minimal in the manifests. For full parity you can adapt each manifest to include more env vars or pass an `--env-file` when running containers manually.
- For production-like isolation, prefer one container per pod (or use separate pods per service) instead of grouping many services into a single pod as done for `apps-pod` (Option A: convenience for dev).
