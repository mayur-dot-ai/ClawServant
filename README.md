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

---

## Installation Guide - For Humans

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

### First Run

```bash
# Check status
python3 clawservant.py --status

# Run a single task
python3 clawservant.py --task "What is 2+2?"

# Start continuous thinking
python3 clawservant.py --continuous
```

---

## Installation Guide - For OpenClaw (and Other Bots)

**⚠️ Prerequisites:** If you cannot:
- Clone from GitHub
- Modify files after download
- Run Python scripts from CLI

Then **stop here** and check with your human operator. You need those capabilities.

### Installation Steps

1. Check that you have Python 3.9+
   
2. ClawServant runs in the root of whatever folder you drop it in. Create a folder you can keep ClawServant and run it from.

3. If you are going to use AWS Bedrock, install boto3.

4. Clone the repo into a folder using git.

5. Create credentials.json and populate it with your LLM provider configuration.

6. Customize personality folder, rules folder, and brain folder.

7. Test it with a single task (like "What's the capital of Italy?") to verify it works.

8. Run any of the commands below that you prefer to use.

### Available Commands

- Single task: `python3 clawservant.py --task "Your task"`
- Continuous mode: `python3 clawservant.py --continuous`
- Check status: `python3 clawservant.py --status`
- View memory: `python3 clawservant.py --memory`
- Drop tasks: `echo "task content" > tasks/task_$(date +%s).md`
- Check results: `cat results/task_*.json`



### Loop Mode (Multi-Step Tasks)

For complex tasks that require multiple steps (read context → analyze → post), use loop mode:

```bash
# Run with loop until TASK_DONE or max iterations
python3 clawservant.py --loop --max-iterations 10 --task "Your multi-step task"
```

**How it works:**
1. Servant processes task, can execute tool calls
2. If output contains `TASK_DONE` → task complete, exit
3. If no `TASK_DONE` → increment iteration, continue
4. If max iterations reached → exit with status "max_iterations_reached"

**When to use loop mode:**
- Tasks requiring context gathering before action
- Multi-step workflows (read → analyze → post)
- Tasks where servant needs multiple tool calls

**Completion signal:** Include `TASK_DONE` in your response when the task is fully complete.

---

## Portability

ClawServant is designed to run from **any directory**. Each installation is self-contained.

**To run ClawServant:**

1. Navigate to the folder where you installed it:
```bash
cd /path/to/your/clawservant
```

2. Run a task or start continuous mode:
```bash
python3 clawservant.py --task "your task"
```

All files (credentials, memory, state) stay in that folder. No global configuration, no ~/.clawservant directory, no environment variables needed.

**Example: Multiple instances**
```bash
mkdir researcher1 researcher2
cd researcher1
git clone https://github.com/mayur-dot-ai/ClawServant.git .
python3 setup.py  # Configure instance 1

cd ../researcher2
git clone https://github.com/mayur-dot-ai/ClawServant.git .
python3 setup.py  # Configure instance 2

# Both run independently with separate credentials and memory
```

## File Structure

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

## Performance

| Metric | Value |
|--------|-------|
| Startup time | ~2 seconds |
| Single task completion | ~8-15 seconds |
| Memory footprint | ~50MB |
| Cost (Bedrock Haiku 4.5) | ~$0.20-0.30/hour (24/7) |

## Provider Details

- **Bedrock** — AWS managed Claude (25-50% cheaper than direct API)
- **Anthropic** — Direct Claude API (more control, slightly more expensive)
- **OpenAI** — Direct GPT-4/GPT-4o API
- **Ollama** — Local LLM (free, offline, but slower)

See [PROVIDERS.md](./PROVIDERS.md) for detailed API reference.

## Update

Keep your installation up-to-date:

```bash
# Automatic (safe - preserves your data)
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

## Development

### Create a Specialist Variant

```bash
cp clawservant.py developer.py
# Edit: change name and system prompt
```

### Extend with Custom Tools

Edit `clawservant.py` to add new capabilities:
- Custom research tools
- API integrations
- Database access
- File processing

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

## Troubleshooting

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

---

## License

MIT License - See LICENSE file for details