"""
DeepInfra provider adapter using the OpenAI-compatible chat completions API.
"""
from __future__ import annotations

import asyncio
import base64
import os
import time

import httpx

from provider import BatchGenerationRequest, BatchGenerationResult, GenerationResult, ModelProvider


class DeepInfraProvider(ModelProvider):
    def __init__(self, model: str, base_url: str | None = None, api_key: str | None = None):
        self._model = model
        self._base_url = (base_url or os.environ.get("FMO_DEEPINFRA_BASE_URL") or "https://api.deepinfra.com/v1/openai").rstrip("/")
        self._api_key = api_key or os.environ.get("DEEPINFRA_API_KEY") or os.environ.get("FMO_DEEPINFRA_API_KEY")
        if not self._api_key:
            raise RuntimeError("DeepInfra API key not set. Set DEEPINFRA_API_KEY or FMO_DEEPINFRA_API_KEY.")

    @property
    def provider_name(self) -> str:
        return "deepinfra"

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
        payload = self._build_payload(prompt, image_bytes, mime_type, max_output_tokens)
        data = self._post_with_backoff(payload, self._headers)
        return self._parse_generation_result(data)

    def generate_batch(
        self,
        requests: list[BatchGenerationRequest],
        max_concurrent: int = 100,
    ) -> list[BatchGenerationResult]:
        return asyncio.run(self._generate_batch_async(requests, max_concurrent=max_concurrent))

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._api_key}",
        }

    def _build_payload(
        self,
        prompt: str,
        image_bytes: bytes,
        mime_type: str,
        max_output_tokens: int | None,
    ) -> dict:
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
        return payload

    def _parse_generation_result(self, data: dict) -> GenerationResult:
        choice = ((data.get("choices") or [{}])[0] or {}).get("message") or {}
        text = choice.get("content") or ""
        if isinstance(text, list):
            text = "".join(part.get("text", "") for part in text if isinstance(part, dict))
        usage = data.get("usage") or {}
        cost = data.get("estimated_cost") or data.get("cost") or None
        try:
            cost_value = float(cost) if cost is not None else None
        except (TypeError, ValueError):
            cost_value = None
        return GenerationResult(
            text=str(text),
            tokens_in=int(usage.get("prompt_tokens") or 0),
            tokens_out=int(usage.get("completion_tokens") or 0),
            cost_usd=cost_value,
        )

    def _post_with_backoff(self, payload: dict, headers: dict) -> dict:
        delay = 1.0
        last_error: str | None = None
        with httpx.Client(timeout=300.0) as client:
            for attempt in range(5):
                response = client.post(f"{self._base_url}/chat/completions", json=payload, headers=headers)
                if response.status_code < 400:
                    return response.json()
                if response.status_code == 429 or 500 <= response.status_code < 600:
                    last_error = f"{response.status_code}: {response.text[:300]}"
                    if attempt < 4:
                        time.sleep(delay)
                        delay *= 2
                        continue
                response.raise_for_status()
        raise RuntimeError(f"DeepInfra request failed after retries: {last_error or 'unknown error'}")

    async def _generate_batch_async(
        self,
        requests: list[BatchGenerationRequest],
        *,
        max_concurrent: int,
    ) -> list[BatchGenerationResult]:
        semaphore = asyncio.Semaphore(max(1, max_concurrent))
        limits = httpx.Limits(max_connections=max(10, max_concurrent), max_keepalive_connections=max(10, max_concurrent))
        async with httpx.AsyncClient(timeout=300.0, limits=limits) as client:
            tasks = [
                self._generate_one_async(client, semaphore, request)
                for request in requests
            ]
            return list(await asyncio.gather(*tasks))

    async def _generate_one_async(
        self,
        client: httpx.AsyncClient,
        semaphore: asyncio.Semaphore,
        request: BatchGenerationRequest,
    ) -> BatchGenerationResult:
        async with semaphore:
            try:
                payload = self._build_payload(
                    request.prompt,
                    request.image_bytes,
                    request.mime_type,
                    request.max_output_tokens,
                )
                data = await self._post_with_backoff_async(client, payload, self._headers)
                return BatchGenerationResult(
                    result=self._parse_generation_result(data),
                    metadata=request.metadata,
                )
            except Exception as exc:
                return BatchGenerationResult(
                    error_message=str(exc),
                    metadata=request.metadata,
                )

    async def _post_with_backoff_async(
        self,
        client: httpx.AsyncClient,
        payload: dict,
        headers: dict,
    ) -> dict:
        delay = 1.0
        last_error: str | None = None
        for attempt in range(5):
            response = await client.post(f"{self._base_url}/chat/completions", json=payload, headers=headers)
            if response.status_code < 400:
                return response.json()
            if response.status_code == 429 or 500 <= response.status_code < 600:
                last_error = f"{response.status_code}: {response.text[:300]}"
                if attempt < 4:
                    await asyncio.sleep(delay)
                    delay *= 2
                    continue
            response.raise_for_status()
        raise RuntimeError(f"DeepInfra request failed after retries: {last_error or 'unknown error'}")
