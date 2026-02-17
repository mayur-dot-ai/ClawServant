#!/usr/bin/env python3
"""
ClawServant Setup Wizard
Interactive configuration for all supported LLM providers
"""

import json
import os
import sys
import subprocess
from pathlib import Path
from typing import Dict, Any

def print_header(text: str):
    """Print section header."""
    print("\n" + "=" * 50)
    print(f"  {text}")
    print("=" * 50)

def get_input(prompt: str, default: str = None) -> str:
    """Get user input with optional default."""
    if default:
        display = f"{prompt} [{default}]: "
    else:
        display = f"{prompt}: "
    
    value = input(display).strip()
    return value if value else default

def get_secret(prompt: str) -> str:
    """Get secret input (hidden)."""
    import getpass
    return getpass.getpass(prompt + ": ")

def setup_bedrock() -> Dict[str, Any]:
    """Configure AWS Bedrock."""
    print("\n🔧 AWS Bedrock Configuration")
    
    region = get_input("AWS Region", "us-east-1")
    
    # List common models
    print("\nCommon Bedrock Claude models:")
    models = {
        "1": "us.anthropic.claude-opus-4-1-20250805-v1:0 (Opus - most capable)",
        "2": "us.anthropic.claude-3-5-sonnet-20241022-v1:0 (Sonnet - balanced)",
        "3": "us.anthropic.claude-haiku-4-5-20251001-v1:0 (Haiku - fast & cheap)",
        "4": "us.anthropic.claude-3-haiku-20240307-v1:0 (Haiku 3.5)",
        "5": "us.anthropic.llama-3-1-405b-v1:0 (Llama 3.1 405B)",
        "6": "Custom (enter your own)",
    }
    
    for key, value in models.items():
        print(f"  {key}) {value}")
    
    choice = get_input("Model choice", "3")
    
    if choice == "6":
        model_id = get_input("Model ID (with region prefix)")
    else:
        model_id = models.get(choice, models["3"]).split(" ")[0]
    
    return {
        "name": "bedrock",
        "enabled": True,
        "config": {
            "region": region,
            "model_id": model_id
        }
    }

def setup_anthropic() -> Dict[str, Any]:
    """Configure Anthropic API."""
    print("\n🔧 Anthropic API Configuration")
    
    api_key = get_secret("API Key (sk-ant-...)")
    
    print("\nCommon Anthropic Claude models:")
    models = {
        "1": "claude-opus-4-1-20250805 (Opus - most capable)",
        "2": "claude-3-5-sonnet-20241022 (Sonnet - balanced)",
        "3": "claude-3-5-haiku-20241022 (Haiku - fast & cheap)",
        "4": "Custom (enter your own)",
    }
    
    for key, value in models.items():
        print(f"  {key}) {value}")
    
    choice = get_input("Model choice", "2")
    
    if choice == "4":
        model = get_input("Model ID")
    else:
        model = models.get(choice, models["2"]).split(" ")[0]
    
    return {
        "name": "anthropic",
        "enabled": True,
        "config": {
            "api_key": api_key,
            "model": model
        }
    }

def setup_openai() -> Dict[str, Any]:
    """Configure OpenAI API."""
    print("\n🔧 OpenAI Configuration")
    
    api_key = get_secret("API Key (sk-...)")
    
    print("\nCommon OpenAI models:")
    models = {
        "1": "gpt-4o (Latest, most capable)",
        "2": "gpt-4o-mini (Fast & affordable)",
        "3": "gpt-4-turbo (Legacy)",
        "4": "Custom (enter your own)",
    }
    
    for key, value in models.items():
        print(f"  {key}) {value}")
    
    choice = get_input("Model choice", "2")
    
    if choice == "4":
        model = get_input("Model ID")
    else:
        model = models.get(choice, models["2"]).split(" ")[0]
    
    return {
        "name": "openai",
        "enabled": True,
        "config": {
            "api_key": api_key,
            "model": model
        }
    }

