#!/bin/bash
# Start ClawServant continuous thinking loop

cd ~/.openclaw/workspace/claw

# Run in background with nohup
nohup python3 clawservant.py --continuous --interval 5 > claw-continuous.log 2>&1 &

echo "✅ ClawServant started (PID: $!)"
echo "   Logs: ~/.openclaw/workspace/claw/claw-continuous.log"
echo "   Memory: ~/.openclaw/workspace/claw/workspace/memory.jsonl"
echo "   Status: python3 clawservant.py --status"
echo "   View memory: python3 clawservant.py --memory"