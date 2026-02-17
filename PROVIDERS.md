# Provider API Reference

## How Each Provider Works

ClawServant abstracts LLM providers so you can swap them without code changes. Each provider handles its API differently:

### Bedrock (AWS)

**API:** AWS Bedrock Runtime `converse()` API  
**Authentication:** AWS credentials (IAM, not API keys)  
**Model Format:** Inference profile (e.g., `us.anthropic.claude-haiku-4-5-20251001-v1:0`)

**Key Details:**
- Uses `converse()` method (not raw Invoke API)
- Supports only `temperature` (not `temperature + top_p` together)
- `maxTokens` parameter (camelCase)
- System prompt in separate `system` array
- Messages in standard format

**Config Example:**
```json
{
  "name": "bedrock",
  "config": {
    "region": "us-east-1",
    "model_id": "us.anthropic.claude-haiku-4-5-20251001-v1:0"
  }
}
```

**Why Bedrock differs:**
- Bedrock doesn't support `temperature + top_p` together (ValidationException)
- Must use inference profiles, not direct model IDs (on-demand throughput error)
- Different message format than other APIs

---

### Anthropic (Direct API)

**API:** Anthropic `messages` API  
**Authentication:** API key (`ANTHROPIC_API_KEY` environment variable)  
**Model:** Model slug (e.g., `claude-3-5-sonnet-20241022`)

**Key Details:**
- Uses `messages.create()` method
- Supports `max_tokens` parameter
- System prompt as string parameter
- Messages in standard format
- Supports both `temperature` and `top_p`

**Config Example:**
```json
{
  "name": "anthropic",
  "config": {
    "api_key": "sk-ant-...",
    "model": "claude-3-5-sonnet-20241022"
  }
}
```

**Why Anthropic is cleaner:**
- Direct API (no AWS/GCP wrapper)
- Supports multiple temperature/sampling params
- Native support for system prompts

---

### OpenAI (Direct API)

**API:** OpenAI Chat Completions  
**Authentication:** API key (`OPENAI_API_KEY` environment variable)  
**Model:** Model slug (e.g., `gpt-4o-mini`)

**Key Details:**
- Uses `chat.completions.create()` method
- `max_tokens` parameter
- System prompt in `messages` array (role="system")
- Supports `temperature`, `top_p`, other sampling params
- Different message structure (no separate system field)

**Config Example:**
```json
{
  "name": "openai",
  "config": {
    "api_key": "sk-...",
    "model": "gpt-4o-mini"
  }
}
```

**Why OpenAI differs:**
- System prompt is part of `messages` (role="system"), not separate
- Message structure different from Anthropic/Bedrock
- Different parameter names/formats

---

### Ollama (Local)

**API:** HTTP REST (local)  
**Authentication:** None (runs on your machine)  
**Model:** Local model name (e.g., `llama2`, `mistral`)

**Key Details:**
- HTTP POST to `/api/generate`
- System prompt concatenated with user prompt (simple format)
- `num_predict` for token limit
- No temperature/sampling in basic call
- Runs on `http://localhost:11434` by default

**Config Example:**
```json
{
  "name": "ollama",
  "config": {
    "base_url": "http://localhost:11434",
    "model": "llama2"
  }
}
```

**Why Ollama is simple:**
- Local, no API keys
- Simpler API (just HTTP POST)
- Free (runs on your hardware)

---

## API Call Comparison

| Aspect | Bedrock | Anthropic | OpenAI | Ollama |
|--------|---------|-----------|--------|--------|
| **Method** | `converse()` | `messages.create()` | `chat.completions.create()` | HTTP POST |
| **Temperature + TopP** | ❌ Just temp | ✅ Both | ✅ Both | ⚠️ Limited |
| **System Prompt** | Separate array | String param | Part of messages | Concatenated |
| **Model Format** | Inference profile | Model slug | Model slug | Local name |
| **Auth** | AWS credentials | API key | API key | None |
| **Cost** | Per 1M tokens | Per 1M tokens | Per 1M tokens | Free |
| **Privacy** | AWS region | Anthropic cloud | OpenAI cloud | Your machine |

---

## Known API Quirks (And How We Handle Them)

### ✅ Fixed: Bedrock temperature + top_p

**Problem:** Bedrock doesn't support both `temperature` and `top_p` simultaneously.

**Solution:** ClawServant only uses `temperature` for Bedrock.

```python
# Bedrock
inferenceConfig={
    "maxTokens": 500,
    "temperature": 1,  # Only this, not top_p
}

# Anthropic/OpenAI (could support both)
# But ClawServant keeps it simple: temperature only for all
```

### ✅ Fixed: Bedrock model ID format

**Problem:** Direct model IDs fail with "on-demand throughput isn't supported" error.

**Solution:** Use inference profiles (with region prefix).

```python
# ❌ Wrong
"model_id": "anthropic.claude-3-5-haiku-20241022-v1:0"

# ✅ Right
"model_id": "us.anthropic.claude-haiku-4-5-20251001-v1:0"
```

### ✅ Fixed: OpenAI message format

**Problem:** OpenAI system prompt must be in `messages` array, not separate.

**Solution:** ClawServant handles it in the OpenAI provider.

```python
# ❌ Would fail
messages=[
    {"role": "user", "content": user_prompt}
],
system=system_prompt

# ✅ What OpenAI expects
messages=[
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": user_prompt}
]
```

### ✅ Fixed: Bedrock message content format

**Problem:** Bedrock's `converse()` requires specific content format. Early version had `"type": "text"` fields that failed.

**Solution:** Content blocks are just `{"text": "..."}`, no type field.

```python
# ❌ Wrong (Bedrock rejects this)
"content": [{"type": "text", "text": "..."}]

# ✅ Right
"content": [{"text": "..."}]
```

---

## Adding a Custom Provider

Want to add a new provider? Extend the base class:

```python
class MyProviderName(LLMProvider):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_key = config.get("api_key") or os.environ.get("MY_API_KEY")
    
    def is_available(self) -> bool:
        """Check if credentials exist."""
        return bool(self.api_key)
    
    async def call(self, system_prompt: str, user_prompt: str, max_tokens: int = 500) -> str:
        """Call your API."""
        # Implement your API call here
        # Return response text
        pass

# Register it
PROVIDERS["myprovider"] = MyProviderName
```

Then add to `credentials.json`:
```json
{
  "providers": [
    {
      "name": "myprovider",
      "enabled": true,
      "config": {"api_key": "..."}
    }
  ]
}
```

---

## Testing Providers

```bash
# Check which providers are available
python3 clawservant.py --status

# Single task with specific provider
python3 clawservant.py --task "Test task"

# If multiple configured, ClawServant tries fallback order

# Check logs for which provider was used
tail ~/.clawservant/workspace/memory.jsonl | grep -i "bedrock\|anthropic\|openai"
```

---

**Key Takeaway:** Each provider has different API quirks. ClawServant abstracts them so you can swap providers without changing code. But if something breaks, check this doc first.