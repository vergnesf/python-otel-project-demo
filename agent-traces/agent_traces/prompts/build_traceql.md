# TraceQL Query Generation

You are an expert in TraceQL.

## User Question
{query}

## Context
{services_context}

## Task

Generate a TraceQL query for **BUSINESS SERVICES ONLY**.

### Available Attributes

- `service.name` - Business service (customer, order, stock, supplier, ordercheck, ordermanagement, suppliercheck)
- `status` - Trace status (ok, error)
- `duration` - Trace duration (e.g., > 500ms)

**FORBIDDEN**: Do NOT use otel* fields.

### Query Patterns

**All traces from business services**:
```
{{{{service.name=~"customer|order|stock|supplier|ordercheck|ordermanagement|suppliercheck"}}}}
```

**Traces from one service**:
```
{{{{service.name="order"}}}}
```

**Error traces**:
```
{{{{service.name=~"customer|order|stock|supplier|ordercheck|ordermanagement|suppliercheck" && status=error}}}}
```

**Slow traces (> 500ms)**:
```
{{{{service.name=~"customer|order|stock|supplier|ordercheck|ordermanagement|suppliercheck" && duration > 500ms}}}}
```

**Slow errors from specific service**:
```
{{{{service.name="order" && status=error && duration > 300ms}}}}
```

### Rules

1. **Filter by business services**: Use `service.name=~"customer|order|stock|supplier|ordercheck|ordermanagement|suppliercheck"`
2. **Duration filter**: `duration > 500ms`
3. **Status filter**: `status=error` or `status=ok`
4. **Combine with &&**: `{service.name="order" && status=error}`
5. **NO LIMIT** in query

Return ONLY the TraceQL query. No explanation.
