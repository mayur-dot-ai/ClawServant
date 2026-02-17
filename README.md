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

## Quick Start

### 1. Install

```bash
git clone https://github.com/you/ClawServant.git
cd ClawServant
```

### 2. Configure Your LLM

Create `~/.clawservant/credentials.json` with your provider:

**AWS Bedrock:**
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
  "fallback_order": ["bedrock"]
}
```

**Or customize the model ID:**
```json
{
  "name": "bedrock",
  "config": {
    "region": "us-east-1",
    "model_id": "us.anthropic.claude-3-5-sonnet-20241022-v2:0"
  }
}
```

**Anthropic API:**
```json
{
  "providers": [
    {
      "name": "anthropic",
      "enabled": true,
      "config": {
        "model": "claude-3-5-sonnet-20241022"
      }
    }
  ],
  "fallback_order": ["anthropic"]
}
```

**OpenAI:**
```json
{
  "providers": [
    {
      "name": "openai",
      "enabled": true,
      "config": {
        "model": "gpt-4o-mini"
      }
    }
  ],
  "fallback_order": ["openai"]
}
```

**Local Ollama:**
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

**Multiple providers (fallback):**
```json
{
  "providers": [
    {"name": "bedrock", "enabled": true, "config": {...}},
    {"name": "anthropic", "enabled": true, "config": {...}},
    {"name": "openai", "enabled": true, "config": {...}}
  ],
  "fallback_order": ["bedrock", "anthropic", "openai", "ollama"]
}
```

See [SETUP.md](./SETUP.md) for complete setup guide for all providers.

### 3. Run

**Option A: Continuous thinking (background)**
```bash
python3 clawservant.py --continuous --interval 5
```

**Option B: Single task**
```bash
python3 clawservant.py --task "Your task here"
```

**Option C: Check status**
```bash
python3 clawservant.py --status
```

### 4. Monitor

ClawServant saves all output to a local workspace:
```
~/.clawservant/
├── workspace/
│   ├── memory.jsonl      # All thoughts, learnings, results (append-only)
│   ├── state.json        # Cycle count, task count, timestamps
│   ├── brain/            # Custom knowledge files (your input)
│   ├── tasks/            # Incoming tasks (.md files)
│   └── results/          # Completed task outputs (.json files)
└── credentials.json      # Your LLM provider config
```

## Architecture

### Core Thinking Cycle

1. **Initialize** — Load core personality, brain files, and memories
2. **Check for tasks** — Scan `tasks/` folder
3. **Process tasks** — If found, send to LLM with context
4. **Record results** — Save output, update memory
5. **Continuous thought** — Generate reflection (no task needed)
6. **Persist** — Save state, append to memory
7. **Wait** — Sleep for `--interval` seconds, repeat

### Identity System (Two Parts)

ClawServant has two separate identity layers:

**1. Core Personality (`core.md`)**
- WHO the agent is: name, role, expertise, communication style, values
- Single file at `~/.clawservant/workspace/core.md`
- Loaded once at startup
- Defines the agent's personality and principles
- Example: "I'm a researcher who values accuracy and cites sources"

**2. Brain Files (`brain/` folder)**
- WHAT the agent knows: domain knowledge, guidelines, standards
- Multiple files in `~/.clawservant/workspace/brain/`
- Examples: `research-methodology.md`, `coding-standards.md`, `company-values.md`
- Auto-reloads every cycle (no restart needed if you add/modify files)
- Each file added to the system prompt automatically

**Key Difference:**
- **core.md** = personality (who you are)
- **brain/** = knowledge (what you know)

Both are incorporated into the system prompt before each LLM call.

### Memory Model

Each entry in `memory.jsonl` is a single-line JSON:

```json
{
  "timestamp": "2026-02-17T09:50:16.090875",
  "kind": "thought",
  "content": "I should focus on the research task at hand",
  "importance": 1
}
```

**Kinds:**
- `thought` — Internal reasoning (importance: 1, low)
- `task` — Received task (importance: 3, high)
- `result` — Task output (importance: 2, medium)
- `observation` — General learnings (importance: 1, low)

## Integration with OpenClaw

### Pattern 1: File-Based Task Queue

Drop a task into the `tasks/` folder, ClawServant picks it up:

```bash
# From your OpenClaw session:
cat > ~/.clawservant/workspace/tasks/analyze-logs.md << 'EOF'
# Analyze Application Logs

