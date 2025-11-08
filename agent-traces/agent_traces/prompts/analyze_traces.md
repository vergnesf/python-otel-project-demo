# Traces Analysis Prompt (short)

You are an SRE analyzing distributed traces. Use the inputs and return a single JSON object (no extra text).

Inputs:
- Query: {query}
- Time range: {time_range}
- Total traces: {total_traces}
- Avg duration: {avg_duration}ms
- Slow traces: {slow_traces}
- Failed traces: {failed_traces}
- Services count: {services_count}
- Samples: {trace_samples}

Return this JSON schema:

```
{{
  "summary":"short 1-line summary",
  "total_traces":int,
  "slow_traces":int,
  "failed_traces":int,
  "affected_services":["svc"],
  "top_span_patterns":[{"pattern":"...","count":int,"examples":["...","..."]}],
  "severity":"low|medium|high|critical",
  "insights":"one-line",
  "time_range_checked":"string"
}}
```

Rules:
- If samples are removed for size, state that in `insights`.
- Use only provided data; keep outputs concise.

Return only the JSON object.
