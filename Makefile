.PHONY: models-init tools-format lint compose-up compose-down test test-lint test-unit test-integration

# Models to pull
MODELS := mistral:7b llama3.2:3b qwen3:0.6b granite4:3b mistral-nemo:12b qwen2.5:7b phi4:14b

# All service directories — used by lint (ruff) and tools-format (ruff format).
# Includes agent/benchmark services that have no smoke tests.
PROJECTS := agent-logs agent-metrics agent-orchestrator agent-traces agent-ui agent-traduction benchmark common-ai common-models customer order ordercheck ordermanagement stock supplier suppliercheck
# Business services with runnable Python processes and a tests/ directory.
# Shared libraries (common-models, common-ai) are excluded — they have no executable entry point.
# Scope: make test-lint and make test-unit. For full lint use PROJECTS (all 16 dirs).
KEEPER_SERVICES := customer order ordercheck ordermanagement stock supplier suppliercheck
# Subset of KEEPER_SERVICES with a container healthcheck defined in docker-compose-apps.yml.
# Only Flask REST APIs (order, stock) have healthchecks — Kafka producers/consumers and workers do not.
# WARNING: only add a service here if docker-compose-apps.yml defines a HEALTHCHECK for it;
# otherwise the integration check will always report "unknown" and fail.
# Scope: make test-integration health loop only.
HEALTHCHECK_SERVICES := order stock

# Detect container runtime (docker or podman)
DOCKER_AVAILABLE := $(shell command -v docker >/dev/null 2>&1 && echo true || echo false)
PODMAN_AVAILABLE := $(shell command -v podman >/dev/null 2>&1 && echo true || echo false)

ifeq ($(PODMAN_AVAILABLE),true)
	COMPOSE_CMD := podman-compose
else ifeq ($(DOCKER_AVAILABLE),true)
	COMPOSE_CMD := docker compose
else
	COMPOSE_CMD := podman-compose
endif

COMPOSE_CMD += --env-file $(CURDIR)/.env

