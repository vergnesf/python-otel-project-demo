#!/bin/bash

# Script to force rebuild of agent-ui with podman

set -e

echo "🔄 Forcing rebuild of agent-ui..."

# Stop the service if running
if podman-compose ps | grep -q agent-ui; then
    echo "🛑 Stopping agent-ui service..."
    podman-compose down agent-ui
fi

# Remove old containers
if podman ps -a --format '{{.Names}}' | grep -q agent-ui; then
    echo "🗑️  Removing old containers..."
    podman rm -f agent-ui 2>/dev/null || true
fi

# Remove old images
if podman images --format '{{.Repository}}:{{.Tag}}' | grep -q 'agent-ui:latest'; then
    echo "🧹 Removing old images..."
    podman rmi agent-ui:latest 2>/dev/null || true
fi

# Rebuild with current timestamp to bust cache
echo "🔨 Building new image..."
cd agent-ui
podman build --no-cache -t agent-ui:latest --build-arg BUILD_TIMESTAMP=$(date +%s) .
cd ..

# Restart the service
echo "🚀 Restarting agent-ui service..."
podman-compose up -d agent-ui

# Show build info
echo "✅ Rebuild complete!"
echo "📊 Build info:"
podman exec agent-ui cat /app/BUILD_INFO.txt 2>/dev/null || echo "Build info not available"

echo "🎉 Agent-ui is now running with the latest code!"
echo "🔗 Access at: http://localhost:3002"
