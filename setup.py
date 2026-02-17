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
from typing import Dict, Any, List

# Load models database
SCRIPT_DIR = Path(__file__).parent
MODELS_FILE = SCRIPT_DIR / "models.json"

if not MODELS_FILE.exists():
    print("❌ Error: models.json not found")
    print(f"   Expected at: {MODELS_FILE}")
    print("   Make sure you cloned the full repository")
    sys.exit(1)

try:
    with open(MODELS_FILE) as f:
        MODELS_DB = json.load(f)
except json.JSONDecodeError as e:
    print(f"❌ Error: models.json is invalid JSON: {e}")
    sys.exit(1)

def print_header(text: str):
    """Print section header."""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)

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

def select_model(provider_key: str) -> str:
    """Let user select from available models."""
    models = MODELS_DB[provider_key]["models"]
    
    print(f"\n🤖 Available {MODELS_DB[provider_key]['name']} models:")
    for i, model in enumerate(models, 1):
        cost = f"({model['costTier']})" if model.get('costTier') else ""
        print(f"  {i:2}) {model['name']:30} {cost:15} - {model['description']}")
    print(f"  {len(models)+1}) Custom (enter ID manually)")
    
    while True:
        choice = get_input("Model choice", "1")
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(models):
                return models[idx]["id"]
            elif idx == len(models):
                return get_input("Model ID")
            else:
                print("Invalid choice")
        except ValueError:
            print("Please enter a number")

def setup_bedrock() -> Dict[str, Any]:
    """Configure AWS Bedrock."""
    print(f"\n🔧 {MODELS_DB['bedrock']['name']} Configuration")
    print(f"   {MODELS_DB['bedrock']['description']}")
    
    region = get_input("AWS Region", "us-east-1")
    model_id = select_model("bedrock")
    
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
    print(f"\n🔧 {MODELS_DB['anthropic']['name']} Configuration")
    print(f"   {MODELS_DB['anthropic']['description']}")
    
    api_key = get_secret("API Key (sk-ant-...)")
    model = select_model("anthropic")
    
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
    print(f"\n🔧 {MODELS_DB['openai']['name']} Configuration")
    print(f"   {MODELS_DB['openai']['description']}")
    
    api_key = get_secret("API Key (sk-...)")
    model = select_model("openai")
    
    return {
        "name": "openai",
        "enabled": True,
        "config": {
            "api_key": api_key,
            "model": model
        }
    }

def setup_openrouter() -> Dict[str, Any]:
    """Configure OpenRouter."""
    print(f"\n🔧 {MODELS_DB['openrouter']['name']} Configuration")
    print(f"   {MODELS_DB['openrouter']['description']}")
    
    api_key = get_secret("API Key (sk-or-...)")
    model = select_model("openrouter")
    
    return {
        "name": "openrouter",
        "enabled": True,
        "config": {
            "api_key": api_key,
            "model": model
        }
    }

def setup_ollama() -> Dict[str, Any]:
    """Configure Ollama."""
    print(f"\n🔧 {MODELS_DB['ollama']['name']} Configuration")
    print(f"   {MODELS_DB['ollama']['description']}")
    
    base_url = get_input("Base URL", "http://localhost:11434")
    model = select_model("ollama")
    
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
    print(f"\nWork directory: {Path.cwd()}")
    print("All files will be created here (credentials.json, memory.jsonl, etc.)")
    
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
    print("  4) OpenRouter (200+ models)")
    print("  5) Ollama (Local LLM)")
    print("  6) Multiple providers (with fallback)")
    
    choice = get_input("Choice (1-6)", "1")
    
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
        providers.append(setup_openrouter())
        fallback_order = ["openrouter"]
    elif choice == "5":
        providers.append(setup_ollama())
        fallback_order = ["ollama"]
    elif choice == "6":
        print("\n🔄 Multiple Providers (will try in order)")
        provider_map = {
            "1": ("bedrock", setup_bedrock),
            "2": ("anthropic", setup_anthropic),
            "3": ("openai", setup_openai),
            "4": ("openrouter", setup_openrouter),
            "5": ("ollama", setup_ollama),
        }
        
        while True:
            sub_choice = get_input("\nAdd provider? (1=Bedrock, 2=Anthropic, 3=OpenAI, 4=OpenRouter, 5=Ollama, 0=Done)", "0")
            if sub_choice == "0":
                break
            elif sub_choice in provider_map:
                name, setup_func = provider_map[sub_choice]
                providers.append(setup_func())
                if name not in fallback_order:
                    fallback_order.append(name)
    
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
            timeout=10,
            text=True
        )
        if result.returncode == 0:
            print("✅ Setup verified!")
        else:
            error_msg = result.stderr if result.stderr else "Unknown error"
            if "No LLM providers available" in error_msg:
                print("⚠️  Provider credentials not configured yet")
                print("   This is normal - configure them in credentials.json")
            else:
                print(f"⚠️  Setup test returned error (OK if credentials aren't active)")
                print(f"   Details: {error_msg[:100]}")
    except subprocess.TimeoutExpired:
        print("⚠️  Test timed out (provider may be slow)")
    except Exception as e:
        print(f"⚠️  Could not test: {e}")
        print("   You can test manually: python3 clawservant.py --status")
    
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