# When running inside a devcontainer with a Podman socket, bind mount paths must be host paths.
# Detect the host path from the btrfs subvolume source (format: /dev/xxx[/host/path]).
_MOUNT_SRC := $(shell findmnt -n -o SOURCE "$(CURDIR)" 2>/dev/null)
HOST_PWD   := $(if $(findstring [,$(_MOUNT_SRC)),$(shell echo '$(_MOUNT_SRC)' | sed 's|.*\[||;s|\].*||'),$(CURDIR))
COMPOSE_CMD := env PWD=$(HOST_PWD) $(COMPOSE_CMD)

models-init:
	@echo "Detecting runtime and looking for running container 'ollama'..."
	@RUNTIME=""; \
	if command -v docker >/dev/null 2>&1 && docker ps --format '{{.Names}}' | grep -xq ollama; then RUNTIME=docker; fi; \
	if [ -z "$$RUNTIME" ] && command -v podman >/dev/null 2>&1 && podman ps --format '{{.Names}}' | grep -xq ollama; then RUNTIME=podman; fi; \
	if [ -z "$$RUNTIME" ]; then echo "No running 'ollama' container found (docker or podman). Start it first."; exit 1; fi; \
	echo "Using $$RUNTIME exec to run pulls"; \
	for m in $(MODELS); do \
		echo "--> Pulling $$m"; \
		if [ "$$RUNTIME" = "docker" ]; then \
			docker exec ollama sh -c "ollama pull $$m" || echo "pull failed for $$m"; \
		else \
			podman exec ollama sh -c "ollama pull $$m" || echo "pull failed for $$m"; \
		fi; \
	done; \
	echo "models-init: done"

# Scoped lint on KEEPER services, then smoke tests, then integration.
# Use 'make lint' for full project lint. Use 'make -k test' to run all phases on failure.
test: test-lint test-unit test-integration

test-lint:
	@echo "Linting KEEPER services..."
	@uvx ruff check $(KEEPER_SERVICES)

test-unit:
	@echo "Running smoke tests for KEEPER services..."
	@failed=0; total_tests=0; \
	for svc in $(KEEPER_SERVICES); do \
		printf "  %-20s" "$$svc"; \
		output=$$(cd $$svc 2>&1 && timeout 60 uv run pytest tests/ -q --tb=short 2>&1); \
		exitcode=$$?; \
		if [ $$exitcode -eq 0 ]; then \
			tcount=$$(echo "$$output" | sed -n 's/^\([0-9]\+\) passed.*/\1/p' | head -1); \
			total_tests=$$((total_tests + $${tcount:-0})); \
			echo "✓ ($${tcount:-?} passed)"; \
		elif [ $$exitcode -eq 124 ]; then \
			echo "✗ (timeout >60s)"; \
			printf "  === %s ===\n" "$$svc"; \
			echo "$$output" | sed 's/^/  /'; \
			failed=$$((failed+1)); \
		elif [ $$exitcode -eq 5 ]; then \
			echo "✗ (no tests found — add tests to tests/)"; \
			printf "  === %s ===\n" "$$svc"; \
			echo "$$output" | sed 's/^/  /'; \
			failed=$$((failed+1)); \
		else \
			echo "✗"; \
			printf "  === %s ===\n" "$$svc"; \
			echo "$$output" | sed 's/^/  /'; \
			failed=$$((failed+1)); \
		fi; \
	done; \
	if [ $$failed -eq 0 ]; then echo "All smoke tests passed ($$total_tests tests)"; else echo "$$failed service(s) failed; $$total_tests tests passed in services that passed"; exit 1; fi

test-integration:
	@echo "Checking container health for $(HEALTHCHECK_SERVICES) (requires running stack)..."
	@# Only HEALTHCHECK_SERVICES (order, stock) have container healthchecks; Kafka services and workers do not.
	@# grep searches STATUS column values: Up/running/healthy/unhealthy/starting; service names don't contain these words.
	@# Health check JSON parsing assumes Docker/Compose --format json output; format varies by version.
	@if [ "$(DOCKER_AVAILABLE)" = "false" ] && [ "$(PODMAN_AVAILABLE)" = "false" ]; then \
		echo "  No container runtime found (docker/podman) — skipping integration checks"; \
		exit 0; \
	fi; \
	if ! $(COMPOSE_CMD) -f docker-compose/docker-compose-apps.yml ps $(HEALTHCHECK_SERVICES) 2>/dev/null | grep -qE "\b(Up|running|healthy|unhealthy|starting)\b"; then \
		echo "  Services $(HEALTHCHECK_SERVICES) not running — skipping integration checks (run make compose-up first)"; \
		exit 0; \
	fi; \
	failed=0; \
	for svc in $(HEALTHCHECK_SERVICES); do \
		printf "  %-20s" "$$svc"; \
		status=$$($(COMPOSE_CMD) -f docker-compose/docker-compose-apps.yml ps $$svc --format json 2>/dev/null | tr -d '\n' | sed -n 's/.*"Health":"\([^"]*\)".*/\1/p'); \
		status=$${status:-unknown}; \
		if [ "$$status" = "healthy" ]; then echo "✓ healthy"; \
		elif [ "$$status" = "unknown" ]; then echo "✗ unknown (no HEALTHCHECK instruction in docker-compose-apps.yml for $$svc — run: docker inspect $$svc | grep -A5 Health)"; failed=$$((failed+1)); \
		else echo "✗ $$status"; failed=$$((failed+1)); fi; \
	done; \
	if [ $$failed -eq 0 ]; then echo "All services healthy"; else echo "$$failed service(s) unhealthy"; exit 1; fi

lint:
	@echo "Linting all projects with ruff..."
	@uvx ruff check $(PROJECTS)

tools-format:
	@echo "Formatting all projects with ruff format..."
	@uvx ruff format $(PROJECTS)

compose-up:
	@echo "Bringing up observability, db, kafka, ai-tools, ai, then apps (in that order)..."
	@echo "Ensuring network otel-network exists..."
	@# create otel-network if it doesn't exist (support docker and podman)
	@if command -v docker >/dev/null 2>&1; then \
		docker network inspect otel-network >/dev/null 2>&1 || docker network create otel-network; \
	elif command -v podman >/dev/null 2>&1; then \
		podman network inspect otel-network >/dev/null 2>&1 || podman network create otel-network; \
	fi
	$(COMPOSE_CMD) -f docker-compose/docker-compose-observability.yml up -d
	$(COMPOSE_CMD) -f docker-compose/docker-compose-db.yml up -d
	$(COMPOSE_CMD) -f docker-compose/docker-compose-kafka.yml up -d
	$(COMPOSE_CMD) -f docker-compose/docker-compose-ai-tools.yml up -d
	$(COMPOSE_CMD) -f docker-compose/docker-compose-ai.yml up -d --build
	$(COMPOSE_CMD) -f docker-compose/docker-compose-apps.yml up -d --build
	$(COMPOSE_CMD) -f docker-compose/docker-compose-traefik.yml up -d
compose-down:
	@echo "Tearing down apps, ai, ai-tools, kafka, db, then observability (reverse order)..."
	$(COMPOSE_CMD) -f docker-compose/docker-compose-apps.yml down
	$(COMPOSE_CMD) -f docker-compose/docker-compose-ai.yml down
	$(COMPOSE_CMD) -f docker-compose/docker-compose-ai-tools.yml down
	$(COMPOSE_CMD) -f docker-compose/docker-compose-kafka.yml down
	$(COMPOSE_CMD) -f docker-compose/docker-compose-db.yml down
	$(COMPOSE_CMD) -f docker-compose/docker-compose-observability.yml down
	$(COMPOSE_CMD) -f docker-compose/docker-compose-traefik.yml down
