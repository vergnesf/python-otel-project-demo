# Models to pull
MODELS := mistral:7b llama3.2:3b qwen3:0.6b granite4:3b mistral-nemo:12b qwen2.5:7b phi4:14b

PROJECTS := agent-logs agent-metrics agent-orchestrator agent-traces agent-ui agent-traduction benchmarks common-ai common-models customer order ordercheck ordermanagement stock supplier suppliercheck

# Detect container runtime (docker or podman)
DOCKER_AVAILABLE := $(shell command -v docker >/dev/null 2>&1 && echo true || echo false)
PODMAN_AVAILABLE := $(shell command -v podman >/dev/null 2>&1 && echo true || echo false)

ifeq ($(PODMAN_AVAILABLE),true)
	COMPOSE_CMD := podman-compose
	COMPOSE_RUN_ARGS := --podman-run-args="--replace"
else ifeq ($(DOCKER_AVAILABLE),true)
	COMPOSE_CMD := docker-compose
	COMPOSE_RUN_ARGS :=
else
	COMPOSE_CMD := podman-compose
	COMPOSE_RUN_ARGS := --podman-run-args="--replace"
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

# Generic redeploy command (usage: make redeploy agent-ui)
redeploy:
	@SERVICE="$(filter-out $@,$(MAKECMDGOALS))"; \
	if [ -z "$$SERVICE" ]; then \
	    echo "❌ Error: No service specified!"; \
	    echo "Usage: make redeploy <service-name>"; \
	    echo "Example: make redeploy agent-ui"; \
	    exit 1; \
	fi; \
	echo "Redeploying service: $$SERVICE using $(COMPOSE_CMD)..."; \
	$(COMPOSE_CMD) $(COMPOSE_RUN_ARGS) up -d --force-recreate --no-deps --build --no-cache $$SERVICE

%:
	@echo "Target '$@' not found. Use 'make help' or check available targets."

tools-format:
	#echo "Use black to format python files"
	for project in $(PROJECTS); do \
		echo "Formatting project $$project..."; \
		cd $$project && uv run black . && cd ..; \
	done