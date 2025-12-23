# Troubleshooting Guide

> NOTE: A condensed troubleshooting handbook is available at `docs/handbook/troubleshooting.md`.
> Use it for quick diagnostics. This file keeps the full reference and extended tips.

## Common Issues

### Services Not Sending Telemetry

**Symptoms**: No logs, metrics, or traces visible in Grafana

**Solutions**:
1. Check OTEL Collector is running:
   ```bash
   docker-compose ps otel-gateway
   ```

2. Verify endpoint configuration in service environment:
   ```bash
   docker-compose config | grep OTEL_EXPORTER_OTLP_ENDPOINT
   ```

3. Check collector logs:
   ```bash
   docker-compose logs -f otel-gateway
   ```

4. Verify service is auto-instrumented:
   ```bash
   docker-compose exec order pip list | grep opentelemetry
   ```

### MCP Server Connection Errors

**Symptoms**: Agents return errors or timeouts when querying

**Solutions**:
1. Verify `GRAFANA_SERVICE_ACCOUNT_TOKEN` is set:
   ```bash
   grep GRAFANA_SERVICE_ACCOUNT_TOKEN .env
   ```

2. Check token has proper permissions in Grafana:
   - Go to Configuration → Service accounts
   - Verify the service account has Editor or Viewer role

3. Ensure MCP service is running:
   ```bash
   docker-compose ps grafana-mcp
   ```

4. Review MCP logs for errors:
   ```bash
   docker-compose logs -f grafana-mcp
   ```

5. Test MCP endpoint directly:
   ```bash
   curl http://localhost:8000/health
   ```

### Agent Query Failures

**Symptoms**: Agents return empty results or errors

**Solutions**:
1. Verify Grafana datasources are configured:
   - Open http://localhost:3000
   - Go to Configuration → Data sources
   - Check that Loki, Mimir, and Tempo are configured and working

2. Check if data exists in datasources:
   ```bash
   # Query Loki directly
   curl 'http://localhost:3100/loki/api/v1/query?query={service_name="varlogs"}'

   # Query Mimir directly
   curl 'http://localhost:9009/prometheus/api/v1/query?query=up'

   # Check Tempo
   curl 'http://localhost:3200/api/search'
   ```

3. Test queries directly in Grafana Explore UI:
   - Open http://localhost:3000/explore
   - Select datasource (Loki/Mimir/Tempo)
   - Run a test query

4. Review agent logs for detailed error messages:
   ```bash
   docker-compose logs -f agent-logs
   docker-compose logs -f agent-metrics
   docker-compose logs -f agent-traces
   ```

### Common Module Not Found

**Symptoms**: 
- `ModuleNotFoundError: No module named 'common_models'` in business services
- `ModuleNotFoundError: No module named 'common_ai'` in AI agents

**Solutions**:

**For Business Services** (order, stock, customer, etc.):
```bash
cd order/
uv pip install -e ../common-models/
uv run uvicorn order.main:app --reload
```

**For AI Agents** (agent-logs, agent-orchestrator, etc.):
```bash
cd agent-logs/
uv pip install -e ../common-ai/
uv run uvicorn agent_logs.main:app --reload
```

**Using PYTHONPATH**:
```bash
export PYTHONPATH=/path/to/project:$PYTHONPATH
cd agent-logs/
uv run uvicorn agent_logs.main:app --reload
```

**Using Docker** (recommended for development):
```bash
docker-compose up agent-logs
```

### Docker Build Failures

**Symptoms**: Docker build fails with dependency errors

**Solutions**:
1. Clear Docker cache and rebuild:
   ```bash
   docker-compose build --no-cache
   ```

2. Check if Python 3.14 image is available:
   ```bash
   docker pull python:3.14-slim
   ```

   If not available, temporarily revert to Python 3.13 in Dockerfiles and pyproject.toml

3. Verify shared modules are copied correctly in Dockerfile:
   ```dockerfile
   # For business services
   COPY common-models/pyproject.toml /app/common-models/pyproject.toml
   COPY common-models/common_models/ /app/common-models/common_models
   
   # For AI agents
   COPY common-ai/pyproject.toml /app/common-ai/pyproject.toml
   COPY common-ai/common_ai/ /app/common-ai/common_ai
   ```

