# Setup Guide: ClawServant Configuration

## 1. Choose Your LLM Provider

ClawServant supports multiple LLM providers. Choose one or more:

| Provider | Cost | Speed | Privacy | Setup |
|----------|------|-------|---------|-------|
| **Bedrock** (AWS Claude) | $$ | Fast | Private (AWS) | Easy (IAM) |
| **Anthropic** (Direct API) | $$$  | Fast | Anthropic cloud | API key |
| **OpenAI** (GPT-4/Mini) | $$$  | Fast | OpenAI cloud | API key |
| **Ollama** (Local LLM) | Free | Variable | Your machine | Install + Run |

## 2. Create Your Credentials File

Create `credentials.json` in your working directory (where you'll run clawservant.py from):

```bash
# Go to your work directory
cd /path/to/my-researcher

# Copy example template
cp /path/to/clawservant/credentials.json.example ./credentials.json

# Edit credentials.json with your provider config
vim credentials.json
```

### Option A: AWS Bedrock (Recommended for mayur.ai)

```json
{
  "providers": [
    {
      "name": "bedrock",
      "enabled": true,
      "config": {
        "region": "us-east-1",
        "model_id": "us.anthropic.claude-haiku-4-5-20251001-v1:0"
      }
    }
  ],
  "fallback_order": ["bedrock", "anthropic", "openai", "ollama"]
}
```

**Setup:**
```bash
# Ensure AWS credentials are configured
aws configure
# Or set environment variables:
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
export AWS_REGION="us-east-1"
```

### Option B: Anthropic Direct API

```json
{
  "providers": [
    {
      "name": "anthropic",
      "enabled": true,
      "config": {
        "api_key": "sk-ant-...",
        "model": "claude-3-5-sonnet-20241022"
      }
    }
  ],
  "fallback_order": ["anthropic", "openai", "ollama"]
}
```

**Setup:**
```bash
# Get API key from https://console.anthropic.com
export ANTHROPIC_API_KEY="sk-ant-..."
```

### Option C: OpenAI API

```json
{
  "providers": [
    {
      "name": "openai",
      "enabled": true,
      "config": {
        "api_key": "sk-...",
        "model": "gpt-4o-mini"
      }
    }
  ],
  "fallback_order": ["openai"]
}
```

**Setup:**
```bash
# Get API key from https://platform.openai.com/api-keys
export OPENAI_API_KEY="sk-..."
```

### Option D: Local Ollama

```json
{
  "providers": [
    {
      "name": "ollama",
      "enabled": true,
      "config": {
        "base_url": "http://localhost:11434",
        "model": "llama2"
      }
    }
  ],
  "fallback_order": ["ollama"]
}
```

**Setup:**
```bash
# Install Ollama: https://ollama.ai
# Start Ollama server: ollama serve
# Pull a model: ollama pull llama2
```

### Option E: Multiple Providers (Fallback)

```json
{
  "providers": [
    {
      "name": "bedrock",
      "enabled": true,
      "config": {
        "region": "us-east-1",
        "model_id": "us.anthropic.claude-haiku-4-5-20251001-v1:0"
      }
    },
    {
      "name": "anthropic",
      "enabled": true,
      "config": {
        "model": "claude-3-5-sonnet-20241022"
      }
    },
    {
      "name": "openai",
      "enabled": true,
      "config": {
        "model": "gpt-4o-mini"
      }
    }
  ],
  "fallback_order": ["bedrock", "anthropic", "openai", "ollama"]
}
```

ClawServant tries providers in order. If Bedrock is unavailable, it falls back to Anthropic, then OpenAI, etc.

## 3. Verify Setup

```bash
# Make sure you're in your work directory
cd /path/to/my-researcher

# Check provider status
python3 /path/to/clawservant/clawservant.py --status

# Expected output:
# === LLM Provider Status ===
# Active provider: None
# Available providers: ['bedrock']
# Credentials file: /path/to/my-researcher/credentials.json
```

## 4. Drop Your First Task

```bash
# You're already in your work directory, so create a task file here
cat > tasks/my-task.md << 'EOF'
# My First Task

Summarize the history of AI from 2020-2026 in 500 words.
EOF

# Start ClawServant (point to the script, cwd provides work files)
python3 /path/to/clawservant/clawservant.py --continuous

# Watch it process the task automatically
# Results saved to: results/task_*.json
```

## 5. Configuration Details

### Credentials File Location

Default: `credentials.json` in the **current working directory** (cwd)

This means you must run the script from the directory where `credentials.json` lives:
```bash
cd /path/to/my-researcher
python3 /path/to/clawservant/clawservant.py --task "Your task"
```

Override with environment variable:
```bash
export CLAWSERVANT_WORK_DIR=/custom/work/path
python3 clawservant.py --task "Your task"
```

Or command-line flag (if added):
```bash
python3 clawservant.py --credentials /path/to/credentials.json --task "Your task"
```

### Work Directory Location

Default: Current working directory (cwd) — wherever you run the script from

This enables true portability:
- Clone clawservant repo to `/tools/clawservant/`
- Create work dir `/work/researcher1/` with its own credentials.json
- Run: `cd /work/researcher1 && python3 /tools/clawservant/clawservant.py`
- Create work dir `/work/researcher2/` with its own credentials.json
- Run: `cd /work/researcher2 && python3 /tools/clawservant/clawservant.py`
- Both instances run simultaneously without interference

Override with environment variable:
```bash
export CLAWSERVANT_WORK_DIR=/custom/work/path
python3 clawservant.py --continuous
```

### Provider Fallback Order

ClawServant tries providers in the order listed in `fallback_order`:

```json
{
  "fallback_order": ["bedrock", "anthropic", "openai", "ollama"]
}
```

If `bedrock` fails (missing credentials, rate limit, etc.), it tries `anthropic`, then `openai`, etc.

### Installation Structure

```
/tools/clawservant/          # Repo clone (shared code)
├── clawservant.py
├── providers.py
├── start.sh
├── credentials.json.example
└── README.md

/work/researcher1/           # Instance 1 (work dir)
├── credentials.json
├── memory.jsonl
├── state.json
├── tasks/
├── results/
├── brain/
├── personality/
└── rules/

/work/researcher2/           # Instance 2 (work dir)
├── credentials.json
├── memory.jsonl
├── state.json
├── tasks/
├── results/
├── brain/
├── personality/
└── rules/
```

All instances use the same code, different work directories.

## 6. Common Issues

### "No LLM providers available"

**Problem:** No credentials configured.

**Solution:**
1. Create `~/.clawservant/credentials.json`
2. Check provider setup (see options above)
3. Verify environment variables or API keys

```bash
# Check AWS
aws s3 ls

# Check Anthropic
echo $ANTHROPIC_API_KEY

# Check OpenAI
echo $OPENAI_API_KEY
```

### "Bedrock on-demand throughput isn't supported"

**Problem:** Using direct model ID instead of inference profile.

**Solution:** Use inference profile format:
```json
{
  "model_id": "us.anthropic.claude-haiku-4-5-20251001-v1:0"
}
```

### "Anthropic API call failed"

**Problem:** Missing or invalid API key.

**Solution:**
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
python3 clawservant.py --status
```

### "Ollama connection refused"

**Problem:** Ollama server not running.

**Solution:**
```bash
# Start Ollama (in another terminal)
ollama serve

# Pull a model
ollama pull llama2
```

## 7. Running ClawServant

### Single Task

```bash
python3 clawservant.py --task "Your task here"
```

### Continuous Thinking (Background)

```bash
# Run in background
nohup python3 clawservant.py --continuous > clawservant.log 2>&1 &

# Or with systemd
# See: INTEGRATION.md (systemd setup)
```

### Check Status

```bash
python3 clawservant.py --status
```

### View Memory

```bash
python3 clawservant.py --memory
```

## 8. Advanced: Custom Providers

Want to add support for a new LLM provider (e.g., Groq, Replicate, vLLM)?

Edit `providers.py` and add a new class:

```python
class YourProviderName(LLMProvider):
    def __init__(self, config):
        self.config = config
        self.api_key = config.get("api_key") or os.environ.get("YOUR_API_KEY")
    
    def is_available(self) -> bool:
        # Check if credentials exist
        return bool(self.api_key)
    
    async def call(self, system_prompt: str, user_prompt: str, max_tokens: int = 500) -> str:
        # Call your API
        # Return response text
        pass

# Register in PROVIDERS dict
PROVIDERS["yourprovider"] = YourProviderName
```

Then add to `credentials.json`:
```json
{
  "providers": [
    {
      "name": "yourprovider",
      "enabled": true,
      "config": {"api_key": "..."}
    }
  ]
}
```

---

**Next:** Read [README.md](./README.md) for usage, or [WHY.md](./WHY.md) for philosophy.