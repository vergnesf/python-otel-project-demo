# Response Validation Prompt

**Task**: Review if the agent response properly answers the user query.

**User Query**: {query}

**Agent Response**: {response}

**Instructions**:
- Check if response is relevant to the query
- Check if response has concrete information
- Identify any missing information
- Be concise

**Response format**: JSON only
```json
{{
  "valid": true,
  "issues": ["list of issues if any"],
  "suggestion": "What could improve the response"
}}
```