def setup_ollama() -> Dict[str, Any]:
    """Configure Ollama."""
    print("\n🔧 Ollama Configuration")
    
    base_url = get_input("Base URL", "http://localhost:11434")
    model = get_input("Model name (llama2, mistral, etc.)", "llama2")
    
    return {
        "name": "ollama",
        "enabled": True,
        "config": {
            "base_url": base_url,
            "model": model
        }
    }

def main():
    """Main setup wizard."""
    print_header("ClawServant Setup Wizard")
    
    # Check if already configured
    if Path("credentials.json").exists():
        response = get_input("\ncredentials.json already exists. Reconfigure? (y/n)", "n")
        if response.lower() != "y":
            print("✅ Keeping existing configuration")
            return
    
    # Select provider
    print("\nSelect LLM provider(s):")
    print("  1) AWS Bedrock (Claude, Llama, Mistral)")
    print("  2) Anthropic (Direct Claude API)")
    print("  3) OpenAI (GPT-4, GPT-4o)")
    print("  4) Ollama (Local LLM)")
    print("  5) Multiple providers (with fallback)")
    
    choice = get_input("Choice (1-5)", "1")
    
    providers = []
    fallback_order = []
    
    if choice == "1":
        providers.append(setup_bedrock())
        fallback_order = ["bedrock"]
    elif choice == "2":
        providers.append(setup_anthropic())
        fallback_order = ["anthropic"]
    elif choice == "3":
        providers.append(setup_openai())
        fallback_order = ["openai"]
    elif choice == "4":
        providers.append(setup_ollama())
        fallback_order = ["ollama"]
    elif choice == "5":
        print("\n🔄 Multiple Providers (will try in order)")
        while True:
            sub_choice = get_input("\nAdd provider? (1=Bedrock, 2=Anthropic, 3=OpenAI, 4=Ollama, 0=Done)", "0")
            if sub_choice == "0":
                break
            elif sub_choice == "1":
                providers.append(setup_bedrock())
                if "bedrock" not in fallback_order:
                    fallback_order.append("bedrock")
            elif sub_choice == "2":
                providers.append(setup_anthropic())
                if "anthropic" not in fallback_order:
                    fallback_order.append("anthropic")
            elif sub_choice == "3":
                providers.append(setup_openai())
                if "openai" not in fallback_order:
                    fallback_order.append("openai")
            elif sub_choice == "4":
                providers.append(setup_ollama())
                if "ollama" not in fallback_order:
                    fallback_order.append("ollama")
    
    if not providers:
        print("❌ No providers selected")
        return
    
    # Build credentials
    credentials = {
        "providers": providers,
        "fallback_order": fallback_order
    }
    
    # Save credentials.json
    with open("credentials.json", "w") as f:
        json.dump(credentials, f, indent=2)
    print("\n✅ credentials.json created")
    
    # Create folders
    print("\n📁 Creating folders...")
    for folder in ["tasks", "results", "brain", "personality", "rules"]:
        Path(folder).mkdir(exist_ok=True)
    print("✅ Folders created (tasks/, results/, brain/, personality/, rules/)")
    
    # Test setup
    print("\n🧪 Testing setup...")
    try:
        result = subprocess.run(
            ["python3", "clawservant.py", "--status"],
            capture_output=True,
            timeout=10
        )
        if result.returncode == 0:
            print("✅ Setup verified!")
        else:
            print("⚠️  Provider not available yet (this is OK if credentials aren't active)")
    except Exception as e:
        print(f"⚠️  Could not test: {e}")
    
    # Success message
    print_header("✅ ClawServant Ready!")
    print("""
To start thinking:
  python3 clawservant.py --continuous

Or run a single task:
  python3 clawservant.py --task "Your task here"

Commands:
  python3 clawservant.py --status    # Check status
  python3 clawservant.py --memory    # View recent memories
  
Workflow:
  1. Drop task files in: tasks/
  2. ClawServant processes them
  3. Results saved to: results/
  4. Memory persisted to: memory.jsonl

For more help, see README.md
""")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup cancelled")
        sys.exit(1)