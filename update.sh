#!/bin/bash
# ClawServant Update Script
# Safely updates ClawServant code without touching credentials/memory

set -e

echo "🤖 ClawServant Update"
echo "===================="
echo ""

# Check if we're in a clawservant directory
if [ ! -f "clawservant.py" ]; then
    echo "❌ Error: clawservant.py not found"
    echo "   Make sure you're in the ClawServant installation directory"
    exit 1
fi

# Check for local changes
if [ -d ".git" ]; then
    if ! git diff-index --quiet HEAD --; then
        echo "⚠️  Warning: You have uncommitted changes in code files"
        echo "   These will be overwritten by the update"
        read -p "Continue? (y/n): " response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            echo "Update cancelled"
            exit 0
        fi
    fi
fi

echo "📦 Checking for updates..."

# Backup current version
if [ -d ".git" ]; then
    echo "📋 Current version:"
    git log --oneline -1
    
    # Fetch latest
    echo ""
    echo "⬇️  Pulling latest changes..."
    git pull origin main
    
    echo ""
    echo "📋 Updated to:"
    git log --oneline -1
else
    echo "❌ Error: .git directory not found"
    echo "   This doesn't appear to be a git clone"
    echo "   Please clone fresh: git clone https://github.com/mayur-dot-ai/ClawServant.git"
    exit 1
fi

echo ""
echo "✅ Update complete!"
echo ""
echo "Your credentials.json and memory.jsonl are unchanged."
echo ""
echo "To verify: python3 clawservant.py --status"