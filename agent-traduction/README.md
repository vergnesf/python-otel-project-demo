# Agent Traduction

Service for language detection and query translation to English.

## 📊 Features

- Language detection (French, English, etc.)
- Automatic translation to English
- REST API endpoints for integration
- Health monitoring endpoint

## 📦 Dependencies

- `httpx`: HTTP client for API calls
- `common-ai`: Shared AI utilities (MCP client, LLM config)

## 🐳 Podman Compose (rebuild a service)

To force the rebuild of a service without restarting the entire stack:

```bash
podman compose up -d --build --force-recreate --no-deps <service>
```

To ensure a rebuild without cache:

```bash
podman compose build --no-cache <service>
podman compose up -d --force-recreate --no-deps <service>
```
