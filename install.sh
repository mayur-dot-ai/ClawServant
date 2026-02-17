#!/bin/bash
# ClawServant Installer
# Usage: curl -fsSL https://github.com/mayur-dot-ai/ClawServant/raw/main/install.sh | bash

set -e

echo "🤖 ClawServant Installer"
echo "======================="
echo ""
echo "ℹ️  ClawServant is designed to be highly portable."
echo "   All files (code, credentials, memory) stay in ONE folder."
echo ""
echo "Installation folder: $(pwd)"
echo ""

# Check prerequisites
if ! command -v git &> /dev/null; then
    echo "❌ Error: git is not installed"
    echo "   Please install git: https://git-scm.com/downloads"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 is not installed"
    echo "   Please install Python 3.9+: https://python.org"
    exit 1
fi

# Check Python version
python_version=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "✅ Python $python_version found"

# Clone if needed
if [ ! -f "clawservant.py" ]; then
    echo "📦 Cloning ClawServant from GitHub..."
    if ! git clone https://github.com/mayur-dot-ai/ClawServant.git . 2>&1; then
        echo "❌ Failed to clone repository"
        echo "   Check your internet connection and GitHub access"
        exit 1
    fi
    echo "✅ Cloned successfully"
else
    echo "✅ clawservant.py found"
fi

# Run setup wizard
echo ""
echo "Starting configuration wizard..."
echo ""
if ! python3 setup.py; then
    echo ""
    echo "❌ Setup failed"
    exit 1
fi

echo ""
echo "✅ Installation complete!"