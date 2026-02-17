"""
Provider abstraction layer for LLM access.

Supports: Bedrock, Anthropic, OpenAI, Ollama, and custom providers.
Auto-detects credentials and tries providers in fallback order.
"""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Base class for LLM providers."""
    
    @abstractmethod
    async def call(self, system_prompt: str, user_prompt: str, max_tokens: int = 500) -> str:
        """Call the LLM and return response text."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if this provider is available (credentials/config present)."""
        pass


class BedrockProvider(LLMProvider):
    """AWS Bedrock Claude provider."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.region = config.get("region", "us-east-1")
        self.model_id = config.get("model_id")
        self.access_key = config.get("access_key")
        self.secret_key = config.get("secret_key")
        self.client = None
    
    def is_available(self) -> bool:
        """Check if AWS credentials are configured in credentials.json."""
        # ONLY use credentials from config file (fully portable)
        if not (self.access_key and self.secret_key):
            return False
        
        try:
            import boto3
            self.client = boto3.client(
                "bedrock-runtime",
                region_name=self.region,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
            )
            # Client created successfully
            return True
        except Exception:
            return False
    
    async def call(self, system_prompt: str, user_prompt: str, max_tokens: int = 500) -> str:
        """Call Bedrock Haiku 4.5."""
        if not self.client:
            self.is_available()  # Initialize client
        
        try:
            response = self.client.converse(
                modelId=self.model_id,
                system=[{"text": system_prompt}],
                messages=[
                    {
                        "role": "user",
                        "content": [{"text": user_prompt}],
                    }
                ],
                inferenceConfig={
                    "maxTokens": max_tokens,
                    "temperature": 1,
                },
            )
            return response["output"]["message"]["content"][0]["text"]
        except Exception as e:
            raise RuntimeError(f"Bedrock call failed: {e}")


class AnthropicProvider(LLMProvider):
    """Anthropic Claude via direct API."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_key = config.get("api_key") or os.environ.get("ANTHROPIC_API_KEY")
        self.model = config.get("model", "claude-3-5-sonnet-20241022")
        self.client = None
    
    def is_available(self) -> bool:
        """Check if Anthropic API key is available."""
        if not self.api_key:
            return False
        try:
            from anthropic import Anthropic
            self.client = Anthropic(api_key=self.api_key)
            return True
        except Exception:
            return False
    
    async def call(self, system_prompt: str, user_prompt: str, max_tokens: int = 500) -> str:
        """Call Anthropic API."""
        if not self.client:
            self.is_available()
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ],
            )
            return response.content[0].text
        except Exception as e:
            raise RuntimeError(f"Anthropic call failed: {e}")


class OpenAIProvider(LLMProvider):
    """OpenAI GPT via direct API."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_key = config.get("api_key") or os.environ.get("OPENAI_API_KEY")
        self.model = config.get("model", "gpt-4o-mini")
        self.client = None
    
    def is_available(self) -> bool:
        """Check if OpenAI API key is available."""
        if not self.api_key:
            return False
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
            return True
        except Exception:
            return False
    
    async def call(self, system_prompt: str, user_prompt: str, max_tokens: int = 500) -> str:
        """Call OpenAI API."""
        if not self.client:
            self.is_available()
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ],
            )
            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"OpenAI call failed: {e}")


class OllamaProvider(LLMProvider):
    """Local Ollama instance."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_url = config.get("base_url", "http://localhost:11434")
        self.model = config.get("model", "llama2")
        self.client = None
    
    def is_available(self) -> bool:
        """Check if Ollama is running."""
        try:
            import requests
            resp = requests.get(f"{self.base_url}/api/tags", timeout=2)
            return resp.status_code == 200
        except Exception:
            return False
    
    async def call(self, system_prompt: str, user_prompt: str, max_tokens: int = 500) -> str:
        """Call local Ollama."""
        import requests
        
        try:
            prompt = f"{system_prompt}\n\n{user_prompt}"
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "num_predict": max_tokens,
                },
                timeout=120,
            )
            return response.json()["response"]
        except Exception as e:
            raise RuntimeError(f"Ollama call failed: {e}")


# Provider registry
PROVIDERS = {
    "bedrock": BedrockProvider,
    "anthropic": AnthropicProvider,
    "openai": OpenAIProvider,
    "ollama": OllamaProvider,
}


class ProviderManager:
    """Manages provider selection and fallback."""
    
    def __init__(self, credentials_file: Optional[Path] = None):
        # Default: credentials.json in current working directory
        if credentials_file is None:
            credentials_file = Path.cwd() / "credentials.json"
        self.credentials_file = credentials_file
        self.config = self._load_config()
        self.providers = self._init_providers()
        self.active_provider = None
    
    def _load_config(self) -> Dict[str, Any]:
        """Load credentials from file."""
        if not self.credentials_file.exists():
            return {
                "providers": [],
                "fallback_order": ["bedrock", "anthropic", "openai", "ollama"],
            }
        
        with open(self.credentials_file) as f:
            return json.load(f)
    
    def _init_providers(self) -> Dict[str, LLMProvider]:
        """Initialize available providers."""
        providers = {}
        provider_configs = {p["name"]: p["config"] for p in self.config.get("providers", [])}
        
        for name, provider_class in PROVIDERS.items():
            config = provider_configs.get(name, {})
            provider = provider_class(config)
            if provider.is_available():
                providers[name] = provider
        
        return providers
    
    async def call(self, system_prompt: str, user_prompt: str, max_tokens: int = 500) -> tuple[str, str]:
        """
        Call LLM with automatic provider fallback.
        
        Returns: (response_text, provider_name)
        """
        fallback_order = self.config.get("fallback_order", ["bedrock", "anthropic", "openai", "ollama"])
        
        for provider_name in fallback_order:
            if provider_name in self.providers:
                try:
                    self.active_provider = provider_name
                    response = await self.providers[provider_name].call(
                        system_prompt, user_prompt, max_tokens
                    )
                    return response, provider_name
                except Exception as e:
                    print(f"[warn] {provider_name} failed: {e}, trying next...")
                    continue
        
        raise RuntimeError(
            f"No LLM providers available.\n"
            f"Edit credentials.json with your API keys.\n\n"
            f"Run: python3 setup.py\n\n"
            f"All credentials must be stored in credentials.json (folder is self-contained)"
        )
    
    def status(self) -> Dict[str, Any]:
        """Get provider status."""
        return {
            "active_provider": self.active_provider,
            "available_providers": list(self.providers.keys()),
            "credentials_file": str(self.credentials_file),
            "config": self.config,
        }