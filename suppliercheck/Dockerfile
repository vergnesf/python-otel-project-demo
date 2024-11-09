# Use an official Python base image
ARG DOCKER_REGISTRY
ARG IMG_PYTHON
FROM ${DOCKER_REGISTRY}${IMG_PYTHON}

USER root

# Set the working directory
WORKDIR /app

# Copy uv configuration files
COPY suppliercheck/pyproject.toml /app/
COPY suppliercheck/uv.lock  /app/
COPY suppliercheck/suppliercheck /app
COPY common/common/ /app/common/common

# Install uv
RUN pip install uv && \
    uv add pip && \
    uv run opentelemetry-bootstrap -a install

# Set the default command to run the producer
CMD ["uv", "run", "opentelemetry-instrument", "python", "/app/suppliercheck_consumer.py"]