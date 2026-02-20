# ClawServant V2 - Migration Guide

## What Changed

ClawServant V2 replaces fragile regex-based tool detection with reliable XML delimiter parsing and adds multi-tool execution within a single iteration.

### Before (V1)
```python
# LLM outputs JSON (maybe wrapped in markdown)
{"tool": "file-io", "params": {...}}

# Framework tries regex to find it
# Often fails due to markdown wrapping, escaping, etc.
# One tool call max per iteration
```

### After (V2)
```python
# LLM outputs XML-wrapped JSON
<tool>{"tool": "file-io", "params": {...}}</tool>

# Framework parses <tool>...</tool> reliably
# Multiple tools in one response
# Up to 10 tool iterations per think() call
```

## Key Improvements

1. **Reliable tool detection** — XML delimiters (`<tool>...</tool>`) instead of regex JSON hunting
2. **Multi-tool support** — Call multiple tools in one response
3. **Tool chaining** — read → analyze → post comment in ONE iteration
4. **Better prompts** — System prompt teaches LLM to use `<tool>` tags with examples

## Breaking Changes

### Tool Call Format

**Old (no longer works):**
```json
{"tool": "shell-exec", "params": {"command": "ls"}}
```

**New (required):**
```xml
<tool>{"tool": "shell-exec", "params": {"command": "ls"}}</tool>
```

### Migration Steps

1. **Update code** — Copy new `clawservant.py` to your servant directory
2. **Update brain files** — Add `tool_format_v2.md` to brain folder (see `docs/tool_format_v2.md`)
3. **Clear old memory** — Optional: remove `memory.jsonl` to start fresh (old tool calls in memory won't parse)

## Implementation Details

### New Methods

- `_extract_tool_calls(text)` — Parses `<tool>...</tool>` tags, returns list of tool call dicts
- `think(prompt, allow_tools=True, max_tool_iterations=10)` — Now loops internally until no more tool calls

### Multi-Tool Loop Logic

```python
while tool_iteration < max_tool_iterations:
    response = await llm.call(prompt)
    tool_calls = extract_tool_calls(response)
    
    if not tool_calls:
        return response  # Done
    
    # Execute all tools, build results prompt
    for tool in tool_calls:
        result = execute_tool(tool)
        
    prompt = f"Tool results: {results}\n\nContinue."
    tool_iteration += 1
```

This enables **read → think → write** in one `think()` call.

## Testing

### Quick Test

```bash
cd /path/to/clawservant
python3 clawservant.py --task "Read the file test.txt and tell me what's in it"
```

Expected: Servant uses `<tool>` format, reads file, analyzes content in ONE iteration.

### With Loop Mode

```bash
python3 clawservant.py --task "Read issue #4 and post a comment" --loop --max-iterations 5
```

Expected: Servant reads issue, generates comment, posts it — all autonomously.

## Rollback

If V2 causes issues, revert to V1:

```bash
git checkout <commit-before-v2> clawservant.py
```

But note: V1's regex detection is fundamentally unreliable. Better to fix V2 issues than rollback.

## Related Issues

- #1 — Tool call detection regex is inconsistent (FIXED in V2)
- #4 — Ralph Loop Improvements (IMPLEMENTED in V2)
- #3 — Integrate Ralph loop pattern (enhanced by V2)

## Questions?

Open an issue: https://github.com/mayur-dot-ai/ClawServant/issues