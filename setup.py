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
    """Get user input with optional default. Silent if EOF."""
    if default:
        display = f"{prompt} [{default}]: "
    else:
        display = f"{prompt}: "
    
    try:
        value = input(display).strip()
        return value if value else default
    except EOFError:
        # Piped mode - use default silently
        if default:
            return default
        raise RuntimeError(f"No input for: {prompt}")

def get_secret(prompt: str) -> str:
    """Get secret input (hidden)."""
    import getpass
    try:
        return getpass.getpass(prompt + ": ")
    except EOFError:
        raise RuntimeError(f"Cannot read secret in non-interactive mode: {prompt}")

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
    print("\n⚠️  You need AWS credentials (Access Key ID + Secret Access Key)")
    print("   Get them from: https://console.aws.amazon.com/iam/home?#/security_credentials")
    
    access_key = get_input("AWS Access Key ID", "")
    secret_key = get_secret("AWS Secret Access Key")
    region = get_input("AWS Region", "us-east-1")
    model_id = select_model("bedrock")
    
    return {
        "name": "bedrock",
        "enabled": True,
        "config": {
            "region": region,
            "model_id": model_id,
            "access_key": access_key,
            "secret_key": secret_key,
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
    
    # Show available providers
    print("\nAvailable LLM providers:")
    provider_list = []
    provider_map = {}
    setup_funcs = {
        "bedrock": setup_bedrock,
        "anthropic": setup_anthropic,
        "openai": setup_openai,
        "openrouter": setup_openrouter,
        "ollama": setup_ollama,
    }
    
    for i, (key, config) in enumerate(MODELS_DB.items(), 1):
        if key in setup_funcs:
            provider_list.append(key)
            provider_map[str(i)] = (key, setup_funcs[key])
            print(f"  {i}) {config['name']:30} - {config['description']}")
    
    print(f"  {len(provider_list)+1}) Multiple providers (with fallback)")
    print(f"  0) Exit")
    
    choice = get_input(f"Choice (0-{len(provider_list)+1})", "1")
    
    providers = []
    fallback_order = []
    
    if choice == "0":
        print("Cancelled")
        return
    elif choice == str(len(provider_list) + 1):
        # Multiple providers
        print("\n🔄 Multiple Providers (will try in order)")
        while True:
            print("\nAvailable providers:")
            for i, (key, config) in enumerate(MODELS_DB.items(), 1):
                if key in setup_funcs:
                    print(f"  {i}) {config['name']}")
            print("  0) Done")
            
            sub_choice = get_input("Add provider (0=Done)", "0")
            if sub_choice == "0":
                break
            elif sub_choice in provider_map:
                name, setup_func = provider_map[sub_choice]
                providers.append(setup_func())
                if name not in fallback_order:
                    fallback_order.append(name)
    elif choice in provider_map:
        # Single provider
        name, setup_func = provider_map[choice]
        providers.append(setup_func())
        fallback_order = [name]
    
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