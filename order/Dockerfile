# Use an official Python base image
ARG DOCKER_REGISTRY=""
ARG IMG_PYTHON="python:3.14-slim"
FROM ${DOCKER_REGISTRY}${IMG_PYTHON}

USER root

# Set the working directory
WORKDIR /app

# Copy uv configuration files
COPY order/pyproject.toml /app/
COPY order/order /app/order
COPY common/common/ /app/common/common

# Install uv and dependencies (excluding dev dependencies)
RUN pip install uv && \
    uv sync --no-dev && \
    uv run opentelemetry-bootstrap -a install

EXPOSE 5000

# Set the default command to run the producer
CMD ["uv", "run", "opentelemetry-instrument", "python", "-m", "order.main"]


