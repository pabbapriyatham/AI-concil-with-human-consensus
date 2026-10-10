"""Keep deterministic tests independent of workstation credentials and model selection."""

import pytest


@pytest.fixture(autouse=True)
def isolated_provider_settings(monkeypatch):
    monkeypatch.setenv(
        "MAHTHILDIS_MODELS",
        "openai:gpt-5.1,gemini:gemini-3-pro-preview,anthropic:claude-sonnet-4-5",
    )
    monkeypatch.setenv("MAHTHILDIS_FALLBACK", "")
