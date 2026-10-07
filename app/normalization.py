import copy
import re
import unicodedata

from .schemas import ModelResponse, TokenUsage, uid


def normalize_text(text: str) -> str:
    return re.sub(r"[ \t]+", " ", unicodedata.normalize("NFKC", text)).strip()


def normalize_response(result, question_id, prompt_version="answer-v1"):
    metadata = copy.deepcopy(result.metadata)
    metadata.update({"provider_response_id": result.response_id, "prompt_version": prompt_version})
    return ModelResponse(
        response_id=uid(),
        question_id=question_id,
        provider=result.provider,
        model=result.model,
        raw_text=result.text,
        normalized_text=normalize_text(result.text),
        latency=result.latency,
        token_usage=TokenUsage(input_tokens=result.input_tokens, output_tokens=result.output_tokens),
        cost=result.cost,
        metadata=metadata,
    )
