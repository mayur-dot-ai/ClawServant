# ClawServant Quick Start (5 minutes)

## 1. Clone
```bash
git clone https://github.com/mayur-dot-ai/ClawServant.git
cd ClawServant
```

## 2. Configure AWS
```bash
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
export AWS_REGION="us-east-1"
```

## 3. Try It
```bash
# Single task
python3 clawservant.py --task "Summarize the history of AI from 2020-2026"

# Check results
cat workspace/results/task_*.json | head -100
```

## 4. Run Continuously
```bash
# In background
nohup python3 clawservant.py --continuous > clawservant.log 2>&1 &

# Check status
python3 clawservant.py --status

# View memories
python3 clawservant.py --memory
```

## 5. Add Tasks
```bash
# Create a task
cat > workspace/tasks/research.md << EOF
# Research AI Trends in 2026

Identify and summarize the top 5 developments in AI/ML space.
Focus on: architecture, reasoning, cost, safety, adoption.

Return structured markdown.
EOF

# ClawServant picks it up automatically and processes within 30 seconds
```

## 6. Integrate with OpenClaw
```bash
# From your OpenClaw session
cat > ~/.openclaw/workspace/clawservant/workspace/tasks/task.md << EOF
Your task here
EOF
```

---

**Want more?** Read [README.md](./README.md) for full docs, or [WHY.md](./WHY.md) for philosophy.