Review the attached logs and identify:
1. Error patterns
2. Performance bottlenecks
3. Security concerns
4. Recommendations
EOF
```

ClawServant processes it and saves results to `workspace/results/`.

### Pattern 2: Sub-Agent Spawning

Use OpenClaw's `sessions_spawn` to run ClawServant for specific projects:

```bash
# From main OpenClaw session:
openclaw sessions_spawn \
  --task "Deploy ClawServant for research project" \
  --label "research-agent"
```

### Pattern 3: Programmatic Access

Query ClawServant's memory from other scripts:

```python
import json
from pathlib import Path

memory_file = Path.home() / ".clawservant/workspace/memory.jsonl"

# Load all memories
memories = []
with open(memory_file) as f:
    for line in f:
        if line.strip():
            memories.append(json.loads(line))

# Find recent results
results = [m for m in memories if m["kind"] == "result"][-10:]
for r in results:
    print(f"[{r['timestamp']}] {r['content'][:100]}...")
```

## Performance

| Metric | Value |
|--------|-------|
| Startup time | ~2 seconds |
| Single task completion | ~8-15 seconds (depending on task complexity) |
| Memory footprint | ~50MB |
| Cost | Depends on LLM provider (Bedrock, Anthropic, OpenAI, or free with Ollama) |

## Configuration

### Workspace Structure

```
~/.clawservant/
├── credentials.json          # LLM provider config (you create)
├── core.md                   # Personality file (WHO you are) - optional
├── brain/                    # Knowledge files (WHAT you know) - optional
│   ├── domain-knowledge.md
│   ├── coding-standards.md
│   └── research-methodology.md
├── memory.jsonl              # Persistent memories (auto-generated)
├── state.json                # Agent state (auto-generated)
├── tasks/                    # Task queue (you drop .md files)
└── results/                  # Task outputs (auto-generated)
```

### Core Personality File

Create `~/.clawservant/workspace/core.md` to define WHO the agent is:

```markdown
# [Your Agent Name]

## Who I Am
- Role: Researcher / Developer / Analyst
- Expertise: [Your specializations]
- Style: [Communication style]

## How I Think
- I approach problems by [methodology]
- I value [principles]
- My strengths: [skills]

## What I Do
- Primary tasks: [main work]
- Tools I use: [capabilities]
- Success looks like: [outcomes]
```

**This is your agent's personality.** It's included in every LLM call.

See `core.md.example` for a complete template.

### Custom Brain Files

Create knowledge files in `~/.clawservant/workspace/brain/` to define WHAT the agent knows:

```bash
# Create a knowledge base
echo "# Company Research Standards

- Always cite sources
- Verify with 3+ independent sources
- Distinguish opinion from fact" > brain/research-standards.md

# Add coding guidelines
echo "# Code Quality Standards

- Python: PEP 8 compliance
- Functions: Clear docstrings
- Error handling: All exceptions caught" > brain/coding-standards.md
```

**Any `.md` or `.txt` file in `brain/` is automatically loaded and included in the system prompt.**

**Auto-reload:** If you add or modify brain files while ClawServant is running, they're automatically reloaded each cycle—no restart needed.

### Credentials File

Your LLM provider is configured separately from your personality/knowledge. This keeps them independent.

Create `~/.clawservant/credentials.json`:

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
  "fallback_order": ["bedrock"]
}
```

You can customize:
- `region` (for Bedrock)
- `model_id` (Bedrock model, e.g., Opus, Sonnet, Haiku)
- `api_key` (for Anthropic/OpenAI)
- Multiple providers with fallback

See [SETUP.md](./SETUP.md) for all provider options.

## Use Cases

### Research Agent
Deploy ClawServant to continuously research market trends, competitor updates, or technical topics:

```bash
# Create recurring research tasks
cat > ~/.clawservant/workspace/tasks/market-research.md << 'EOF'
# Weekly Market Research

Research and summarize this week's AI/ML developments:
- New model releases
- Pricing changes
- Enterprise adoption patterns
EOF

python3 clawservant.py --continuous --interval 3600  # Run hourly
```

### Code Analysis Agent
Use ClawServant to analyze codebases, suggest optimizations, or generate documentation:

