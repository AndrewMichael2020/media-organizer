"""
Provider interface for AI model calls.
All providers must implement `generate(prompt, image_bytes) -> GenerationResult`.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class GenerationResult:
    text: str
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float | None = None


@dataclass
class BatchGenerationRequest:
    prompt: str
    image_bytes: bytes
    mime_type: str = "image/jpeg"
    max_output_tokens: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class BatchGenerationResult:
    result: GenerationResult | None = None
    error_message: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class ModelProvider(ABC):
    @abstractmethod
    def generate(
        self,
        prompt: str,
        image_bytes: bytes,
        mime_type: str = "image/jpeg",
        max_output_tokens: int | None = None,
    ) -> GenerationResult:
        """Send a prompt + image and return a GenerationResult with text and token counts."""
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str: ...

    @property
    @abstractmethod
    def model_name(self) -> str: ...

    def generate_batch(
        self,
        requests: list[BatchGenerationRequest],
        max_concurrent: int = 50,
    ) -> list[BatchGenerationResult]:
        raise NotImplementedError(f"{self.__class__.__name__} does not support app-side batch generation")
