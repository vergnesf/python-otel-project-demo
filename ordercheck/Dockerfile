ARG DOCKER_REGISTRY
ARG IMG_PYTHON

FROM ${DOCKER_REGISTRY}${IMG_PYTHON}

RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

ENV PYTHON_JIT=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN groupadd -r appuser && useradd -r -g appuser appuser -m

COPY ordercheck/pyproject.toml ./ordercheck/
COPY ordercheck/ordercheck /app/ordercheck/ordercheck/
COPY common-models ./common-models/

WORKDIR /app/ordercheck

RUN pip install --no-cache-dir uv && \
    uv sync --no-dev && \
    uv run --no-dev opentelemetry-bootstrap -a install

RUN chown -R appuser:appuser /app

USER appuser

CMD ["uv", "run", "--no-dev", "opentelemetry-instrument", "python", "ordercheck/ordercheck_consumer.py"]
