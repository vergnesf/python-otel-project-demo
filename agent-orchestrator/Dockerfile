ARG DOCKER_REGISTRY
ARG IMG_PYTHON

FROM ${DOCKER_REGISTRY}${IMG_PYTHON}

RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

ENV PYTHON_JIT=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN groupadd -r appuser && useradd -r -g appuser appuser -m

COPY agent-orchestrator/pyproject.toml /app/agent-orchestrator/
COPY common-ai /app/common-ai/

WORKDIR /app/agent-orchestrator

RUN pip install --no-cache-dir uv && \
    uv sync --no-dev && \
    uv pip install pip && \
    uv run --no-dev opentelemetry-bootstrap -a install

COPY agent-orchestrator/agent_orchestrator /app/agent-orchestrator/agent_orchestrator/

RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8001

CMD ["uv", "run", "--no-dev","opentelemetry-instrument", "uvicorn", "agent_orchestrator.main:app", "--host", "0.0.0.0", "--port", "8001", "--timeout-keep-alive", "600", "--timeout-graceful-shutdown", "600"]
