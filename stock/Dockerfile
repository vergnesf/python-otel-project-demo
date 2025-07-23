# Use an official Python base image
ARG DOCKER_REGISTRY=""
ARG IMG_PYTHON="python:3.13-slim"
FROM ${DOCKER_REGISTRY}${IMG_PYTHON}

USER root

# Set the working directory
WORKDIR /app

# Copy uv configuration files
COPY stock/pyproject.toml /app/
COPY stock/uv.lock  /app/
COPY stock/stock /app/stock
COPY common/common/ /app/common/common

# Install uv
RUN pip install uv && \
    uv add pip && \
    uv run opentelemetry-bootstrap -a install

EXPOSE 5000

# Set the default command to run the producer
CMD ["uv", "run", "opentelemetry-instrument", "python", "-m", "stock.main"]


