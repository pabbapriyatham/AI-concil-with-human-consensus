import asyncio

from app.knowledge.store import Store
from app.orchestration import ConsensusEngine, ConsensusRequest
from app.orchestration.schemas import ModelSpec
from app.providers.base import ProviderError, ProviderResult


def test_failed_providers_consult_router_only_once(monkeypatch):
    monkeypatch.setenv("MAHTHILDIS_FALLBACK", "openrouter:openrouter/free")
    calls = []

    class Provider:
        def __init__(self, name):
            self.name = name

        async def generate(self, model, messages, **kwargs):
            calls.append(self.name)
            if self.name != "openrouter":
                raise ProviderError("quota exceeded")
            return ProviderResult("openrouter", model, "Paris is in France.", "fallback-1")

    request = ConsensusRequest(
        question="Fallback test unique question",
        models=[ModelSpec(provider="gemini", model="primary"), ModelSpec(provider="groq", model="fast")],
        allow_escalation=False,
    )
    result = asyncio.run(ConsensusEngine(Store("sqlite:///:memory:", initialize=True), Provider).run(request))
    assert calls == ["gemini", "groq", "openrouter"]
    assert len(result["responses"]) == 1
    assert result["responses"][0]["provider"] == "openrouter"
    assert len(result["errors"]) == 2


def test_legacy_uses_native_providers_and_one_fallback(monkeypatch):
    from backend import openrouter

    monkeypatch.setenv("MAHTHILDIS_FALLBACK", "openrouter:openrouter/free")
    calls = []

    class Provider:
        def __init__(self, name):
            self.name = name

        async def generate(self, model, messages, **kwargs):
            calls.append((self.name, model))
            if self.name != "openrouter":
                raise ProviderError("rate limited")
            return ProviderResult(self.name, model, "A real fallback answer", "legacy-1")

    monkeypatch.setattr(openrouter, "get_provider", Provider)
    result = asyncio.run(openrouter.query_models_parallel(
        ["gemini:primary", "groq:fast"], [{"role": "user", "content": "Unique legacy fallback"}]
    ))
    assert len(calls) == 3
    assert result["gemini:primary"]["provenance"]["provider"] == "openrouter"
    assert result["groq:fast"] is None
