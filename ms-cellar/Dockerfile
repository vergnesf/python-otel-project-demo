ARG DOCKER_REGISTRY
ARG IMG_PYTHON

FROM ${DOCKER_REGISTRY}${IMG_PYTHON}

RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

ENV PYTHON_JIT=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN groupadd -r appuser && useradd -r -g appuser appuser -m

COPY ms-cellar/pyproject.toml /app/ms-cellar/
COPY lib-models /app/lib-models/

WORKDIR /app/ms-cellar

RUN pip install --no-cache-dir uv && \
    uv run --no-dev python -m ensurepip && \
    uv run --no-dev opentelemetry-bootstrap -a install

COPY ms-cellar/cellar /app/ms-cellar/cellar/

RUN chown -R appuser:appuser /app

USER appuser

CMD ["uv", "run", "--no-dev", "opentelemetry-instrument", "python", "cellar/main.py"]
