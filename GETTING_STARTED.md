# Getting Started Guide 🚀

This guide will help you get the complete stack up and running with Docker or Podman, including GPU support for AI workloads.

## 📋 Prerequisites

### Docker Setup

- **Docker** and **Docker Compose** installed
- **Git** for cloning the repository
- Minimum **8GB RAM** recommended (16GB+ for full AI workloads)

### Podman Setup (Alternative)

- **Podman** and **Podman Compose** installed
- **SELinux** considerations (see below for GPU setup)

### GPU Requirements (Optional but Recommended)

For AI/LLM acceleration with NVIDIA GPUs:
- **NVIDIA drivers** installed
- **NVIDIA Container Toolkit** installed (see GPU section below)
- **CUDA-capable GPU** with sufficient VRAM

## 🐳 Quick Start with Docker

### 1. Clone the Repository

```bash
# Clone the repository
git clone <repository-url>
cd python-otel-project-demo
```

### 2. Start All Services

```bash
# Start the complete stack
docker-compose up -d

# View logs to monitor startup
docker-compose logs -f
```

### 3. Access the Services

Once all containers are running (may take 1-2 minutes for first startup):

- **Grafana Dashboard**: [http://localhost:3000](http://localhost:3000) (admin/admin)
- **Agents Web UI**: [http://localhost:3002](http://localhost:3002)
- **Kafka UI**: [http://localhost:8080](http://localhost:8080)
- **Database Admin**: [http://localhost:8081](http://localhost:8081)

## 🐋 Using Podman Instead of Docker

### 1. Install Podman Compose

```bash
# Install podman-compose if not available
pip install podman-compose
```

### 2. Start Services with Podman

```bash
# Use podman-compose instead of docker-compose
podman-compose up -d

# View logs
podman-compose logs -f
```

### 3. SELinux Considerations

On SELinux-enabled systems (Fedora, RHEL, CentOS), you may need to:

```bash
# Allow containers to use devices (for GPU access)
sudo setsebool -P container_use_devices true
```

## 🖥️ GPU Setup with NVIDIA Container Toolkit

### 1. Install NVIDIA Container Toolkit

**For Docker:**
```bash
# Configure repository and install
distribution=$(. /etc/os-release;echo $ID$VERSION_ID) && \
curl -s -L https://nvidia.github.io/nvidia-container-toolkit/gpgkey | sudo apt-key add - && \
curl -s -L https://nvidia.github.io/nvidia-container-toolkit/$distribution/nvidia-container-toolkit.list | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt update
sudo apt install -y nvidia-container-toolkit
sudo systemctl restart docker
```

**For Podman:**
```bash
# Install toolkit
sudo dnf install -y nvidia-container-toolkit

# Configure Podman
sudo nvidia-ctk runtime configure --runtime=podman
sudo systemctl restart podman
```

### 2. Verify GPU Access

```bash
# Test GPU access with a simple container
podman run --rm --gpus all nvidia/cuda:11.0.3-base-ubuntu20.04 nvidia-smi

# You should see your GPU information
```

### 3. Start Services with GPU Support

```bash
# The docker-compose.yml is already configured for GPU access
podman-compose up -d

# Verify Ollama is using GPU
podman logs ollama | grep -i "inference compute"
# Should show "id=cuda" instead of "id=cpu"
```

### 4. Troubleshooting GPU Issues

**If GPU is not detected:**

1. Check NVIDIA drivers are installed:
   ```bash
   nvidia-smi
   ```

2. Verify container runtime configuration:
   ```bash
   sudo nvidia-ctk runtime configure --runtime=docker  # or podman
   sudo systemctl restart docker  # or podman
   ```

3. Check device permissions:
   ```bash
   ls -l /dev/nvidia*
   ```

4. For Podman on SELinux systems:
   ```bash
   sudo setsebool -P container_use_devices true
   ```

## 🎯 Post-Installation Setup

### 1. Configure MCP Authentication

For AI agents to work, you need to set up Grafana service account:

```bash
# 1. Open Grafana: http://localhost:3000
# 2. Login with admin/admin
# 3. Go to Configuration → Service accounts → Create service account
# 4. Generate token and copy it
# 5. Add token to environment
echo 'GRAFANA_SERVICE_ACCOUNT_TOKEN=eyJ...your-token...' >> .env

# 6. Restart MCP service
docker-compose restart grafana-mcp
# or
podman-compose restart grafana-mcp
```

### 2. Verify All Services

```bash
# Check all containers are running
docker-compose ps
# or
podman-compose ps

# Check specific service logs
docker-compose logs -f agent-logs
```

## 🔧 Common Commands

```bash
# Start all services
docker-compose up -d
# podman-compose up -d

# Stop all services
docker-compose down
# podman-compose down

# Rebuild and start
docker-compose up --build -d
# podman-compose up --build -d

# View logs for specific service
docker-compose logs -f order
# podman-compose logs -f order

# Restart a service
docker-compose restart agent-logs
# podman-compose restart agent-logs

# Complete cleanup (removes all data)
docker-compose down -v
# podman-compose down -v
```

## 🎓 Next Steps

- **Explore the Architecture**: See [docs/architecture.md](docs/architecture.md)
- **Learn about AI Agents**: See [docs/agents.md](docs/agents.md)
- **Local Development**: See [docs/handbook/development.md](docs/handbook/development.md)
- **Troubleshooting**: See [docs/handbook/troubleshooting.md](docs/handbook/troubleshooting.md)

## 💡 Tips

1. **Resource Management**: The stack uses significant resources. For development, you can start only specific services.

2. **GPU Monitoring**: Use `nvidia-smi` to monitor GPU usage by containers.

3. **Network Isolation**: All services communicate via Docker/Podman network automatically.

4. **Persistent Data**: Data is stored in Docker volumes. Use `docker-compose down -v` to clean everything.

Enjoy exploring the AI-powered observability platform! 🎉