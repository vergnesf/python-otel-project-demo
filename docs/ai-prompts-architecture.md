# AI Prompts Architecture

This document describes the organization of prompts for observability agents.

## 📂 Structure

Each agent has its own `prompts/` directory containing markdown files:

```
agent-logs/agent_logs/prompts/
├── build_logql.md      # LogQL query construction
└── analyze_logs.md     # Log analysis

agent-metrics/agent_metrics/prompts/
├── build_promql.md     # PromQL query construction
└── analyze_metrics.md  # Metrics analysis

agent-traces/agent_traces/prompts/
├── build_traceql.md    # TraceQL query construction
└── analyze_traces.md   # Trace analysis

agent-orchestrator/agent_orchestrator/prompts/
└── synthesize_analysis.md  # Multi-agent synthesis
```

## 🎯 Purpose by Agent

### Logs Agent
Analyzes application logs via Loki (MCP Grafana)

**build_logql.md**
- Generates optimized LogQL queries based on user question
- Example: "errors in customer" → `{service_name="customer"} |= "error"`

**analyze_logs.md**
- Intelligent analysis of retrieved logs
- Identifies error patterns, affected services, severity

### Metrics Agent
Analyzes system metrics via Mimir/Prometheus (MCP Grafana)

**build_promql.md**
- Generates PromQL queries to extract relevant metrics
- Example: "error rate" → `rate(http_requests_total{status=~"5.."}[5m])`

**analyze_metrics.md**
- Detects anomalies (error rate, latency, CPU, memory)
- Compares against thresholds and identifies performance issues

### Traces Agent
Analyzes distributed traces via Tempo (MCP Grafana)

**build_traceql.md**
- Generates TraceQL queries to filter traces
- Example: "slow traces" → `{duration > 500ms}`

**analyze_traces.md**
- Identifies bottlenecks and slow services
- Analyzes dependencies between services

### Orchestrator Agent
Coordinates the 3 specialized agents

**synthesize_analysis.md**
- Correlates signals from 3 agents (logs + metrics + traces)
- Provides Root Cause Analysis (RCA)
- Generates prioritized actionable recommendations

## 🔧 Technical Implementation

### Common Pattern

All agents use the same pattern:

```python
# 1. Loading prompts
PROMPTS_DIR = Path(__file__).parent / "prompts"

def load_prompt(filename: str) -> str:
    """Load a prompt template from a markdown file"""
    prompt_path = PROMPTS_DIR / filename
    if prompt_path.exists():
        return prompt_path.read_text()
    return ""

# 2. Building queries with LLM
async def _build_*ql_query_with_llm(self, query: str, context: dict) -> str:
    prompt_template = load_prompt("build_*.md")
    prompt = prompt_template.format(query=query, ...)
    response = self.llm.invoke(prompt)
    return response.content

# 3. Analysis with LLM
async def _analyze_*_with_llm(self, data: dict, query: str, ...) -> dict:
    prompt_template = load_prompt("analyze_*.md")
    prompt = prompt_template.format(query=query, data=data, ...)
    response = self.llm.invoke(prompt)
    return {"summary": response.content, ...}
```

### Template Variables

Markdown files use `{variable}` placeholders:

**build_*.md**
- `{query}`: User question
- `{services_context}`: Available/mentioned services

**analyze_*.md**
- `{query}`: User question
- `{time_range}`: Analysis time period
- `{*_data}`: Raw observability data
- Specific metrics (error_rate, latency, etc.)

**synthesize_analysis.md**
- `{query}`: User question
- `{logs_analysis}`, `{metrics_analysis}`, `{traces_analysis}`: Agent results
- `{*_confidence}`: Confidence level of each agent
- Quantitative data from each agent

## 📝 Best Practices

### Modifying Prompts

1. **Test locally**: Change the prompt and restart the agent
2. **Validate format**: Check that `{var}` variables exist
3. **Be concise**: Prompts should be clear and direct
4. **Include examples**: Always provide examples in prompts

### Adding New Prompts

1. Create the `.md` file in `{agent}/prompts/`
2. Define template variables
3. Add loading function in Python code
4. Test with different user inputs

### Debugging

If a prompt doesn't work:

1. Check logs: `logger.warning(f"Prompt file not found: {filename}")`
2. Test fallback: Code falls back to logic without LLM
3. Validate variables: KeyError indicates a missing variable

## 🚀 Evolution

Prompts are externalized to:

- **Facilitate tuning** without touching Python code
- **Enable versioning** of prompts (A/B testing)
- **Collaborate**: Data scientists modify prompts, SREs modify code
- **Reuse**: Prompts shared across observability projects

## 📊 Data Flow

```
User Query
    ↓
Orchestrator
    ├─→ Logs Agent
    │   ├─ build_logql.md → LogQL query → Loki (MCP)
    │   └─ analyze_logs.md → Analysis
    ├─→ Metrics Agent
    │   ├─ build_promql.md → PromQL query → Mimir (MCP)
    │   └─ analyze_metrics.md → Analysis
    └─→ Traces Agent
        ├─ build_traceql.md → TraceQL query → Tempo (MCP)
        └─ analyze_traces.md → Analysis
    ↓
synthesize_analysis.md → Unified Response
    ↓
User (via UI)
```

## 🔗 References

- **LangChain**: LLM framework used (`.llm.invoke()`)
- **MCP Grafana**: Client for Loki/Mimir/Tempo
- **Common AI**: Shared module (`get_llm()`, `MCPGrafanaClient`)
