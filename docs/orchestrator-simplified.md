# Orchestrator Agent - Simplified Architecture

## Overview

The Orchestrator Agent has been simplified to focus on **3 core AI-powered functionalities**, each designed with prompts optimized for Small Language Models (SLM).

## Design Philosophy

### Simplicity First
- Clear separation of concerns
- One responsibility per function
- Easy to understand and maintain

### AI-Driven with Fallbacks
- Primary: AI-powered decision making
- Fallback: Keyword-based logic when AI unavailable
- Robust error handling at each step

### Optimized for Small Language Models
- Short, direct prompts
- Strict JSON response format
- No unnecessary context
- Clear task definitions

## The 3 Core Functionalities

### 1. Language Detection & Translation 🌐

**Purpose**: Enable multi-language support by detecting and translating queries to English.

**How it works**:
```
User Query → Detect Language → Translate if needed → English Query
```

**Prompts**:
- `detect_language.md`: Returns "ENGLISH" or "NOT_ENGLISH"
- `translate_to_english.md`: Translates to English preserving meaning

**Example**:
```
Input:  "Montre-moi les erreurs récentes"
Detect: "NOT_ENGLISH"
Output: "Show me recent errors"
```

**Fallback**: Without LLM, assumes English and passes through.

**Benefits**:
- Supports French and other languages
- Transparent translation in response
- No user action needed

### 2. Intelligent Agent Routing 🎯

**Purpose**: Determine which specialized agent(s) to call based on the query content.

**How it works**:
```
English Query → Analyze Intent → Select Agents → [logs, metrics, traces]
```

**Agents**:
- **logs**: For errors, exceptions, log messages
- **metrics**: For CPU, memory, latency, performance metrics
- **traces**: For slow requests, bottlenecks, distributed tracing

**Prompt**:
- `route_agents.md`: Returns JSON with selected agents and reasoning

**Examples**:
```
"Show me errors"           → ["logs"]
"What is CPU usage?"       → ["metrics"]
"Which requests are slow?" → ["traces"]
"Show errors and CPU"      → ["logs", "metrics"]
```

**Fallback**: Keyword-based routing
- "error", "log" → logs agent
- "cpu", "memory", "latency" → metrics agent
- "slow", "trace", "bottleneck" → traces agent
- Default → logs agent

**Benefits**:
- Only calls necessary agents (reduces latency)
- Transparent reasoning in response
- Intelligent multi-agent selection

### 3. Response Validation ✅

**Purpose**: Verify that agent responses properly answer the user's question.

**How it works**:
```
Query + Agent Responses → Analyze Quality → Validation Result
```

**Prompt**:
- `validate_response.md`: Returns JSON with validation status, issues, suggestions

**Example**:
```json
{
  "validated": true,
  "issues": [],
  "suggestion": "Response is complete and relevant"
}
```

**Or if issues found**:
```json
{
  "validated": false,
  "issues": ["Missing concrete examples", "No error count provided"],
  "suggestion": "Add specific error examples and counts"
}
```

**Fallback**: Without LLM, returns unvalidated status.

**Benefits**:
- Quality control of responses
- Identifies missing information
- Provides improvement suggestions
- Builds user trust

