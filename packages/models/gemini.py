"""
Gemini provider adapter using google-genai SDK.
"""
from __future__ import annotations

import os

from google import genai
from google.genai import types

from provider import ModelProvider, GenerationResult


class GeminiProvider(ModelProvider):
    def __init__(self, model: str = "gemini-3.1-flash-lite-preview", api_key: str | None = None):
        self._model = model
        key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("FMO_GEMINI_API_KEY")
        if not key:
            raise RuntimeError(
                "Gemini API key not set. Set GEMINI_API_KEY or FMO_GEMINI_API_KEY env var."
            )
        self._client = genai.Client(api_key=key)

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def model_name(self) -> str:
        return self._model

    def generate(self, prompt: str, image_bytes: bytes, mime_type: str = "image/jpeg") -> GenerationResult:
        response = self._client.models.generate_content(
            model=self._model,
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                prompt,
            ],
        )
        tokens_in = 0
        tokens_out = 0
        if response.usage_metadata:
            tokens_in = response.usage_metadata.prompt_token_count or 0
            tokens_out = response.usage_metadata.candidates_token_count or 0
        return GenerationResult(
            text=response.text or "",
            tokens_in=tokens_in,
            tokens_out=tokens_out,
        )
