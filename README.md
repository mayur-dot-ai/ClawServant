# ClawServant

> **An autonomous specialist agent for OpenClaw installations.**
>
> A lean, CLI-first AI employee that thinks continuously, learns from experience, and executes tasks — without web UI overhead.

## What is ClawServant?

ClawServant is a pure-Python specialist agent powered by your choice of LLM. It's designed to run as a persistent background process, handling deep work tasks (research, analysis, code generation, etc.) while maintaining long-term memory across restarts.

**In one sentence:** Drop a task file, ClawServant thinks through it, saves the result, and remembers what it learned.

### Why ClawServant Exists

Traditional AI agents (web UIs, FastAPI servers, etc.) add complexity when what you need is simplicity:
- ❌ Web UIs add 80MB+ overhead (FastAPI, React, JavaScript)
- ❌ Async task routing adds 30-60s latency
- ❌ No clear integration path with existing automation tools
- ❌ Expensive development/maintenance for lightweight use cases

ClawServant strips away the UI and leaves the engine:
- ✅ Pure Python (500 lines)
- ✅ No external frameworks (just provider libraries)
- ✅ Instant task detection (file-based)
- ✅ 50MB footprint (runs on 2GB systems)
- ✅ Persistent memory (JSONL, searchable)
- ✅ OpenClaw-native (stdin/files/JSON I/O)
- ✅ Flexible LLM backends (Bedrock, Anthropic, OpenAI, Ollama, or custom)

### Credits

