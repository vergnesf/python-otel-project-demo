# Use an official Python base image
ARG DOCKER_REGISTRY
ARG IMG_PYTHON
FROM ${DOCKER_REGISTRY}${IMG_PYTHON}

USER root

# Set the working directory
WORKDIR /app

# Copy Poetry configuration files
COPY suppliercheck/pyproject.toml /app/
COPY suppliercheck/poetry.lock  /app/
COPY suppliercheck/suppliercheck /app
COPY common/common/ /app/common/common

# Install Poetry
RUN pip install poetry && \
    poetry install --no-root && \
    poetry run opentelemetry-bootstrap -a install

# Set the default command to run the producer
CMD ["poetry", "run", "opentelemetry-instrument", "python", "/app/suppliercheck_consumer.py"]