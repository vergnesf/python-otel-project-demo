FROM python:3.14-slim

# Avoid prompts during package install
ENV DEBIAN_FRONTEND=noninteractive

# System dependencies + Node.js (pour promptfoo)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    make \
    ca-certificates \
    gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install promptfoo globally
RUN npm install -g promptfoo

# Create non-root user (matches devcontainer convention)
RUN groupadd --gid 1000 vscode \
    && useradd --uid 1000 --gid 1000 -m -s /bin/bash vscode

USER vscode
WORKDIR /workspace

# Install UV pour l'utilisateur vscode
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/home/vscode/.local/bin:$PATH"
