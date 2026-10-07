"""Provider-independent contract; raw payloads stay available for auditing."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncIterator


class ProviderError(RuntimeError):
    """Sanitized provider failure, safe for logs."""


@dataclass
class ProviderResult:
    provider: str
    model: str
    text: str
    response_id: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    latency: float = 0.0
    cost: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class ModelProvider(ABC):
    @abstractmethod
    async def generate(self, model: str, messages: list[dict], **kwargs) -> ProviderResult:
        """Produce one response."""

    async def stream(self, model: str, messages: list[dict], **kwargs) -> AsyncIterator[str]:
        """Buffered stream fallback. Native token streaming may override this."""
        yield (await self.generate(model, messages, **kwargs)).text

    def get_model_info(self, model: str) -> dict:
        return {"provider": self.name, "model": model, "streaming": "buffered"}
