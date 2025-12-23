````markdown
# Documentation consolidation plan

This file proposes a consolidation of the `docs/` folder to reduce duplication, keep content up-to-date, and make it easier for contributors to find canonical information.

Goals
- Remove duplicated guidance across files (MCP setup, orchestration, prompts)
- Make operational steps (run, debug, env vars) concise and central
- Keep architecture and strategy documents focused on high-level decisions
- Provide a single entrypoint for contributors and a clear TOC

Proposed target structure

```
docs/
├── README.md                # This file: consolidation plan + how to contribute
├── handbook/                # Short operational/HowTo guides (run/debug/config)
│   ├── development.md       # Local development (condensed)
│   ├── configuration.md     # Environment and .env examples (condensed)
│   └── troubleshooting.md   # Troubleshooting steps (condensed)
├── architecture.md          # High-level architecture (keep)
├── agents.md                # Agentic network overview (keep)
├── prompts.md               # Prompts & prompt-loading (merge ai-prompts-architecture)
├── strategy.md              # Agentic MCP strategy (merge agentic-mcp-strategy)
└── security.md              # Docker/security notes (keep)
```

Rationale and mapping
- `development.md`, `configuration.md`, `troubleshooting.md` currently contain overlapping procedural steps. Move common operational content to `handbook/` and keep `architecture.md` and `agents.md` conceptual only.
- `ai-prompts-architecture.md` and parts of `agentic-mcp-strategy.md` explain prompts and prompt-loading. Consolidate into `prompts.md` to avoid duplication.
- Keep `strategy.md` for progressive roadmap (phases) and enrichment plans; remove copy/paste technical snippets already present in code.

Practical next steps (I can apply these if you want)
1. Create `docs/handbook/` and move trimmed versions of `development.md`, `configuration.md`, `troubleshooting.md` into it.
2. Create `docs/prompts.md` by merging `ai-prompts-architecture.md` and the prompt-related sections of `agentic-mcp-strategy.md` (remove duplicates).
3. Create `docs/strategy.md` containing the roadmap and phase list (trim examples/large code blocks).
4. Update internal links in `docs/` and root `README.md` to point to new files.
5. Optionally: run a spellcheck/format pass on all Markdown files.

Acceptance criteria
- No duplicated step-by-step instructions across more than one handbook file.
- Architecture/strategy docs are conceptual and do not contain operational commands.
- `docs/handbook/*` contains all `curl/docker-compose` commands and config examples.

If you want, I can perform steps 1–4 automatically and open a branch with the changes. Tell me which steps to run now.

````
