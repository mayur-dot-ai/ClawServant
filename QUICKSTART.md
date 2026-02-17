# ClawServant Quick Start (5 minutes)

## 1. Clone
```bash
git clone https://github.com/you/ClawServant.git
cd ClawServant
```

## 2. Configure Your LLM Provider

Choose one (or multiple):

**Option A: AWS Bedrock (if you have AWS access)**
```bash
# Configure AWS credentials
aws configure
# Or set environment variables:
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
export AWS_REGION="us-east-1"
```

**Option B: Anthropic Claude API**
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

**Option C: OpenAI**
```bash
export OPENAI_API_KEY="sk-..."
```

**Option D: Local Ollama (Free, Offline)**
```bash
# Install Ollama: https://ollama.ai
# Start: ollama serve
# Pull a model: ollama pull llama2
```

## 3. Create Credentials File

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
  "fallback_order": ["bedrock", "anthropic", "openai", "ollama"]
}
```

**Replace with your provider.** See [SETUP.md](./SETUP.md) for all options and examples.

## 4. Try It

```bash
# Check status (verifies provider is available)
python3 clawservant.py --status

# Single task
python3 clawservant.py --task "Summarize the history of AI from 2020-2026"

# Check results
cat ~/.clawservant/workspace/results/task_*.json | head -100
```

## 5. Add a Task

```bash
# Create a task
cat > ~/.clawservant/workspace/tasks/research.md << EOF
# Research Task

Identify and summarize the top 5 developments in AI/ML this week.
Focus on: architecture, reasoning, cost, safety, adoption.

Return structured markdown.
EOF

# Run continuously
python3 clawservant.py --continuous

# ClawServant picks up the task automatically and processes it
# Results saved to ~/.clawservant/workspace/results/
```

## 6. Customize Your Agent (Optional)

**Add personality:**
```bash
cat > ~/.clawservant/workspace/core.md << 'EOF'
# My Agent

## Who I Am
- Role: Research Specialist
- Expertise: AI/ML, emerging technologies
- Style: Analytical, well-sourced, clear

## How I Think
- I verify claims with multiple sources
- I distinguish opinion from fact
- I cite everything
EOF
```

**Add domain knowledge:**
```bash
cat > ~/.clawservant/workspace/brain/research-standards.md << 'EOF'
# Research Standards

When researching:
1. Seek 3+ independent sources
2. Verify facts before including
3. Cite sources explicitly
4. Flag uncertainty clearly
5. Structure findings logically
EOF
```

---

**Want more?** 
- Full docs: [README.md](./README.md)
- Provider setup: [SETUP.md](./SETUP.md)
- Philosophy: [WHY.md](./WHY.md)