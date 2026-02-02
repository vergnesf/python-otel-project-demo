.PHONY: models-init tools-format compose-up compose-down

# Models to pull
MODELS := mistral:7b llama3.2:3b qwen3:0.6b granite4:3b mistral-nemo:12b qwen2.5:7b phi4:14b

PROJECTS := agent-logs agent-metrics agent-orchestrator agent-traces agent-ui agent-traduction benchmarks common-ai common-models customer order ordercheck ordermanagement stock supplier suppliercheck

# Detect container runtime (docker or podman)
DOCKER_AVAILABLE := $(shell command -v docker >/dev/null 2>&1 && echo true || echo false)
PODMAN_AVAILABLE := $(shell command -v podman >/dev/null 2>&1 && echo true || echo false)

ifeq ($(PODMAN_AVAILABLE),true)
	COMPOSE_CMD := podman-compose
else ifeq ($(DOCKER_AVAILABLE),true)
	COMPOSE_CMD := docker-compose
else
	COMPOSE_CMD := podman-compose
endif

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

tools-format:
	#echo "Use black to format python files"
	for project in $(PROJECTS); do \
		echo "Formatting project $$project..."; \
		cd $$project && uv run black . && cd ..; \
	done

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