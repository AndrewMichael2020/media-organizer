"""
LM Studio provider adapter using the local OpenAI-compatible API.
"""
from __future__ import annotations

import base64
import os

import httpx

from provider import GenerationResult, ModelProvider


class LMStudioProvider(ModelProvider):
    def __init__(self, model: str, base_url: str | None = None, api_key: str | None = None):
        self._model = model
        self._base_url = (base_url or os.environ.get("FMO_LMSTUDIO_BASE_URL") or "http://127.0.0.1:1234/v1").rstrip("/")
        # LM Studio usually accepts any key or none; keep this configurable.
        self._api_key = api_key or os.environ.get("LMSTUDIO_API_KEY") or os.environ.get("FMO_LMSTUDIO_API_KEY") or "lm-studio"

    @property
    def provider_name(self) -> str:
        return "lmstudio"

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
        image_b64 = base64.b64encode(image_bytes).decode("ascii")
        payload = {
            "model": self._model,
            "temperature": 0.1,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{image_b64}"}},
                    ],
                }
            ],
        }
        if max_output_tokens and max_output_tokens > 0:
            payload["max_tokens"] = max_output_tokens

        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        with httpx.Client(timeout=300.0) as client:
            response = client.post(f"{self._base_url}/chat/completions", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        choice = ((data.get("choices") or [{}])[0] or {}).get("message") or {}
        text = choice.get("content") or ""
        usage = data.get("usage") or {}
        return GenerationResult(
            text=text,
            tokens_in=int(usage.get("prompt_tokens") or 0),
            tokens_out=int(usage.get("completion_tokens") or 0),
        )
