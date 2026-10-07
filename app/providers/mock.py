"""Deterministic fixtures, never pretending to answer arbitrary questions."""
from uuid import uuid4
from .base import ModelProvider, ProviderResult


class MockProvider(ModelProvider):
    name = "mock"

    async def generate(self, model, messages, **kwargs):
        question = messages[-1]["content"].lower()
        if "final ranking:" in question:
            text = "Fixture review.\nFINAL RANKING:\n1. Response A\n2. Response B\n3. Response C"
        elif "title:" in question:
            text = "Development example"
        elif "eiffel" in question:
            year = "1888" if "gemini" in model else "1889"
            text = f"The Eiffel Tower was completed in {year} and is located in Paris."
        else:
            text = "I cannot determine this from the development fixtures."
        return ProviderResult("mock", model, text, str(uuid4()), 0, 0, 0.0, 0.0,
                              {"mock": True, "prompt_version": "mock-v1"})
