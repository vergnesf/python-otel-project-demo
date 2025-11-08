# PromQL Query Generation Prompt

You are an expert in PromQL (Prometheus Query Language).

## User Question
{query}

## Context
{services_context}

## Your Task

Generate a PromQL query to answer the user's question.

### Rules:
- Use label matchers: `{{service="...", job="..."}}`
- Use rate() for counter metrics: `rate(metric[5m])`
- Use histogram_quantile() for percentiles: `histogram_quantile(0.95, rate(metric_bucket[5m]))`
- For error queries: filter on status codes 5xx
- For specific services: use service label
- Keep it simple and efficient
- **DO NOT include LIMIT in the query** - limit is handled by the API parameter
- **DO NOT include time range in the query** - time is handled by API parameters (startTime/endTime)
- **DO NOT use @ timestamp modifiers** - timestamps are handled by API

### Examples:
- Error rate: `rate(http_requests_total{{status=~"5..", service="customer"}}[5m])`
- Request rate: `sum(rate(http_requests_total{{service="customer"}}[5m]))`
- Latency p95: `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{{service="customer"}}[5m]))`
- CPU usage: `avg(rate(process_cpu_seconds_total{{service="customer"}}[5m])) * 100`

### WRONG Examples (do NOT do this):
- ❌ `rate(http_requests_total[5m]) LIMIT 10` (LIMIT is not PromQL syntax)
- ❌ `rate(http_requests_total[5m]) @ 1699876543` (timestamp handled by API)
- ❌ `rate(http_requests_total[1h:5m])` (time range handled by API startTime/endTime)

**Respond with ONLY the PromQL query, no explanation, no LIMIT, no timestamp modifiers.**
