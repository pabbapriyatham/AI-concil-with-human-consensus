"""Compatibility transport for the original council, using shared providers."""
import asyncio
import json
import logging
import os
from uuid import uuid4
from app.providers import get_provider, ProviderError
from app.providers.cache import ResponseCache

_cache = ResponseCache()
log = logging.getLogger('mahthildis.legacy')


async def query_model(model, messages, timeout=120.0):
    request_id = str(uuid4())
    key = _cache.key('openrouter', model, messages, 'council-v1', os.getenv('DEV_MODE'))
    try:
        result = _cache.get(key)
        if result is None:
            result = await get_provider('openrouter').generate(model, messages, timeout=timeout, request_id=request_id)
            _cache.put(key, result)
        return {'content': result.text,
                'reasoning_details': result.metadata.get('raw_payload', {}).get('choices', [{}])[0].get('message', {}).get('reasoning_details'),
                'provenance': {'response_id': result.response_id, 'provider': result.provider,
                               'latency': result.latency, 'input_tokens': result.input_tokens,
                               'output_tokens': result.output_tokens, 'cost': result.cost,
                               'cache_hit': result.metadata.get('cache_hit', False)}}
    except ProviderError as exc:
        log.warning(json.dumps({'request_id': request_id, 'stage': 'provider', 'model': model, 'error': str(exc)}))
        return None


async def query_models_parallel(models, messages):
    responses = await asyncio.gather(*(query_model(model, messages) for model in models))
    return dict(zip(models, responses))
