# Brain Files

Drop `.md` or `.txt` files here. ClawServant reads them and incorporates knowledge into its thinking.

**Examples of what to add:**

- `domain-knowledge.md` — Industry specifics, terminology, context
- `company-values.md` — Organizational principles and culture
- `coding-standards.md` — Technical guidelines and best practices
- `research-methodology.md` — How to approach research tasks
- `tone-guide.md` — Voice, style, communication preferences
- `guidelines.md` — General rules or constraints

**How it works:**
- ClawServant reads all files in this folder at startup
- Content is incorporated into the system prompt
- Your agent learns from these files without explicit instruction

**Example:**

```markdown
# Research Guidelines

When researching topics:
1. Seek multiple independent sources
2. Distinguish opinion from fact
3. Cite sources clearly
4. Flag uncertainty explicitly
5. Summarize findings in structured format
```

**Note:** Files are read at agent startup. Changes require restart.