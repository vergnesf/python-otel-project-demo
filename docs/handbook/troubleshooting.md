````markdown
# Troubleshooting Handbook (condensed)

Quick steps for common issues.

## MCP connection errors
- Check `GRAFANA_SERVICE_ACCOUNT_TOKEN` in `.env`
- Ensure `grafana-mcp` is running: `docker-compose ps grafana-mcp`
- Inspect logs: `docker-compose logs -f grafana-mcp`

## No telemetry in Grafana
- Check OTEL collector: `docker-compose ps otel-gateway`
- Verify `OTEL_EXPORTER_OTLP_ENDPOINT` env var
- Check Loki/Mimir/Tempo endpoints directly (curl)

## ModuleNotFound (common modules)
- Install editable: `uv pip install -e ../common-ai/` or `../common-models/`

## Docker build issues
- Rebuild without cache: `docker-compose build --no-cache`

## Useful commands
- Follow logs: `docker-compose logs -f agent-logs agent-metrics agent-traces`
- Restart a service: `docker-compose restart order`

````
