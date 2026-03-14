ARG DOCKER_REGISTRY
ARG IMG_PYTHON

FROM ${DOCKER_REGISTRY}${IMG_PYTHON}

RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

ENV PYTHON_JIT=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN groupadd -r appuser && useradd -r -g appuser appuser -m

COPY ms-order/pyproject.toml /app/ms-order/
COPY lib-models /app/lib-models/

WORKDIR /app/ms-order

RUN pip install --no-cache-dir uv && \
    uv add pip && \
    uv run --no-dev opentelemetry-bootstrap -a install

COPY ms-order/order /app/ms-order/order/

RUN chown -R appuser:appuser /app

USER appuser

CMD ["uv", "run", "--no-dev", "opentelemetry-instrument", "python", "order/main.py"]
