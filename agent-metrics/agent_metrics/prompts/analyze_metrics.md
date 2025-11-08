# Metrics Analysis Prompt (short)

You are an SRE analyzing metrics. Use the inputs and return a single JSON object (no extra text).

Inputs:
- Query: {query}
- Service: {service_name}
- Time range: {time_range}
- Error rate: {error_rate}%
- Request rate: {request_rate}
- Latency p95: {latency_p95}ms
- CPU: {cpu_usage}%
- Memory: {memory_mb}MB
- Anomalies (if any): {anomalies}

Return this JSON schema:

```
{{
  "health":"healthy|degraded|critical",
  "summary":"one-line",
  "metrics":{ "error_rate":num, "request_rate":num, "latency_p95":num, "cpu_usage":num, "memory_mb":num },
  "out_of_threshold":["error_rate","latency_p95"],
  "anomalies":["..."],
  "recommendations":["..."],
  "time_range_checked":"string",
  "insights":"one-line"
}}
```

Rules:
- If metrics for requested window are missing, set `anomalies` empty and `insights` to "insufficient metrics for requested window".
- Keep outputs concise and factual.

Return only the JSON object.