```bash
python3 clawservant.py --task "Analyze /repo codebase and suggest performance improvements"
```

### Content Creation
Have ClawServant draft blog posts, technical documentation, or summaries:

```bash
python3 clawservant.py --task "Draft a blog post on: The State of AI in Q1 2026"
```

### Decision Support
Ask ClawServant to analyze options and provide structured recommendations:

```bash
python3 clawservant.py --task "Compare these three approaches [details] and recommend the best one"
```

## Development & Extension

### Add Custom Tools

Modify the `think()` method to include tool calls (web search, file I/O, API calls, etc.):

```python
async def think(self, prompt: str) -> str:
    # Add tool support here
    # Examples: web search, database queries, API calls
    pass
```

### Create Specialist Variants

Copy `clawservant.py` and change the core personality:

```bash
cp clawservant.py developer.py
# Edit developer.py: change system prompt to Developer role
python3 developer.py --task "Generate a Python function that..."
```

Build variants:
- **Researcher** — Deep analysis, citations, synthesis
- **Developer** — Code generation, debugging, optimization
- **Security** — Risk analysis, threat modeling, compliance
- **Architect** — System design, trade-off analysis

### Add Custom LLM Providers

Edit `providers.py` and extend the `LLMProvider` class:

```python
class YourProviderName(LLMProvider):
    def __init__(self, config):
        self.config = config
        self.api_key = config.get("api_key") or os.environ.get("YOUR_API_KEY")
    
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    async def call(self, system_prompt: str, user_prompt: str, max_tokens: int = 500) -> str:
        # Call your API
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

## Common Questions

**Q: Why no web UI?**  
A: Web UIs add 80MB+ overhead and 30-60s task latency. For autonomous background work, a CLI + file-based interface is faster and simpler.

**Q: Can I run multiple ClawServant instances?**  
A: Yes! Each can have a different `WORK_DIR` and personality. Deploy as separate processes or systemd services.

**Q: What happens if ClawServant crashes?**  
A: Restart it. All memories are persisted to `memory.jsonl`, so it resumes with full context.

**Q: Can I use ClawServant with my existing tooling?**  
A: Yes. ClawServant outputs JSON and markdown, so it works with pipelines, webhooks, CI/CD systems, etc.

**Q: What's the memory limit?**  
A: Theoretically unlimited (JSONL is append-only), but practical limit is ~500 memories per day (~3MB). Context window includes the last 10 memories.

**Q: How do I customize ClawServant's behavior?**  
A: Create a `core.md` file in `workspace/` and add brain files to `workspace/brain/`. See "Configuration" section above.

## Troubleshooting

### "No LLM providers available"

**Problem:** No credentials configured.

**Solution:**
1. Create `~/.clawservant/credentials.json`
2. Check provider setup (see [SETUP.md](./SETUP.md))
3. Verify environment variables or API keys

### Task Not Processing

1. Check if task file is in `~/.clawservant/workspace/tasks/`
2. Verify ClawServant is running (`ps aux | grep clawservant`)
3. Check `~/.clawservant/workspace/memory.jsonl` for errors
4. Ensure LLM provider is configured and available

### Memory Grows Too Large

```bash
# Archive old memories
cp ~/.clawservant/workspace/memory.jsonl ~/.clawservant/workspace/memory.archive.jsonl

# Keep only recent
tail -100 ~/.clawservant/workspace/memory.archive.jsonl > ~/.clawservant/workspace/memory.jsonl
```

## License

MIT — Use, modify, and distribute freely.

## Contributing

Found a bug? Want to add features? Open an issue or PR on GitHub.

---

**Inspired by:** [HermitClaw](https://github.com/openclaw/hermitclaw) — a delightful thinking agent we learned from  
**For:** OpenClaw installations and autonomous AI workflows  
**Status:** Production ready  
**Updated:** 2026-02-17


## Quick Start

### 1. Install

```bash
git clone https://github.com/mayur-dot-ai/ClawServant.git
cd ClawServant
```

### 2. Configure AWS Credentials

ClawServant uses AWS Bedrock. Ensure your AWS credentials are configured:

```bash
# Either set environment variables:
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_REGION="us-east-1"

