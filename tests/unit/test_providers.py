import asyncio

import httpx
import pytest

from app.providers.base import ProviderError
from app.providers.cache import ResponseCache
from app.providers.http import HTTPProvider
from app.providers.mock import MockProvider


def test_mock_and_cache():
    result = asyncio.run(MockProvider().generate("gemini", [{"role": "user", "content": "Eiffel Tower"}]))
    assert "1888" in result.text and result.metadata["mock"]
    cache = ResponseCache()
    cache.put("x", result)
    hit = cache.get("x")
    assert hit.metadata["cache_hit"] and hit.cost == 0
    assert "cache_hit" not in result.metadata


@pytest.mark.parametrize(
    "name,data,text",
    [
        (
            "openai",
            {
                "id": "1",
                "choices": [{"message": {"content": "yes"}}],
                "usage": {"prompt_tokens": 2, "completion_tokens": 1},
            },
            "yes",
        ),
        (
            "anthropic",
            {
                "id": "2",
                "content": [{"type": "text", "text": "yes"}],
                "usage": {"input_tokens": 2, "output_tokens": 1},
            },
            "yes",
        ),
        (
            "gemini",
            {
                "responseId": "3",
                "candidates": [{"content": {"parts": [{"text": "yes"}]}}],
                "usageMetadata": {"promptTokenCount": 2, "candidatesTokenCount": 1},
            },
            "yes",
        ),
    ],
)
def test_adapters(monkeypatch, name, data, text):
    for key in ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY"]:
        monkeypatch.setenv(key, "secret")
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(200, json=data)

    provider = HTTPProvider(name, httpx.MockTransport(handler))
    result = asyncio.run(provider.generate("fixture-model", [{"role": "user", "content": "Q"}]))
    assert result.text == text and result.input_tokens == 2 and result.cost is None
    assert requests and result.metadata["raw_payload"] == data


def test_failure_sanitized(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "secret")
    provider = HTTPProvider("openai", httpx.MockTransport(lambda _: httpx.Response(401)))
    with pytest.raises(ProviderError, match="HTTPStatusError") as exc:
        asyncio.run(provider.generate("m", []))
    assert "secret" not in str(exc.value)


def test_retry(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "secret")
    count = []

    def handler(_):
        count.append(1)
        if len(count) == 1:
            return httpx.Response(429, headers={"retry-after": "0"})
        return httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]})

    result = asyncio.run(HTTPProvider("openai", httpx.MockTransport(handler)).generate("m", []))
    assert result.metadata["retries"] == 1
