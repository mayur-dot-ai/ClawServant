# Tool Calling Format (V2)

**CRITICAL: Tool format has changed.**

## New Format: XML Delimiters

To call a tool, wrap JSON in `<tool>...</tool>` tags:

```
<tool>{"tool": "tool_name", "params": {"param": "value"}}</tool>
```

## Why This Works Better

- **Reliable parsing** — No more regex failures
- **Multi-tool support** — Call multiple tools in one response
- **Tool chaining** — read → analyze → post in ONE iteration

## Examples

### Single Tool Call

```
<tool>{"tool": "file-io", "params": {"action": "read", "path": "README.md"}}</tool>
```

### Multiple Tool Calls

```
First, let me read the issue:
<tool>{"tool": "shell-exec", "params": {"command": "python3 /home/ec2-user/github-mcp/github-wrapper.py issue-get mayur-dot-ai ClawServant 4"}}</tool>

Then analyze and post a comment:
<tool>{"tool": "shell-exec", "params": {"command": "python3 /home/ec2-user/github-mcp/github-wrapper.py issue-comment mayur-dot-ai ClawServant 4 \"Analysis complete\""}}</tool>
```

## What Happens

1. You output response with `<tool>` tags
2. Framework extracts ALL tool calls
3. Executes them sequentially
4. Feeds results back to you
5. You can request MORE tools or provide final answer

## Iteration Behavior

Within ONE `think()` call, you can iterate up to **10 times** calling tools. This means:

- Read a file → analyze → write result → done (all in one go)
- No need to stop after each tool
- Framework handles the loop for you

## Old Format (DEPRECATED)

❌ **This no longer works:**
```json
{"tool": "file-io", "params": {...}}
```

The regex-based detector has been removed. Always use `<tool>` tags.

## Migration

If you see old JSON-only tool calls in memory or brain files, they won't work anymore. Update them to use `<tool>` tags.