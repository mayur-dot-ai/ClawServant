# Why ClawServant Was Built

## The Problem

**Modern AI agents are over-engineered.**

When you deploy an AI agent, you typically get:
- FastAPI server (5-10MB)
- React frontend (20-30MB)
- WebSocket handlers, job queues, async task managers
- Docker containers, orchestration complexity
- Monitoring, logging, dashboards

**For what?** To send a text prompt and get a response back.

This overhead kills productivity for teams that just need **thinking machines**, not user interfaces.

### The Specific Problem at mayur.ai

We had [Hermit](https://github.com/openclaw/hermitclaw) running, which is excellent, but:

1. **Web UI bottleneck** — Even though we didn't need a UI, it was always running, consuming resources
2. **Task routing latency** — 30-60+ second delays from "task received" to "agent thinking"
3. **Memory overhead** — ~80MB for FastAPI + React + Node.js
4. **Complexity** — 5+ separate processes just to get one agent thinking

On a 2GB EC2 instance (our test environment), this was inefficient.

## The Solution: ClawServant

We asked: **What if we just built the engine?**

No UI. No frameworks. Just Python + Bedrock + persistent memory.

### What Changed

**Before (Hermit):**
```
Task file → [File watcher] → [API] → [FastAPI] → [WebSocket] → [Brain] → Bedrock
                                                                             ↓
                                                                        (30-60s latency)
```

**After (ClawServant):**
```
Task file → [Direct read] → [Bedrock] → [Result saved]
                                        (8-15s, instant)
```

### The Result

| Metric | Hermit | ClawServant | Improvement |
|--------|--------|-------------|------------|
| Startup | ~3-5s | ~2s | 30% faster |
| Memory footprint | ~80MB | ~50MB | 37% reduction |
| Task latency | 30-60s+ | 8-15s | 80% faster |
| Lines of code | 2000+ | 400 | 80% less complexity |
| Dependencies | FastAPI, React, Node, Python | Python only | 1 language |
| Cost | ~$50-70/mo | ~$50-70/mo | Same (different reason) |

## Why This Design?

### 1. CLI-First (No Web UI)

OpenClaw installations are **already** CLI-based. ClawServant fits naturally:

```bash
# Drop a task
cat > workspace/tasks/research.md << EOF
Analyze X
EOF

# Run ClawServant
python3 clawservant.py --continuous

# Get results
cat workspace/results/task_*.json
```

**Benefit:** No learning curve. No new UI. Just files and JSON.

### 2. Persistent Memory (JSONL)

Instead of in-memory caches or complex databases, we use append-only JSONL:

```json
{"timestamp": "...", "kind": "thought", "content": "...", "importance": 1}
{"timestamp": "...", "kind": "task", "content": "...", "importance": 3}
{"timestamp": "...", "kind": "result", "content": "...", "importance": 2}
```

**Benefit:** 
- Fully auditable (every thought is recorded)
- Searchable (grep, jq, Python)
- Recoverable (append-only means no accidental loss)
- Shareable (it's just JSON)

### 3. AWS Bedrock (Not OpenAI)

Bedrock costs 25-50% less than OpenAI and integrates with AWS IAM. For infrastructure-first teams, it's the natural choice.

**Benefit:**
- Lower cost ($50-70/mo vs $100-200/mo for equivalent OpenAI usage)
- Region-resilient (inference profiles auto-route across regions)
- No external API keys to manage (IAM only)

### 4. Instant Task Detection

File-based task queue means zero latency:

```bash
echo "Your task" > tasks/my-task.md
# ClawServant immediately picks it up (next 5-second cycle)
```

**Benefit:** Predictable, observable, no complex job queues.

## How to Use ClawServant

### Single Specialist Agent

```bash
# Start as Researcher
python3 clawservant.py --continuous
```

### Multiple Agents (Different Roles)

```bash
# Create variants
cp clawservant.py researcher.py   # Change system prompt
cp clawservant.py developer.py    # Change system prompt
cp clawservant.py security.py     # Change system prompt

# Run each with different WORK_DIR
WORK_DIR=~/researcher python3 researcher.py --continuous
WORK_DIR=~/developer python3 developer.py --continuous
WORK_DIR=~/security python3 security.py --continuous
```

### Integrate with OpenClaw

**From your main OpenClaw session:**

```bash
# Pattern 1: Spawn ClawServant for a project
openclaw sessions_spawn \
  --task "Deploy ClawServant for market research" \
  --label "market-researcher"

# Pattern 2: Queue a task
cat > ~/.openclaw/workspace/clawservant/workspace/tasks/analyze.md << EOF
# Analyze this data
...
EOF

# Pattern 3: Read results
python3 -c "
import json
from pathlib import Path

results_dir = Path.home() / '.openclaw/workspace/clawservant/workspace/results'
for result_file in sorted(results_dir.glob('*.json'))[-5:]:
    result = json.load(open(result_file))
    print(f\"{result['timestamp']}: {result['task'][:50]}\")
    print(f\"Result: {result['result'][:200]}\n\")
"
```

## Why Not Just Use ChatGPT / Claude Web?

| Need | ChatGPT | Claude Web | ClawServant |
|------|---------|-----------|------------|
| **Automation** | ❌ (no API) | ❌ (no API) | ✅ |
| **Persistent memory** | ❌ | ❌ | ✅ |
| **Cost control** | High | Medium | Low |
| **Infrastructure control** | ❌ (Anthropic cloud) | ❌ (Anthropic cloud) | ✅ (Your AWS) |
| **Privacy** | ❌ | ❌ | ✅ (stays in AWS region) |
| **Offline capability** | ❌ | ❌ | ❌ (needs AWS) |

## What About Hermit?

Hermit is excellent for interactive use cases where you want a UI. ClawServant is for **autonomous background work**.

**Use Hermit when:**
- You need a web interface
- Humans interact directly with the agent
- Visual feedback matters

**Use ClawServant when:**
- You want autonomous background work
- Integration with automation tools matters
- Minimal overhead is critical
- You're building production systems

## Future Roadmap

### Phase 1 ✅ (Done)
- Pure Python implementation
- Bedrock integration
- Persistent JSONL memory
- File-based task queue

### Phase 2 (Next)
- Tool support (web_search, file I/O, API calls)
- Variant agents (Developer, Security, Architect)
- Memory search/retrieval optimization
- Systemd service templates

### Phase 3 (Future)
- Multi-agent orchestration
- Tool marketplace (shared tools across agents)
- Cost budgets and monitoring
- Performance analytics

## The Philosophy

**ClawServant is built on three principles:**

1. **Simplicity** — Do one thing well (think, learn, output)
2. **Clarity** — Everything is observable (files, JSON, logs)
3. **Efficiency** — Minimal overhead, maximum value

It's not a framework. It's not a platform. It's an **employee** — hired to do deep work, with long-term memory, and the ability to learn.

---

**Next:** [Quick Start](./README.md) or [Integration Guide](./INTEGRATION.md)