## Complete Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    USER QUERY                                │
│            "Montre-moi les erreurs récentes"                 │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  STEP 1: LANGUAGE DETECTION & TRANSLATION                    │
│  ────────────────────────────────────────                    │
│  Prompt: detect_language.md                                  │
│  Result: "NOT_ENGLISH"                                       │
│                                                              │
│  Prompt: translate_to_english.md                             │
│  Result: "Show me recent errors"                             │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  STEP 2: INTELLIGENT ROUTING                                 │
│  ────────────────────────────                                │
│  Prompt: route_agents.md                                     │
│  Input: "Show me recent errors"                              │
│  Result: {                                                   │
│    "agents": ["logs"],                                       │
│    "reason": "Error query routed to logs agent"              │
│  }                                                           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  STEP 3: CALL SELECTED AGENTS (PARALLEL)                     │
│  ─────────────────────────────────────                       │
│  → Logs Agent: /analyze                                      │
│    Response: {                                               │
│      "analysis": "Found 5 errors in customer service",       │
│      "recommendations": ["Check DB connection"],             │
│      "data": {"error_count": 5}                             │
│    }                                                         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  STEP 4: RESPONSE VALIDATION                                 │
│  ────────────────────────────                                │
│  Prompt: validate_response.md                                │
│  Input: Query + Agent Responses                              │
│  Result: {                                                   │
│    "validated": true,                                        │
│    "issues": [],                                             │
│    "suggestion": "Response is complete"                      │
│  }                                                           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  FINAL RESPONSE                                              │
│  ──────────────                                              │
│  {                                                           │
│    "query": "Montre-moi les erreurs récentes",              │
│    "translated_query": "Show me recent errors",              │
│    "language": "non-english",                                │
│    "routing": {...},                                         │
│    "agent_responses": {...},                                 │
│    "validation": {...},                                      │
│    "summary": "...",                                         │
│    "recommendations": [...]                                  │
│  }                                                           │
└─────────────────────────────────────────────────────────────┘
```

## Prompt Design Principles

All prompts follow these principles for optimal SLM performance:

### 1. Brevity
- Short task description
- No unnecessary context
- Direct instructions

### 2. Clarity
- One clear task per prompt
- Unambiguous instructions
- Simple language

### 3. Structure
- Consistent format across prompts
- Clear sections (Task, Input, Output)
- Examples when helpful

### 4. Strict Output
- JSON format only
- No markdown code blocks in output
- No explanations or preambles

### Example Prompt Structure

```markdown
# Task Name

**Task**: [One sentence description]

**Input**: {variable}

**Instructions**:
- [Clear instruction 1]
- [Clear instruction 2]
- [Clear instruction 3]

**Response format**: JSON only
```json
{
  "field": "value"
}
```
```

## Benefits of This Architecture

### For Development
- ✅ Easy to test (unit tests for each function)
- ✅ Easy to debug (clear separation)
- ✅ Easy to modify (change one function without affecting others)

### For Users
- ✅ Multi-language support (automatic translation)
- ✅ Faster responses (only necessary agents called)
- ✅ Quality assurance (validation included)
- ✅ Transparency (all decisions visible)

### For Operations
- ✅ Robust (fallbacks when AI unavailable)
- ✅ Observable (detailed logging at each step)
- ✅ Scalable (parallel agent calls)
- ✅ Cost-effective (optimized prompts, selective routing)

## Performance Characteristics

### Latency
- Language detection: ~100-200ms (with SLM)
- Routing decision: ~100-200ms (with SLM)
- Agent calls: Parallel execution (same as single agent)
- Validation: ~100-200ms (with SLM)

**Total overhead**: ~300-600ms compared to direct agent call

### Token Usage
Each prompt is designed to minimize tokens:
- detect_language.md: ~50 tokens
- translate_to_english.md: ~60 tokens
- route_agents.md: ~100 tokens
- validate_response.md: ~120 tokens

**Total**: ~330 tokens per request (excluding agent responses)

### Cost Optimization
- Only selected agents are called (not all 3)
- Translation only if needed
- Validation optional (can be disabled)
- SLM-optimized (works with smaller models)

## Testing Strategy

### Unit Tests (22 tests)
- Mock LLM responses
- Test each function in isolation
- Fast execution (~1-2 seconds)
- No external dependencies

**Coverage**:
- Language detection: 5 tests
- Routing: 9 tests
- Validation: 5 tests
- End-to-end: 3 tests

### Integration Tests (4 tests)
- Real HTTP calls
- Real LLM inference
- Full workflow validation
- Slower execution (~30-60 seconds)

## Configuration Options

```bash
# Enable/disable features
LLM_EPHEMERAL_PER_CALL=false  # Fresh LLM instance per call
AGENT_CALL_TIMEOUT=60         # Timeout for agent calls

# Fallback behavior
# If LLM unavailable:
# - Language: Assumes English
# - Routing: Uses keywords
# - Validation: Returns unvalidated
```

## Future Enhancements

### Planned
- [ ] Caching for translations
- [ ] Performance metrics per step
- [ ] Support for more languages
- [ ] Streaming responses

### Under Consideration
- [ ] User feedback loop for validation
- [ ] A/B testing different prompts
- [ ] Adaptive routing based on response quality
- [ ] Custom routing rules per user

## Related Documentation

- [AI Prompts Architecture](./ai-prompts-architecture.md) - General prompt design
- [Prompts Simplified](./prompts-simplified.md) - Prompt optimization techniques
- [Agents](./agents.md) - Specialized agents overview
- [Architecture](./architecture.md) - Overall system architecture