# Or configure via AWS CLI:
aws configure
```

### 3. Run

**Option A: Continuous thinking (background)**
```bash
python3 clawservant.py --continuous --interval 5
```

**Option B: Single task**
```bash
python3 clawservant.py --task "Analyze the current state of AI pricing in 2026"
```

**Option C: Check status**
```bash
python3 clawservant.py --status
python3 clawservant.py --memory  # View recent thoughts and learnings
```

### 4. Monitor

ClawServant saves all output to a local workspace:
```
workspace/
├── memory.jsonl      # All thoughts, learnings, results (append-only)
├── state.json        # Cycle count, task count, timestamps
├── tasks/            # Incoming tasks (.md files)
└── results/          # Completed task outputs (.json files)
```

## Integration with OpenClaw

### Pattern 1: File-Based Task Queue

Drop a task into the `tasks/` folder, ClawServant picks it up:

```bash
# From your OpenClaw session:
cat > ~/.openclaw/workspace/clawservant/workspace/tasks/analyze-logs.md << 'EOF'
# Analyze Application Logs

Review the attached logs and identify:
1. Error patterns
2. Performance bottlenecks
3. Security concerns
4. Recommendations

[logs would be included]
EOF
```

ClawServant processes it and saves results to `workspace/results/`.

### Pattern 2: Sub-Agent Spawning

Use OpenClaw's `sessions_spawn` to run ClawServant for specific projects:

```bash
# From main OpenClaw session:
openclaw sessions_spawn \
  --task "Deploy ClawServant for Q2 market research project" \
  --label "market-research-agent"
```

### Pattern 3: Programmatic Access

Query ClawServant's memory from other scripts:

```python
import json
from pathlib import Path

memory_file = Path.home() / ".openclaw/workspace/clawservant/workspace/memory.jsonl"

# Load all memories
memories = []
with open(memory_file) as f:
    for line in f:
        if line.strip():
            memories.append(json.loads(line))

# Find recent research results
results = [m for m in memories if m["kind"] == "result"][-10:]
for r in results:
    print(f"[{r['timestamp']}] {r['content'][:100]}...")
```

## How It Works

### Architecture

```
┌──────────────────┐
│   Task Input     │  Markdown files, API calls, stdin
└────────┬─────────┘
         │
    ┌────▼────────────────┐
    │ ClawServant Agent   │  5-second thinking cycle
    │  - Reads tasks      │  - Processes one at a time
    │  - Calls Bedrock    │  - Records results
    │  - Saves memories   │  - Tracks state
    └────┬────────────────┘
         │
    ┌────▼──────────────────┐
    │  Persistent Storage   │
    │  - memory.jsonl       │  All thoughts (append-only)
    │  - state.json         │  Cycle tracking
    │  - results/           │  Task outputs
    └───────────────────────┘
```

### The Thinking Cycle

1. **Initialize** — Load memories, restore state
2. **Check for tasks** — Scan `tasks/` folder
3. **Process tasks** — If found, send to LLM with context
4. **Record results** — Save output, update memory
5. **Continuous thought** — Generate reflection (no task needed)
6. **Persist** — Save state, append to memory
7. **Wait** — Sleep for `--interval` seconds, repeat

### Memory Model

Each entry in `memory.jsonl` is a single-line JSON:

```json
{
  "timestamp": "2026-02-17T09:50:16.090875",
  "kind": "thought",
  "content": "I should focus on research methodology improvements",
  "importance": 1
}
```

**Kinds:**
- `thought` — Internal reasoning (importance: 1, low)
- `task` — Received task (importance: 3, high)
- `result` — Task output (importance: 2, medium)
- `observation` — General learnings (importance: 1, low)

## Performance

| Metric | Value |
|--------|-------|
| Startup time | ~2 seconds |
| Single task completion | ~8-15 seconds (depending on task complexity) |
| Memory footprint | ~50MB |
| Cost (Bedrock Haiku 4.5) | ~$0.20-0.30/hour continuous |
| Monthly (24/7) | ~$50-70 |

## Configuration

Edit `clawservant.py` to customize:

```python
MODEL_ID = "us.anthropic.claude-haiku-4-5-20251001-v1:0"  # LLM model
WORK_DIR = Path.home() / ".openclaw/workspace/clawservant/workspace"  # Workspace location
```

## Use Cases

### Research Agent
Deploy ClawServant to continuously research market trends, competitor updates, or technical topics:

```bash
# Create recurring research tasks
echo "# Weekly Market Research" > workspace/tasks/market.md
python3 clawservant.py --continuous --interval 3600  # Run hourly
```

### Code Analysis Agent
Use ClawServant to analyze codebases, suggest optimizations, or generate documentation:

```bash
python3 clawservant.py --task "Analyze the codebase in /repo and suggest performance improvements"
```

### Content Creation
Have ClawServant draft blog posts, technical documentation, or summaries:

```bash
python3 clawservant.py --task "Draft a blog post on: The State of AI in Q1 2026"
```

### Decision Support
Ask ClawServant to analyze options and provide structured recommendations:

```bash
python3 clawservant.py --task "Compare these three approaches [details] and recommend the best one"
```

## Development & Extension

### Add Custom Tools

Modify the `think()` method to include tool calls:

```python
async def think(self, prompt: str) -> str:
    """Add tool support here."""
    # Example: web search, file I/O, API calls
    # Tools can be called within the LLM response handling
    pass
