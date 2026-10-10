"""Compatibility transport for the original council, using shared providers."""

import asyncio
import json
import logging
import os
from uuid import uuid4

from app.orchestration.schemas import configured_fallback
from app.providers import ProviderError, get_provider
from app.providers.cache import ResponseCache
from app.tracing import request_context

_cache = ResponseCache()
log = logging.getLogger("mahthildis.legacy")


async def query_model(model, messages, timeout=120.0, allow_fallback=True):
    request_id = request_context.get() or str(uuid4())
    provider, model_id = model.split(":", 1) if ":" in model and model.split(":", 1)[0] in {
        "gemini", "groq", "openrouter", "openai", "anthropic", "mock"
    } else ("openrouter", model)
    key = _cache.key(provider, model_id, messages, "council-v1", os.getenv("DEV_MODE"))
    try:
        result = _cache.get(key)
        if result is None:
            result = await get_provider(provider).generate(
                model_id, messages, timeout=timeout, request_id=request_id
            )
            _cache.put(key, result)
        return {
            "content": result.text,
            "reasoning_details": result.metadata.get("raw_payload", {})
            .get("choices", [{}])[0]
            .get("message", {})
            .get("reasoning_details"),
            "provenance": {
                "response_id": result.response_id,
                "provider": result.provider,
                "model": result.model,
                "latency": result.latency,
                "input_tokens": result.input_tokens,
                "output_tokens": result.output_tokens,
                "cost": result.cost,
                "cache_hit": result.metadata.get("cache_hit", False),
            },
        }
    except ProviderError as exc:
        log.warning(
            json.dumps({"request_id": request_id, "stage": "provider", "model": model, "error": str(exc)})
        )
        fallback = configured_fallback()
        if allow_fallback and fallback and fallback.key != f"{provider}:{model_id}":
            response = await query_model(fallback.key, messages, timeout, allow_fallback=False)
            if response:
                response["provenance"]["fallback_for"] = model
            return response
        return None


async def query_models_parallel(models, messages):
    responses = dict(zip(models, await asyncio.gather(
        *(query_model(model, messages, allow_fallback=False) for model in models)
    )))
    fallback = configured_fallback()
    failed = [model for model, result in responses.items() if result is None]
    if failed and fallback and fallback.key not in models:
        replacement = await query_model(fallback.key, messages, allow_fallback=False)
        if replacement:
            replacement["provenance"]["fallback_for"] = failed[0]
            responses[failed[0]] = replacement
    return responses
