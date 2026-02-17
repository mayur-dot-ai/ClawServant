#!/bin/bash
# ClawServant Interactive Installer
# Usage: curl -fsSL https://github.com/mayur-dot-ai/ClawServant/raw/main/install.sh | bash

set -e

echo "🤖 ClawServant Installer"
echo "========================"
echo ""

# Check if already in clawservant directory
if [ -f "clawservant.py" ]; then
    echo "✅ ClawServant code found in current directory"
    CLAWSERVANT_DIR="."
else
    echo "📦 Cloning ClawServant from GitHub..."
    git clone https://github.com/mayur-dot-ai/ClawServant.git clawservant
    cd clawservant
    CLAWSERVANT_DIR="."
    echo "✅ Cloned to ./clawservant"
    echo ""
fi

# Ask for provider
echo "Select your LLM provider:"
echo "  1) AWS Bedrock (Claude, Llama, Mistral)"
echo "  2) Anthropic (Direct Claude API)"
echo "  3) OpenAI (GPT-4, GPT-4o)"
echo "  4) Ollama (Local LLM)"
echo "  5) Custom Provider"
read -p "Choice (1-5): " provider_choice

case $provider_choice in
  1)
    PROVIDER="bedrock"
    echo ""
    echo "AWS Bedrock Configuration:"
    read -p "AWS Region (default: us-east-1): " aws_region
    aws_region=${aws_region:-us-east-1}
    read -p "Model ID (default: us.anthropic.claude-haiku-4-5-20251001-v1:0): " model_id
    model_id=${model_id:-us.anthropic.claude-haiku-4-5-20251001-v1:0}
    
    cat > credentials.json << EOF
{
  "providers": [
    {
      "name": "bedrock",
      "enabled": true,
      "config": {
        "region": "$aws_region",
        "model_id": "$model_id"
      }
    }
  ],
  "fallback_order": ["bedrock"]
}
EOF
    echo "✅ credentials.json created"
    ;;
    
  2)
    PROVIDER="anthropic"
    echo ""
    echo "Anthropic Configuration:"
    read -sp "API Key (sk-ant-...): " api_key
    echo ""
    read -p "Model (default: claude-3-5-sonnet-20241022): " model
    model=${model:-claude-3-5-sonnet-20241022}
    
    cat > credentials.json << EOF
{
  "providers": [
    {
      "name": "anthropic",
      "enabled": true,
      "config": {
        "api_key": "$api_key",
        "model": "$model"
      }
    }
  ],
  "fallback_order": ["anthropic"]
}
EOF
    echo "✅ credentials.json created"
    ;;
    
  3)
    PROVIDER="openai"
    echo ""
    echo "OpenAI Configuration:"
    read -sp "API Key (sk-...): " api_key
    echo ""
    read -p "Model (default: gpt-4o-mini): " model
    model=${model:-gpt-4o-mini}
    
    cat > credentials.json << EOF
{
  "providers": [
    {
      "name": "openai",
      "enabled": true,
      "config": {
        "api_key": "$api_key",
        "model": "$model"
      }
    }
  ],
  "fallback_order": ["openai"]
}
EOF
    echo "✅ credentials.json created"
    ;;
    
  4)
    PROVIDER="ollama"
    echo ""
    echo "Ollama Configuration:"
    read -p "Base URL (default: http://localhost:11434): " base_url
    base_url=${base_url:-http://localhost:11434}
    read -p "Model name (default: llama2): " model
    model=${model:-llama2}
    
    cat > credentials.json << EOF
{
  "providers": [
    {
      "name": "ollama",
      "enabled": true,
      "config": {
        "base_url": "$base_url",
        "model": "$model"
      }
    }
  ],
  "fallback_order": ["ollama"]
}
EOF
    echo "✅ credentials.json created"
    ;;
    
  5)
    PROVIDER="custom"
    echo ""
    echo "Custom Provider - Edit credentials.json manually after setup"
    cp credentials.json.example credentials.json
    ;;
    
  *)
    echo "❌ Invalid choice"
    exit 1
    ;;
esac

echo ""
echo "📁 Setting up folders..."
mkdir -p tasks results brain personality rules
echo "✅ Folders created (tasks/, results/, brain/, personality/, rules/)"

echo ""
echo "🧪 Testing setup..."
if python3 clawservant.py --status > /dev/null 2>&1; then
    echo "✅ Setup verified!"
else
    echo "⚠️  Setup test failed. Check credentials.json and provider setup."
fi

echo ""
echo "========================================="
echo "✅ ClawServant Ready!"
echo "========================================="
echo ""
echo "To start:"
echo "  python3 clawservant.py --continuous"
echo ""
echo "Or run a single task:"
echo "  python3 clawservant.py --task \"Your task here\""
echo ""
echo "Check status:"
echo "  python3 clawservant.py --status"
echo ""
echo "View memory:"
echo "  python3 clawservant.py --memory"
echo ""
echo "Drop tasks in: tasks/"
echo "Results saved to: results/"
echo "Memory persisted to: memory.jsonl"
echo ""