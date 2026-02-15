FROM python:3.14-slim

# Avoid prompts during package install
ENV DEBIAN_FRONTEND=noninteractive

# make is the only system tool needed at image level
# (git, node, uv are installed via devcontainer features / postCreateCommand)
RUN apt-get update && apt-get install -y --no-install-recommends \
    make \
    && rm -rf /var/lib/apt/lists/*
