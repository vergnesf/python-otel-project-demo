# Development Setup & Best Practices

## Local Dependencies Management

This project uses `uv` with local path-based dependencies. To avoid caching issues during development, all local packages should be installed in **editable mode**.

### Configuration

In any `pyproject.toml` that depends on local packages:

```toml
[tool.uv.sources]
common-ai = { path = "../common-ai", editable = true }
```

The `editable = true` flag ensures:
- ✅ Code changes are **immediately reflected** without rebuilding
- ✅ No stale wheel caches
- ✅ Proper module reloading during development

### Setup Instructions

```bash
# Install/sync dependencies (uv handles editable installs automatically)
cd agent-orchestrator
uv sync

# Verify editable installation
uv run python -c "import common_ai; print(common_ai.__file__)"
# Should point to ../common-ai/common_ai/__init__.py
```

### Troubleshooting

If you see import errors after modifying a local package:

```bash
# Clear caches and rebuild
rm -rf .venv uv.lock __pycache__
uv sync
```

### Why This Matters

Without `editable = true`:
- ❌ Modifications to `common-ai/` won't be visible in dependent packages
- ❌ Need manual reinstallation after every change
- ❌ Wastes development time with confusing "stale module" errors

With `editable = true`:
- ✅ Direct symlinks to source files
- ✅ Instant reflection of changes
- ✅ Standard Python development workflow

---

## All Local Packages (Using Editable Mode)

The following packages should **always** be in editable mode when developing:

- `common-ai` - Shared AI utilities (required by all agents)
- `common-models` - Shared model definitions (required by services)

Update `pyproject.toml` in dependent packages:

```toml
[tool.uv.sources]
common-ai = { path = "../common-ai", editable = true }
common-models = { path = "../common-models", editable = true }
```