ClawServant builds on lessons learned from [HermitClaw](https://github.com/openclaw/hermitclaw). We took the core concept (persistent thinking agent with memory) and stripped away the web UI to create a CLI-first tool optimized for autonomous background work and tight OpenClaw integration.

### ClawServant vs Alternatives

| Feature | Web UI Agents | ClawServant |
|---------|---------------|------------|
| **Memory footprint** | 80MB+ | 50MB |
| **Task latency** | 30-60s | 8-15s |
| **Startup time** | 3-5s | 2s |
| **Lines of code** | 2000+ | 500 |
| **External frameworks** | FastAPI, React, Node | None (pure Python) |
| **File-based task queue** | ❌ | ✅ |
| **Persistent memory** | ❌ | ✅ (JSONL) |
| **LLM flexibility** | Single provider | 4+ providers + custom |
| **Web UI** | ✅ | ❌ (CLI-first) |
| **Best for** | Interactive use | Autonomous background work |

## Quick Start

### Option 1: Automated Installer (Recommended)

```bash
curl -fsSL https://github.com/mayur-dot-ai/ClawServant/raw/main/install.sh | bash
python3 setup.py
```

This will:
1. Clone the repository
2. Run an interactive setup wizard
3. Configure your LLM provider (30+ models across multiple providers)
4. Create folders and credentials.json
5. Install required dependencies
6. Verify the setup works

### Prerequisites

Before running ClawServant, make sure you have Python 3.9+ and pip3 installed.

**Required Python packages** (installed automatically by setup.py or manually):

```bash
# For AWS Bedrock support
pip3 install boto3

# For Anthropic API support
pip3 install anthropic

# For OpenAI API support
pip3 install openai

# For OpenRouter support
pip3 install httpx
```

Or install all at once:
```bash
pip3 install boto3 anthropic openai httpx
```

### Option 2: Manual Setup

```bash
# Clone
git clone https://github.com/mayur-dot-ai/ClawServant.git
cd ClawServant

# Run setup wizard
python3 setup.py
```

### Option 3: Manual Configuration

```bash
git clone https://github.com/mayur-dot-ai/ClawServant.git
cd ClawServant

# Copy and edit credentials
cp credentials.json.example credentials.json
# Edit credentials.json with your provider config

# Create folders
mkdir -p tasks results brain personality rules
```

## First Run

```bash
# Check status
python3 clawservant.py --status

# Run a single task
python3 clawservant.py --task "What is 2+2?"

# Start continuous thinking
python3 clawservant.py --continuous
```
```
/path/to/work/
├── credentials.json      # Your LLM provider config
├── memory.jsonl          # All thoughts, learnings, results (append-only)
├── state.json            # Cycle count, task count, timestamps
├── tasks/                # Drop .md files here
├── results/              # Completed task outputs (.json)
├── brain/                # Knowledge files
├── personality/          # Agent personality definition
└── rules/                # Behavior rules
```

## Portability

ClawServant is designed to run from **any directory**. Each installation is self-contained.

**To run ClawServant:**

1. Navigate to the folder where you installed it:
```bash
cd /path/to/your/clawservant
```

2. Run the Python script:
```bash
python3 clawservant.py --continuous
```

**Running multiple instances:**

Each instance gets its own folder with separate credentials and memory:

```bash
# Instance 1: Research agent
cd /work/researcher1
python3 clawservant.py --continuous

# Instance 2: Developer agent  
cd /work/researcher2
python3 clawservant.py --continuous
```

Each folder has its own:
- `credentials.json` (API keys/config)
- `memory.jsonl` (persistent memory)
- `tasks/`, `results/`, `brain/`, etc.

No global state, no conflicts. They run completely independently.

**Optional: Custom work directory**

If you want credentials and memory in a different location:
```bash
export CLAWSERVANT_WORK_DIR=/custom/path
python3 clawservant.py --continuous
```

## How It Works

### The Thinking Cycle

1. **Initialize** — Load memories, restore state
2. **Check for tasks** — Scan `tasks/` folder
3. **Process tasks** — If found, send to LLM with context
4. **Record results** — Save output, update memory
5. **Continuous thought** — Generate reflection (no task needed)
6. **Persist** — Save state, append to memory
7. **Wait** — Sleep for `--interval` seconds, repeat

### Identity System (Three Layers)

**1. Personality (`personality/personality.md`)**
- WHO the agent is
- Communication style, values, preferences
- Loaded once at startup

**2. Rules (`rules/rules.md`)**
- HOW the agent behaves
- If/then guidelines, constraints
- Decision-making framework

**3. Brain (`brain/` folder)**
- WHAT the agent knows
- Domain knowledge, standards, best practices
- Auto-reloads if files change (no restart needed)

All three are auto-incorporated into the system prompt before each LLM call.

### Memory Model

Each entry in `memory.jsonl` is a single-line JSON:

```json
{
  "timestamp": "2026-02-17T09:50:16.090875",
  "kind": "thought",
  "content": "I should focus on improving my research methodology",
  "importance": 1
}
```

**Kinds:**
- `thought` — Internal reasoning
- `task` — Received task
- `result` — Task output
- `observation` — General learnings

Memory is **append-only** and persistent across restarts.

## Use Cases

### Research Agent
```bash
mkdir -p /work/researcher
cd /work/researcher
cp /path/to/ClawServant/credentials.json.example credentials.json
# Edit credentials.json
echo "Research Q1 2026 AI trends" > tasks/research.md
python3 /path/to/ClawServant/clawservant.py --continuous
```

### Multiple Specialists
```bash
# Code reviewer
cd /work/code-reviewer && python3 /path/to/ClawServant/clawservant.py --continuous

# Security analyzer  
cd /work/security && python3 /path/to/ClawServant/clawservant.py --continuous

# Content writer
cd /work/writer && python3 /path/to/ClawServant/clawservant.py --continuous
```

## Configuration

Edit `credentials.json` to change:
- LLM provider
- Model ID
- Region (for Bedrock)
- Fallback order

Edit `personality/personality.md` to define agent identity.
Edit `rules/rules.md` to define behavior guidelines.
Add knowledge files to `brain/` folder.

## Updates

ClawServant is a git repository, so updating is simple:

```bash
# Navigate to your installation
cd /path/to/your/clawservant

# Update the code
bash update.sh
```

This safely pulls the latest code without touching:
- `credentials.json` (your API keys)
- `memory.jsonl` (your memories)
- `tasks/`, `results/`, `brain/`, etc. (your data)

To manually update:
```bash
git pull origin main
```

Your local files are unaffected since they're in `.gitignore`.

## Performance

| Metric | Value |
|--------|-------|
| Startup time | ~2 seconds |
| Single task completion | ~8-15 seconds |
| Memory footprint | ~50MB |
| Cost (Bedrock Haiku 4.5) | ~$0.20-0.30/hour (24/7) |

## Troubleshooting

### "No LLM providers available"
Ensure `credentials.json` exists in your work directory with valid provider config.

### Task not processing
1. Verify task file is in `tasks/` directory
2. Check file extension is `.md`
3. Run `python3 clawservant.py --status` to debug

### Memory grows too large
```bash
# Archive old memories
cp memory.jsonl memory.archive.jsonl
# Keep only recent
tail -500 memory.archive.jsonl > memory.jsonl
```

## Provider Details

- **Bedrock** — AWS managed Claude (25-50% cheaper than direct API)
- **Anthropic** — Direct Claude API (more control, slightly more expensive)
- **OpenAI** — Direct GPT-4/GPT-4o API
- **Ollama** — Local LLM (free, offline, but slower)

See [PROVIDERS.md](./PROVIDERS.md) for detailed API reference.

## Development

### Create a Specialist Variant

```bash
cp clawservant.py developer.py
# Edit: change name and system prompt
python3 developer.py --task "Generate a Python function..."
```

### Add Custom Tools

Modify the `think()` method to include tool calls (web search, file I/O, APIs, etc.).

### Contribute

Found a bug? Want a feature? Open an issue or PR on GitHub.

## License

MIT — Use, modify, and distribute freely.

---

**Built by:** mayur.ai  
**Powered by:** AWS Bedrock + Claude  
**Status:** Production ready (Feb 2026)  
**For:** OpenClaw installations and autonomous AI workflows

---

## FAQ

### Q: Can I use multiple providers with fallback?

**A:** Yes! In `setup.py`, choose "Multiple providers (with fallback)" option. ClawServant will try each in order until one works.

Edit `credentials.json` to set priority:
```json
{
  "providers": [
    { "name": "bedrock", ... },
    { "name": "anthropic", ... }
  ],
  "fallback_order": ["bedrock", "anthropic"]
}
```

### Q: How portable is this really?

**A:** Completely! Everything lives in one folder:
- `credentials.json` — Your API keys
- `memory.jsonl` — Your memories
- `tasks/`, `results/`, etc. — Your data

Copy the folder anywhere, run `python3 clawservant.py`, it just works. No global state, no ~/.clawservant folder, no environment variables needed.

### Q: Can I run multiple instances simultaneously?

**A:** Yes! Each folder is independent. Create separate directories:
```bash
mkdir researcher1 researcher2
cd researcher1
git clone https://github.com/mayur-dot-ai/ClawServant.git .
python3 setup.py
# Each has its own credentials, memory, and state
```

### Q: What's the cost?

**A:** Depends on model and usage:

| Model | Cost | Ideal For |
|-------|------|-----------|
| Bedrock Haiku 4.5 | ~$0.20-0.30/hr (24/7) | Budget, continuous work |
| Bedrock Sonnet | ~$0.80/hr (24/7) | Balanced reasoning |
| OpenAI GPT-4o | ~$1.50/hr (24/7) | Premium reasoning |
| Ollama Local | Free | Offline, no API cost |

### Q: Can I customize the system prompt?

**A:** Yes! Edit `personality/personality.md` and `rules/rules.md`:
- `personality.md` — How the agent thinks and behaves
- `rules/rules.md` — Guidelines and constraints

Changes take effect on next task.

### Q: Where does memory persist?

**A:** Two places:
- `memory.jsonl` — Long-term memory (survives restarts)
- `brain/` — Brain files (persistent knowledge base)

Memory is searchable and human-readable (JSONL format).

### Q: How do I stop a running task?

**A:** Just delete the task file:
```bash
rm tasks/task_*.md
```

ClawServant checks for task file before starting each cycle.

### Q: Can I integrate with OpenClaw's webhook system?

**A:** Not yet, but planned! For now, use file-based task queue.

### Q: Is ClawServant secure?

**A:** Credentials are stored locally in `credentials.json`. Best practices:
- Never commit `credentials.json` to git (it's in `.gitignore`)
- Don't share your ClawServant folder (it has your API keys)
- Rotate credentials periodically
- Use dedicated API keys with minimal permissions when possible

---

## Extended Troubleshooting

### "ModuleNotFoundError: No module named 'boto3'"

**Problem:** You're using AWS Bedrock but boto3 isn't installed.

**Solution:**
```bash
pip3 install boto3
```

All required packages:
```bash
pip3 install boto3 anthropic openai httpx
```

### "Credentials showing but provider says unavailable"

**Problem:** credentials.json has credentials but provider won't connect.

**For AWS Bedrock:**
- Verify AWS Access Key ID is correct
- Verify AWS Secret Access Key is complete (not truncated)
- Check region is supported (usually `us-east-1`)
- Ensure your AWS account has Bedrock API access enabled
- Try: `python3 -c "import boto3; boto3.client('bedrock-runtime', region_name='us-east-1')"`

**For Anthropic/OpenAI:**
- Verify API key is correct (copy fresh from provider's dashboard)
- Check API key hasn't been revoked or rate-limited
- Try the API key in another tool first to verify it works

### "Task stuck in tasks/ folder"

**Problem:** Task file isn't being processed.

**Solution:** Make sure filename follows pattern: `task_*.md` or `task_*.txt`

**Debug:**
```bash
ls -la tasks/
python3 clawservant.py --status
# Check if task is actually being found
```

### "Memory file too large"

**Problem:** `memory.jsonl` growing too fast.

**Solution:**
```bash
# Archive old memories
mv memory.jsonl memory.archive.jsonl
touch memory.jsonl

# Keep only recent
tail -500 memory.archive.jsonl > memory.jsonl
```

### "Invalid credentials.json"

**Problem:** JSON parsing error.

**Solution:** Validate your JSON:
```bash
python3 -m json.tool credentials.json
```

If it fails, check for:
- Trailing commas (not allowed in JSON)
- Missing quotes around keys
- Unescaped special characters in values

### "DeprecationWarning about datetime"

**Problem:** You see warnings about `datetime.utcnow()` (older versions only).

**Solution:** Update to latest version:
```bash
git pull origin main
```