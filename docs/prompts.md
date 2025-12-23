````markdown
# Prompts (Agents)

This document consolidates how prompts are organized and used by the observability agents.

## Structure

Each agent keeps prompt templates in a `prompts/` directory. Typical files:

```
agent-logs/agent_logs/prompts/
  ├── system.md
  ├── build_logql.md
  └── analyze_logs.md

agent-metrics/agent_metrics/prompts/
  ├── system.md
  ├── build_promql.md
  └── analyze_metrics.md

agent-traces/agent_traces/prompts/
  ├── system.md
  ├── build_traceql.md
  └── analyze_traces.md

agent-orchestrator/agent_orchestrator/prompts/
  └── synthesize_analysis.md
```

## Pattern

All agents follow the same pattern:

1. Load prompt template from `prompts/` using a small helper `load_prompt(filename)`
2. Render template variables (`{query}`, `{time_range}`, `{logs_data}`, etc.)
3. Invoke LLM with the rendered prompt
4. Parse and return the content as structured JSON

Example loader (Python):

```python
PROMPTS_DIR = Path(__file__).parent / "prompts"

def load_prompt(filename: str) -> str:
    prompt_path = PROMPTS_DIR / filename
    return prompt_path.read_text() if prompt_path.exists() else ""
```

## Template variables

- `{query}`: User question
- `{time_range}`: Analysis time period
- `{services_context}`: Known service names or environment
- `{logs_data}`, `{metrics_data}`, `{traces_data}`: Raw payloads returned by MCP

## Best practices

- Keep prompts focused and short
- Include examples and expected output format
- Version prompts when testing (e.g., `build_logql.v2.md`)
- Validate variables exist before rendering to avoid KeyError

## Debugging

- Add logging when a prompt file is missing
- Provide a fallback non-LLM path to avoid breaking the agent

## Where to change prompts

- Edit files in each agent's `prompts/` folder and restart the corresponding agent

````
