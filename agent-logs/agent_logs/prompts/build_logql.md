# LogQL Query Generation Prompt

You are an expert in LogQL (Loki Query Language).

## User Question
{query}

## Context
{services_context}

## Your Task

Generate a LogQL query to answer the user's question.

### Rules:
- Use label matchers: `{{service_name="...", job="..."}}`
- Use text filters: `|= "text"` for contains, `|~ "regex"` for regex
- For error queries: filter on "error", "fail", "exception" keywords
- For specific services: use service_name label
- Keep it simple and efficient
- **DO NOT include LIMIT in the query** - limit is handled by the API parameter
- **DO NOT include time range** - time is handled by API parameters

### Examples:
- Errors in all services: `{{job=~".+"}} |= "error"`
- Errors in customer service: `{{service_name="customer"}} |= "error"`
- Database errors: `{{job=~".+"}} |~ "(?i)(database|db).*error"`

### WRONG Examples (do NOT do this):
- ❌ `{{job=~".+"}} |= "error" LIMIT 5` (LIMIT is not LogQL syntax)
- ❌ `{{job=~".+"}} |= "error" limit 10` (limit is an API parameter, not query syntax)

**Respond with ONLY the LogQL query, no explanation, no LIMIT clause.**

