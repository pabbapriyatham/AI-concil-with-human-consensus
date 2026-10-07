# Architectural decisions

Preserve baseline APIs and frontend; new consensus logic lives in app/.
Keep structured relations independently testable; numeric conflicts require matching
subject/predicate/unit, and similarity alone never establishes truth.

Semantic backend: Sentence Transformers all-MiniLM-L6-v2 is optional. Hash ngram
vectors are an explicitly labeled offline development substitute, with limited
paraphrase recall. Windows application control blocked the installed SciPy DLL;
portable hashing avoids that dependency in offline execution.

NLI investigated: [DeBERTa model card](https://huggingface.co/MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli).
It combines MNLI/FEVER/ANLI training; entailment is directional and not evidence of
world truth. Named labels are required; opaque output orders are not guessed.
Actual downloaded model accuracy and domain transfer require separate experiments.

REST contracts: [OpenAI](https://developers.openai.com/api/reference/resources/chat),
[Gemini](https://ai.google.dev/api/generate-content),
[Anthropic](https://platform.claude.com/docs/en/api/messages).
Model IDs are configurable; adapter contract tests are not live availability tests.
