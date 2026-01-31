.PHONY: models-init

# Models to pull
MODELS := mistral:7b llama3.2:3b qwen3:0.6b granite4:3b mistral-nemo:12b qwen2.5:7b phi4:14b

PROJECTS := agent-orchestrator agent-translator agent-logger agent-metrics

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