# AI Model Configuration

This directory contains configuration files for AI model parameters used across the project.

## Files

### model-params.yml

Defines optimal parameters for each AI model used in the system. These parameters are automatically loaded by `common-ai` and used by all agents.

**Structure:**

```yaml
# Default parameters (fallback when model not found)
default:
  temperature: 0.0      # Deterministic output
  top_k: 1              # Top-k sampling (most deterministic)
  max_tokens: 2000      # Maximum response length

# Model-specific configurations
models:
  model-name:tag:
    temperature: 0.0
    top_k: 1
    max_tokens: 2000
    context_size: 8192  # Optional: context window size
```

**Usage:**

The configuration is automatically loaded by `common-ai` when creating LLM instances:

```python
from common_ai import get_llm, get_model_params

# Get LLM with auto-loaded params from config
llm = get_llm(model="qwen3:0.6b")  # Uses params from model-params.yml

# Get params directly
params = get_model_params("mistral:7b")  # Returns: {temperature: 0.0, top_k: 1, ...}
```

**Behavior:**

1. **Exact match**: If the model name exactly matches a key in `models`, those parameters are used
2. **Prefix match**: If no exact match, tries matching by base name (e.g., `qwen3` matches `qwen3:0.6b`)
3. **Default fallback**: If no match found, uses `default` parameters and logs a warning

**Adding new models:**

```yaml
models:
  new-model:7b:
    temperature: 0.0
    top_k: 1
    max_tokens: 2000
    context_size: 16384
```

## Parameter Explanation

### temperature
- **Range**: 0.0 - 2.0
- **Default**: 0.0 (deterministic)
- **Purpose**: Controls randomness in model outputs
  - 0.0 = deterministic, always picks highest probability token
  - Higher values = more creative/random outputs

### top_k
- **Range**: 1 - vocabulary_size
- **Default**: 1 (most deterministic)
- **Purpose**: Limits sampling to top K most likely tokens
  - 1 = always pick the most likely token
  - Higher values = consider more alternatives

### max_tokens
- **Range**: 1 - model_max
- **Default**: 2000
- **Purpose**: Maximum length of generated response

### context_size (optional)
- **Purpose**: Document the model's context window size
- **Note**: This is informational; actual context is configured in Ollama/deployment

## Configuration in Docker

In Docker containers, the config is expected at:
- `/app/config/ai/model-params.yml`

Make sure to mount the config directory in docker-compose.yml:

```yaml
volumes:
  - ./config:/app/config:ro
```
