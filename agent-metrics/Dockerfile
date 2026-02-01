ARG DOCKER_REGISTRY
ARG IMG_PYTHON

FROM ${DOCKER_REGISTRY}${IMG_PYTHON}

RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

ENV PYTHON_JIT=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN groupadd -r appuser && useradd -r -g appuser appuser -m

COPY agent-metrics/pyproject.toml /app/agent-metrics/
COPY common-ai /app/common-ai/

WORKDIR /app/agent-metrics

RUN pip install --no-cache-dir uv && \
    uv add pip && \
    uv run --no-dev opentelemetry-bootstrap -a install

COPY agent-metrics/agent_metrics /app/agent-metrics/agent_metrics/

RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8002

CMD ["uv", "run", "--no-dev", "opentelemetry-instrument", "uvicorn", "agent_metrics.main:app", "--host", "0.0.0.0", "--port", "8002"]
