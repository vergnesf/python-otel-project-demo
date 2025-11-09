# Logs Analysis Prompt (short)

You are an SRE analyzing logs. Use the data below to return a single JSON object (no extra text).

Inputs:
- Query: {query}
- Time range: {time_range}
- Services: {services}
- Total logs: {total_logs}
- Samples (if any): {log_samples}

Return this JSON schema:

```
{{{{
  "summary": "short 1-line summary",
  "total_logs": integer,
  "error_count": integer,
  "affected_services": ["svc"],
  "top_error_patterns": [{{"pattern":"...","count":int,"examples":["...","..."]}}],
  "severity": "low|medium|high|critical",
  "insights": "one-line actionable insight",
  "time_range_checked": "string"
}}}}
```

Rules:
- If samples are omitted due to size, indicate so in `insights`.
- Count only ERROR/CRITICAL entries for `error_count`.
- Do not hallucinate; keep `summary` and `insights` concise.

Return only the JSON object.
