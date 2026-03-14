"""
Gemini provider adapter using google-genai SDK.
"""
from __future__ import annotations

import json
import os

from google import genai
from google.genai import types

from provider import ModelProvider, GenerationResult
from schemas import ImageExtractionOutput


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

    def generate(
        self,
        prompt: str,
        image_bytes: bytes,
        mime_type: str = "image/jpeg",
        max_output_tokens: int | None = None,
    ) -> GenerationResult:
        contents = [
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
            prompt,
        ]
        try:
            # Best case: let the SDK/model enforce the schema directly.
            response = self._client.models.generate_content(
                model=self._model,
                contents=contents,
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    response_mime_type="application/json",
                    response_schema=ImageExtractionOutput,
                    max_output_tokens=max_output_tokens,
                ),
            )
        except Exception:
            try:
                # Some preview models reject schema mode but still handle JSON mode.
                response = self._client.models.generate_content(
                    model=self._model,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        temperature=0.1,
                        response_mime_type="application/json",
                        max_output_tokens=max_output_tokens,
                    ),
                )
            except Exception:
                # Final fallback: plain generation, then local repair/parsing.
                response = self._client.models.generate_content(
                    model=self._model,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        temperature=0.1,
                        max_output_tokens=max_output_tokens,
                    ),
                )
        tokens_in = 0
        tokens_out = 0
        if response.usage_metadata:
            tokens_in = response.usage_metadata.prompt_token_count or 0
            tokens_out = response.usage_metadata.candidates_token_count or 0
        parsed = getattr(response, "parsed", None)
        text = response.text or ""
        if parsed is not None:
            if hasattr(parsed, "model_dump_json"):
                text = parsed.model_dump_json()
            else:
                text = json.dumps(parsed)
        return GenerationResult(
            text=text,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
        )
