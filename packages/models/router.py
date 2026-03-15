"""
Model router — selects and returns a configured provider.
"""
from __future__ import annotations

import sys
from pathlib import Path

from provider import ModelProvider


def get_provider(provider: str = "gemini", model: str = "gemini-2.0-flash-lite") -> ModelProvider:
    """Return a configured model provider instance."""
    p = provider.lower()
    if p == "gemini":
        from gemini import GeminiProvider
        return GeminiProvider(model=model)
    if p == "lmstudio":
        from lmstudio import LMStudioProvider
        return LMStudioProvider(model=model)
    raise ValueError(f"Unknown model provider: {provider!r}. Supported: gemini, lmstudio")
