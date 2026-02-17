#!/bin/bash
# ClawServant Installer for macOS, Linux
# Usage: curl -fsSL https://github.com/mayur-dot-ai/ClawServant/raw/main/install.sh | bash

set -e

echo "🤖 ClawServant Installer"
echo ""

# Check prerequisites
if ! command -v git &> /dev/null; then
    echo "❌ Error: git is not installed"
    echo "   Install from: https://git-scm.com/downloads"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 is not installed"
    echo "   Install from: https://python.org"
    exit 1
fi

python_version=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || echo "unknown")
echo "✅ Python $python_version found"
echo "✅ Working directory: $(pwd)"
echo ""

# Clone
if [ ! -f "clawservant.py" ]; then
    echo "📦 Cloning ClawServant..."
    git clone https://github.com/mayur-dot-ai/ClawServant.git . || exit 1
fi

echo ""
echo "⚠️  Next steps:"
echo ""
echo "1. Install Python dependencies:"
echo "   pip3 install boto3 anthropic openai httpx"
echo ""
echo "2. Configure your LLM provider:"
echo "   python3 setup.py"
echo ""
echo "3. Start using ClawServant:"
echo "   python3 clawservant.py --task 'Your task here'"
echo ""