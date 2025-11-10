````markdown
# Configuration Handbook (condensed)

## Environment
- Copy example: `cp .env.example .env`
- Important vars: `GRAFANA_SERVICE_ACCOUNT_TOKEN`, `LLM_BASE_URL`, `ERROR_RATE`

## Core images
- `IMG_GRAFANA`, `IMG_GRAFANA_MCP`, `IMG_LOKI`, `IMG_MIMIR`, `IMG_TEMPO`

## MCP Service Account
1. Start stack: `docker-compose up -d`
2. Open Grafana: `http://localhost:3000` (admin/admin)
3. Create service account → generate token
4. Add token to `.env`: `GRAFANA_SERVICE_ACCOUNT_TOKEN=...`
5. Restart MCP: `docker-compose restart grafana-mcp`

## Datasources
- `config/grafana/datasources/default.yaml` contains Loki/Mimir/Tempo entries

````
