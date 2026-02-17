#!/bin/bash
# Start ClawServant continuous thinking loop

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Run from the script directory (wherever it's installed)
cd "$SCRIPT_DIR"

# Run in background with nohup
nohup python3 clawservant.py --continuous --interval 5 > clawservant-continuous.log 2>&1 &

PID=$!

echo "✅ ClawServant started (PID: $PID)"
echo "   Logs: $SCRIPT_DIR/clawservant-continuous.log"
echo "   Memory: $SCRIPT_DIR/memory.jsonl"
echo "   Work dir: $SCRIPT_DIR"
echo "   Status: cd $SCRIPT_DIR && python3 clawservant.py --status"
echo "   View memory: cd $SCRIPT_DIR && python3 clawservant.py --memory"