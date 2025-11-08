# Use an official Python base image
ARG DOCKER_REGISTRY=""
ARG IMG_PYTHON="python:3.13-slim"
FROM ${DOCKER_REGISTRY}${IMG_PYTHON}

USER root

# Set the working directory
WORKDIR /app

# Copy uv configuration files
COPY ordercheck/pyproject.toml /app/
COPY ordercheck/ordercheck /app
COPY common/common/ /app/common/common

# Install uv
RUN pip install uv && \
    uv add pip && \
    uv run opentelemetry-bootstrap -a install

# Set the default command to run the producer
CMD ["uv", "run", "opentelemetry-instrument", "python", "/app/ordercheck_consumer.py"]