import os
from .base import ProviderError
from .http import HTTPProvider
from .mock import MockProvider


def get_provider(name: str):
    if os.getenv("DEV_MODE", "false").lower() == "true" or name == "mock":
        return MockProvider()
    if name not in {"openai", "gemini", "anthropic", "openrouter"}:
        raise ProviderError("Unsupported provider")
    return HTTPProvider(name)
