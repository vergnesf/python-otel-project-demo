# Agent Routing Prompt

**Task**: Decide which observability agent(s) to call based on the user query.

**Query**: {query}

**Available Agents**:
- **logs**: For errors, exceptions, error messages, log entries
- **metrics**: For CPU, memory, latency, throughput, rates, performance numbers
- **traces**: For slow requests, bottlenecks, request flows, distributed tracing

**Instructions**:
- Choose one or more agents: "logs", "metrics", "traces"
- Be specific and selective
- Only choose agents that are directly relevant
- Prefer fewer agents when possible

**Response format**: JSON only, no markdown
```json
{{
  "agents": ["logs"],
  "reason": "Short reason why"
}}
```
