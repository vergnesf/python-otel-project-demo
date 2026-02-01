ARG DOCKER_REGISTRY=""
ARG IMG_PYTHON="python:3.14-slim"

FROM ${DOCKER_REGISTRY}${IMG_PYTHON}

RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

ENV PYTHON_JIT=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN groupadd -r appuser && useradd -r -g appuser appuser -m

COPY ordermanagement/pyproject.toml /app/ordermanagement/
COPY common-models /app/common-models/

WORKDIR /app/ordermanagement

RUN pip install --no-cache-dir uv && \
    uv add pip && \
    uv run --no-dev opentelemetry-bootstrap -a install

COPY ordermanagement/ordermanagement /app/ordermanagement/ordermanagement/

RUN chown -R appuser:appuser /app

USER appuser

CMD ["uv", "run", "--no-dev", "opentelemetry-instrument", "python", "ordermanagement/ordermanagement.py"]
