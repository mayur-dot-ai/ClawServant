#!/bin/bash
# ClawServant Installer
# Usage: curl -fsSL https://github.com/mayur-dot-ai/ClawServant/raw/main/install.sh | bash

set -e

# Clone if needed
if [ ! -f "clawservant.py" ]; then
    echo "📦 Cloning ClawServant..."
    git clone https://github.com/mayur-dot-ai/ClawServant.git clawservant
    cd clawservant
fi

# Run setup wizard
python3 setup.py