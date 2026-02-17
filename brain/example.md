# Brain Files - How to Use

## What Goes Here

Drop any `.md` or `.txt` file in this folder. ClawServant will:
1. Read all files in **alphabetical order**
2. Incorporate them into the agent's knowledge base
3. Include them in every LLM call

## Naming

Use descriptive names. Examples:
- `coding-standards.md` — Technical guidelines
- `domain-knowledge.md` — Industry terminology
- `research-methodology.md` — How to approach problems
- `company-values.md` — Organizational principles

Files are sorted alphabetically, so use prefixes if order matters:
- `01-foundations.md`
- `02-standards.md`
- `03-guidelines.md`

## Auto-Reload

Brain files auto-reload every cycle. Add, remove, or modify files without restarting ClawServant.