4. Check modules are installed in builder stage:
   ```dockerfile
   # Business services
   RUN uv pip install -e /app/common-models
   
   # AI agents
   RUN uv pip install -e /app/common-ai
   ```

### Kafka Connection Issues

**Symptoms**: Services can't connect to Kafka, messages not flowing

**Solutions**:
1. Check Kafka is running:
   ```bash
   docker-compose ps broker
   ```

2. View Kafka logs:
   ```bash
   docker-compose logs -f broker
   ```

3. Test Kafka connectivity:
   ```bash
   # List topics
   docker-compose exec broker kafka-topics --list --bootstrap-server localhost:9092

   # Check consumer groups
   docker-compose exec broker kafka-consumer-groups --list --bootstrap-server localhost:9092
   ```

4. Verify KAFKA advertised listeners in docker-compose.yml:
   ```yaml
   KAFKA_ADVERTISED_LISTENERS: "PLAINTEXT://broker:29092,PLAINTEXT_HOST://localhost:9092"
   ```

### Database Connection Errors

**Symptoms**: Order or Stock services can't connect to PostgreSQL

**Solutions**:
1. Check PostgreSQL is running:
   ```bash
   docker-compose ps postgres
   ```

2. View PostgreSQL logs:
   ```bash
   docker-compose logs -f postgres
   ```

3. Test database connection:
   ```bash
   docker-compose exec postgres psql -U postgres -c '\l'
   ```

4. Check database credentials in docker-compose.yml match service configuration

### High Memory Usage

**Symptoms**: System running slow, containers being killed

**Solutions**:
1. Check container resource usage:
   ```bash
   docker stats
   ```

2. Reduce resource limits in docker-compose.yml:
   ```yaml
   deploy:
     resources:
       limits:
         memory: 512M  # Reduce from 1G
   ```

3. Stop unnecessary services:
   ```bash
   # Run only core services
   docker-compose up -d grafana loki mimir tempo otel-gateway broker postgres
   ```

4. Increase Docker Desktop memory limit (if using Docker Desktop)

### Port Conflicts

**Symptoms**: `bind: address already in use`

**Solutions**:
1. Check what's using the port:
   ```bash
   sudo lsof -i :3000  # Replace with conflicting port
   ```

2. Stop the conflicting service or change port in docker-compose.yml:
   ```yaml
   ports:
     - "3001:3000"  # Change host port to 3001
   ```

### Agent Web UI Not Loading

**Symptoms**: http://localhost:3002 not accessible

**Solutions**:
1. Check agent-ui container is running:
   ```bash
   docker-compose ps agent-ui
   ```

2. View logs:
   ```bash
   docker-compose logs -f agent-ui
   ```

3. Verify port mapping:
   ```bash
   docker-compose port agent-ui 3000
   ```

4. Check if orchestrator is reachable from UI:
   ```bash
   docker-compose exec agent-ui curl http://agent-orchestrator:8001/health
   ```

## Debugging Tips

### Enable Debug Logging

Add to service environment in docker-compose.yml:

```yaml
environment:
  - LOG_LEVEL=debug
  - OTEL_LOG_LEVEL=debug
```

### View All Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f order

# Last 100 lines
docker-compose logs --tail=100 agent-logs

# Follow logs for multiple services
docker-compose logs -f agent-logs agent-metrics agent-traces
```

### Inspect Container

```bash
# Get shell in container
docker-compose exec order bash

# Check environment variables
docker-compose exec order env | grep OTEL

# Check network connectivity
docker-compose exec order ping -c 3 otel-gateway
```

### Restart Individual Services

```bash
# Restart single service
docker-compose restart order

# Recreate service (rebuilds if needed)
docker-compose up -d --force-recreate order
```

### Clean Slate

Complete reset of the environment:

```bash
# Stop everything
docker-compose down

# Remove volumes (WARNING: deletes all data)
docker-compose down -v

# Remove images
docker-compose down -v --rmi all

# Rebuild from scratch
docker-compose up --build -d
```

## Getting Help

If you're still stuck:

1. Check existing issues on GitHub
2. Enable debug logging and collect logs
3. Create a minimal reproduction case
4. Open an issue with:
   - Docker and Docker Compose versions
   - Operating system
   - Error messages and logs
   - Steps to reproduce
