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

The compose configuration is split across several files and a `Makefile` helper is provided to start them in the correct order.

Order: observability → db → kafka → ai-tools → ai → apps

```bash
# Copy example environment and override images/tokens as needed
cp .env.example .env

# Recommended: use the Makefile which selects docker/podman and brings up all compose files
make compose-up

# View aggregated logs
podman-compose logs -f || docker-compose logs -f
```

### 3. Access the Services

Once all containers are running (may take 1-2 minutes for first startup):

**All services are accessible via Traefik reverse proxy:**

- **Traefik Dashboard**: [http://localhost:8082](http://localhost:8082)
- **Grafana Dashboard**: [http://localhost:8081/grafana/](http://localhost:8081/grafana/) (admin/admin)
- **Agents Web UI**: [http://localhost:8081/agents/ui/](http://localhost:8081/agents/ui/)
- **Kafka UI (AKHQ)**: [http://localhost:8081/akhq/](http://localhost:8081/akhq/)
- **Database Admin (Adminer)**: [http://localhost:8081/adminer/](http://localhost:8081/adminer/)

> **Note**: Services are no longer exposed on individual ports. Traefik handles all external access.

## 🐋 Using Podman Instead of Docker

### 1. Install Podman Compose

```bash
# Install podman-compose if not available
pip install podman-compose
```

### 2. Start Services with Podman

You can still use `podman-compose` directly, but the `Makefile` automates the correct file ordering and will detect `podman` vs `docker`.

```bash
# Recommended (Makefile will call podman when available)
make compose-up

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

## 🎮 GPU Setup with AMD GPUs (Vulkan)

Ollama supports AMD GPUs through Vulkan, which is simpler than ROCm and works out-of-the-box on most modern Linux distributions.

### 1. Verify Vulkan Support

```bash
# Check Vulkan installation
vulkaninfo | grep -i "deviceName\|driverName"

# Example output for AMD GPU:
# deviceName = AMD Radeon RX 9070 XT
# driverName = radv
```

### 2. Configure Compose File for AMD

Edit `docker-compose/docker-compose-ai-tools.yml` - the configuration is already optimized for AMD:

```yaml
ollama:
  image: ${DOCKER_REGISTRY:-}${DOCKER_IMG_OLLAMA}
  container_name: ollama
  environment:
    OLLAMA_VULKAN: "1"  # Enable Vulkan support for AMD
  devices:
    - /dev/dri
  group_add:
    - video
  volumes:
    - ollama-data:/root/.ollama:Z
```

### 3. Verify Device Permissions

```bash
# Check device permissions
ls -l /dev/dri

# Add your user to video group if needed
sudo usermod -aG video $USER
# Log out and back in for group changes to take effect
```

### 4. Start Services with AMD GPU

```bash
# Start the stack
make compose-up

# Verify Ollama is using Vulkan
podman logs ollama | grep -i -E "vulkan|gpu|compute"
# Should show: "Vulkan support enabled" and GPU info
```

### 5. Troubleshooting AMD GPU Issues

**If AMD GPU is not detected:**

1. Verify Vulkan installation:
   ```bash
   vulkaninfo | head -20
   # Should show your AMD GPU
   ```

2. Check device permissions:
   ```bash
   ls -l /dev/dri
   # Should be accessible by video group
   ```

3. Ensure user is in video group:
   ```bash
   groups | grep video
   ```

4. Check Ollama logs for specific errors:
   ```bash
   podman logs ollama 2>&1 | grep -i -A5 "error\|warn"
   ```

5. For Podman on SELinux systems:
   ```bash
   sudo setsebool -P container_use_devices true
   ```

**Supported AMD GPUs:**
- All RDNA architecture GPUs (RX 5000, 6000, 7000, 9000 series)
- Most GCN architecture GPUs (Vega, Polaris)
- Vulkan provides broad compatibility without needing ROCm

## 🎯 Post-Installation Setup

### 1. Create Environment Configuration

First, create your `.env` file from the example:

```bash
# Copy the example environment file
cp .env.example .env

# The .env file is now ready with the default Grafana token
# (You'll update it with your own token in the next step)
```

### 2. Configure MCP Authentication

For AI agents to work, you need to set up Grafana service account with a token:

```bash
# 1. Start the stack (without grafana-mcp working yet)
docker-compose up -d
# or
podman-compose up -d

# 2. Wait for Grafana to be ready (about 30-40 seconds)
# 3. Open Grafana: http://localhost:8081/grafana/
# 4. Login with admin/admin
# 5. Go to Configuration → Service accounts (or use the menu)
# 6. Create a new service account with a descriptive name (e.g., "MCP Integration")
# 7. Generate a token for this service account
# 8. Copy the full token value

# 9. Update your .env file with the actual token
sed -i 's/GRAFANA_SERVICE_ACCOUNT_TOKEN=.*/GRAFANA_SERVICE_ACCOUNT_TOKEN=YOUR_TOKEN_HERE/' .env

# OR manually edit .env and replace the token value

# 10. Restart the grafana-mcp service to apply the new token
make redeploy grafana-mcp
```

### 3. Verify All Services

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
# Start all services (preferred)
make compose-up

# Stop all services
make compose-down

# Rebuild a specific service (useful during development)
podman-compose -f <compose-files...> up --build -d <service> || \
   docker-compose -f <compose-files...> up --build -d <service>

# View logs for specific service
podman-compose logs -f order || docker-compose logs -f order

# Restart a service
make restart-service SERVICE=agent-logs  # (calls the underlying compose command)

# Complete cleanup (removes all data)
make compose-down && podman-compose down -v || docker-compose down -v
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