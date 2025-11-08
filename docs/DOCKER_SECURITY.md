# Docker Security Best Practices

This project implements several Docker security best practices to ensure containers run with minimal privileges.

## Non-Root User Execution

All application containers run as a non-root user `appuser` instead of root.

### Benefits

- **Reduced Attack Surface**: If a container is compromised, the attacker has limited privileges
- **Principle of Least Privilege**: Containers only have the permissions they need
- **Compliance**: Meets security requirements for many organizations
- **Better Isolation**: Prevents containers from modifying host system files

### Implementation

Each Dockerfile creates and uses a non-root user:

```dockerfile
# Create non-root user with home directory
RUN groupadd -r appuser && useradd -r -g appuser appuser -m

# ... copy files and dependencies ...

# Set ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser
```

### Verification

Check which user a container is running as:

```bash
docker exec stock whoami
# Output: appuser
```

## OS Updates

All runtime images include OS package updates to patch known vulnerabilities:

```dockerfile
# Update OS packages
RUN apt-get update && \
    apt-get upgrade -y && \
    rm -rf /var/lib/apt/lists/*
```

This ensures containers run with the latest security patches.

## Multi-Stage Builds

The project uses multi-stage Docker builds to:

- Keep runtime images minimal (smaller attack surface)
- Only include necessary dependencies in final image
- Separate build-time and runtime dependencies

```dockerfile
# Builder stage - install build tools
FROM python:3.14-slim AS builder
RUN pip install uv && uv sync

# Runtime stage - minimal image
FROM python:3.14-slim
COPY --from=builder /app/.venv /app/.venv
```

## Security Checklist

✅ **Non-root execution**: All containers run as `appuser`  
✅ **OS updates**: Latest security patches applied  
✅ **Minimal images**: Only necessary packages included  
✅ **No secrets in images**: Environment variables used for configuration  
✅ **Read-only where possible**: Application code owned by non-root user

## PostgreSQL Special Case

PostgreSQL 18+ requires a specific volume mount configuration:

```yaml
postgres:
  volumes:
    - postgres-data:/var/lib/postgresql  # Not /var/lib/postgresql/data
```

This is required for the new `pg_upgrade --link` feature and multi-version support.

## Testing Security

Verify security configurations:

```bash
# Check all containers run as non-root
docker compose ps --format "table {{.Name}}\t{{.Status}}" | while read name status; do
  [ "$name" = "NAME" ] && continue
  echo -n "$name: "
  docker exec $name whoami 2>/dev/null || echo "not running"
done

# Check no containers run as root
docker compose ps -q | xargs -I {} docker exec {} whoami | grep -c root
# Should output: 0
```

## Resources

- [Docker Security Best Practices](https://docs.docker.com/develop/security-best-practices/)
- [CIS Docker Benchmark](https://www.cisecurity.org/benchmark/docker)
- [OWASP Docker Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Docker_Security_Cheat_Sheet.html)
