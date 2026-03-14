"""
Provider interface for AI model calls.
All providers must implement `generate(prompt, image_bytes) -> GenerationResult`.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class GenerationResult:
    text: str
    tokens_in: int = 0
    tokens_out: int = 0


class ModelProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, image_bytes: bytes, mime_type: str = "image/jpeg") -> GenerationResult:
        """Send a prompt + image and return a GenerationResult with text and token counts."""
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str: ...

    @property
    @abstractmethod
    def model_name(self) -> str: ...
