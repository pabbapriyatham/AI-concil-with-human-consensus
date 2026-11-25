"""Native REST adapters with bounded retries and redacted errors."""

import asyncio
import json
import logging
import os
import time

import httpx

from .base import ModelProvider, ProviderError, ProviderResult
from .pricing import configured_prices

log = logging.getLogger("mahthildis.providers")


class HTTPProvider(ModelProvider):
    def __init__(self, name: str, transport=None, retries: int = 2):
        self.name, self.transport, self.retries = name, transport, retries

    def request(self, model, messages):
        keys = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "gemini": "GEMINI_API_KEY",
            "openrouter": "OPENROUTER_API_KEY",
            "groq": "GROQ_API_KEY",
        }
        key = os.getenv(keys[self.name])
        if not key:
            raise ProviderError(f"{self.name}: missing credential")
        if self.name in {"openai", "openrouter", "groq"}:
            url = {
                "openai": "https://api.openai.com/v1/chat/completions",
                "openrouter": "https://openrouter.ai/api/v1/chat/completions",
                "groq": "https://api.groq.com/openai/v1/chat/completions",
            }[self.name]
            return url, {"Authorization": f"Bearer {key}"}, {"model": model, "messages": messages}
        if self.name == "anthropic":
            system = "\n".join(m["content"] for m in messages if m["role"] == "system")
            payload = {
                "model": model,
                "max_tokens": 2048,
                "messages": [m for m in messages if m["role"] != "system"],
            }
            if system:
                payload["system"] = system
            return (
                "https://api.anthropic.com/v1/messages",
                {"x-api-key": key, "anthropic-version": "2023-06-01"},
                payload,
            )
        system = "\n".join(m["content"] for m in messages if m["role"] == "system")
        payload = {
            "contents": [
                {"role": "model" if m["role"] == "assistant" else "user", "parts": [{"text": m["content"]}]}
                for m in messages
                if m["role"] != "system"
            ]
        }
        if system:
            payload["systemInstruction"] = {"parts": [{"text": system}]}
        return (
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            {"x-goog-api-key": key},
            payload,
        )

    def parse(self, data, model, latency):
        if self.name in {"openai", "openrouter", "groq"}:
            text = data["choices"][0]["message"].get("content")
            usage = data.get("usage", {})
            inp, out = usage.get("prompt_tokens"), usage.get("completion_tokens")
            response_id = data.get("id", "")
        elif self.name == "anthropic":
            text = "\n".join(b["text"] for b in data.get("content", []) if b["type"] == "text")
            usage = data.get("usage", {})
            inp, out = usage.get("input_tokens"), usage.get("output_tokens")
            response_id = data.get("id", "")
        else:
            parts = data["candidates"][0]["content"]["parts"]
            text = "\n".join(p.get("text", "") for p in parts if not p.get("thought"))
            usage = data.get("usageMetadata", {})
            inp, out = usage.get("promptTokenCount"), usage.get("candidatesTokenCount")
            response_id = data.get("responseId", "")
        if not isinstance(text, str) or not text.strip():
            raise ProviderError(f"{self.name}: empty or blocked response")
        # Prices are configured, never guessed. Rates are USD per million tokens.
        rates = configured_prices().get(f"{self.name}:{model}")
        cost = (
            (inp * rates["input"] + out * rates["output"]) / 1e6
            if rates and inp is not None and out is not None
            else None
        )
        return ProviderResult(
            self.name,
            model,
            text,
            response_id,
            inp,
            out,
            latency,
            cost,
            {
                "raw_payload": data,
                "model_version": data.get("modelVersion", data.get("model")),
                "prompt_version": "council-v1",
            },
        )

    async def generate(self, model, messages, timeout=60.0, request_id="", **kwargs):
        url, headers, payload = self.request(model, messages)
        if self.name == "openai":
            payload["max_completion_tokens"] = 2048
        elif self.name in {"openrouter", "groq"}:
            payload["max_tokens"] = 2048
        elif self.name == "gemini":
            payload["generationConfig"] = {"maxOutputTokens": 2048}
        start = time.perf_counter()
        try:
            async with asyncio.timeout(timeout):
                async with httpx.AsyncClient(timeout=timeout, transport=self.transport) as client:
                    for attempt in range(self.retries + 1):
                        try:
                            response = await client.post(url, headers=headers, json=payload)
                            if response.status_code in {429, 500, 502, 503, 504} and attempt < self.retries:
                                try:
                                    delay = min(
                                        5.0, max(0.0, float(response.headers.get("retry-after", 2**attempt)))
                                    )
                                except ValueError:
                                    delay = 2**attempt
                                log.info(
                                    json.dumps(
                                        {
                                            "request_id": request_id,
                                            "stage": "retry",
                                            "provider": self.name,
                                            "model": model,
                                            "attempt": attempt + 1,
                                        }
                                    )
                                )
                                await asyncio.sleep(delay)
                                continue
                            response.raise_for_status()
                            result = self.parse(response.json(), model, time.perf_counter() - start)
                            result.metadata["retries"] = attempt
                            return result
                        except httpx.TransportError:
                            if attempt == self.retries:
                                raise
                            await asyncio.sleep(min(2**attempt, 5))
        except ProviderError:
            raise
        except (httpx.HTTPError, TimeoutError, AttributeError, KeyError, IndexError, ValueError, TypeError) as exc:
            # Exception strings can contain URLs/headers/credentials; expose only the class.
            raise ProviderError(f"{self.name}: {type(exc).__name__}") from None
        raise ProviderError(f"{self.name}: retry budget exhausted")