```

### Create Specialist Variants

Copy `clawservant.py` and change the system prompt:

```bash
cp clawservant.py developer.py
# Edit developer.py: change system prompt to Developer role
python3 developer.py --task "Generate a Python function that..."
```

Build variants:
- **Researcher** — Deep analysis, citations, synthesis
- **Developer** — Code generation, debugging, optimization
- **Security** — Risk analysis, threat modeling, compliance
- **Architect** — System design, trade-off analysis

### Store in Org

All variants can live in the same repo with different roles:

```
ClawServant/
├── clawservant.py     # Base Researcher
├── developer.py       # Developer variant
├── security.py        # Security variant
└── architect.py       # Architect variant
```

## Comparison with Alternatives

| Feature | ClawServant | Hermit (HermitClaw) | ChatGPT | Local LLama |
|---------|-------------|-------------------|---------|-----------|
| CLI-first | ✅ | ❌ (web UI) | ❌ (web UI) | ✅ |
| Persistent memory | ✅ | ✅ | ❌ | ⚠️ |
| AWS integration | ✅ (Bedrock) | ✅ (Bedrock) | N/A | ❌ |
| Offline | ❌ (needs AWS) | ❌ (needs AWS) | ❌ | ✅ |
| Cost | $50-70/mo | $50-70/mo | $20/mo | Free |
| OpenClaw native | ✅ | ⚠️ | ❌ | ❌ |
| Production ready | ✅ | ⚠️ | ✅ | ⚠️ |

## Common Questions

**Q: Why Bedrock and not OpenAI?**  
A: Bedrock is cheaper (25-50% savings), IAM-integrated, and runs in AWS regions. For mayur.ai's infrastructure, it's the natural choice.

**Q: Can I run multiple ClawServant instances?**  
A: Yes! Each can have a different `WORK_DIR` and role. Deploy as separate processes or systemd services.

**Q: What happens if ClawServant crashes?**  
A: Restart it. All memories are persisted to `memory.jsonl`, so it resumes with full context.

**Q: Can I integrate ClawServant with my existing tooling?**  
A: Yes. ClawServant outputs JSON and markdown, so it works with pipelines, webhooks, CI/CD systems, etc.

**Q: What's the memory limit?**  
A: Theoretically unlimited (JSONL is append-only), but practical limit is ~500 memories per day (~3MB). Context window includes the last 10 memories.

## Troubleshooting

### AWS Credentials Not Found
```bash
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_REGION="us-east-1"
python3 clawservant.py --status
```

### Task Not Processing
1. Check if task file is in `workspace/tasks/`
2. Verify ClawServant is running (`ps aux | grep clawservant`)
3. Check `workspace/memory.jsonl` for errors
4. Ensure AWS credentials are valid

### Memory Grows Too Large
```bash
# Archive old memories
cp workspace/memory.jsonl workspace/memory.archive.jsonl
# Keep only recent
tail -100 workspace/memory.archive.jsonl > workspace/memory.jsonl
```

## License

MIT — Use, modify, and distribute freely.

## Contributing

Found a bug? Want to add features? Open an issue or PR on GitHub.

---

**Built by:** mayur.ai  
**Powered by:** AWS Bedrock + Claude Haiku 4.5  
**Status:** Production ready (Feb 2026)  
**For:** OpenClaw installations and autonomous AI workflows