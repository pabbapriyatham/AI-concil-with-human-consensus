"""42 controlled synthetic records. No invented real-world ground truth."""

import json
from pathlib import Path

categories = [
    "factual",
    "numerical",
    "temporal",
    "causal",
    "reasoning",
    "ambiguous",
    "conflicting-information",
]
rows = []
for category in categories:
    for i in range(6):
        identity = f"{category}-{i:02d}"
        subject = f"Registry item {category.replace('-', ' ')} {chr(65 + i)}"
        if category == "factual":
            good, bad = f"{subject} is enabled.", f"{subject} is not enabled."
        elif category == "numerical":
            good, bad = f"{subject} has {12 + i} units.", f"{subject} has {15 + i} units."
        elif category in {"temporal", "conflicting-information"}:
            good, bad = f"{subject} was completed in {2021 + i}.", f"{subject} was completed in {2020 + i}."
        elif category == "causal":
            good, bad = f"{subject} was caused by cooling.", f"{subject} was not caused by cooling."
        elif category == "reasoning":
            good, bad = f"{subject} totals {18 + i} units.", f"{subject} totals {22 + i} units."
        else:
            good = bad = f"{subject} may have been completed in 2021."
        ambiguous = category in {"ambiguous", "conflicting-information"}
        evidence_text = (
            "The supplied registry does not establish this item's status."
            if category == "ambiguous"
            else good
        )
        evidence = [
            {
                "text": evidence_text,
                "source": f"synthetic registry {identity}",
                "source_type": "dataset",
                "source_quality": 1,
                "provenance": {"synthetic": True},
            }
        ]
        if category == "conflicting-information":
            evidence.append(
                {
                    "text": bad,
                    "source": f"conflicting synthetic registry {identity}",
                    "source_type": "dataset",
                    "source_quality": 1,
                    "provenance": {"synthetic": True},
                }
            )
        rows.append(
            {
                "id": identity,
                "question": f"According to the supplied registry, what can be established about {subject}?",
                "ground_truth": None if ambiguous else good,
                "expected_claims": [] if ambiguous else [good],
                "evidence": evidence,
                "difficulty": "hard" if ambiguous else "easy",
                "category": category,
                "fixture_responses": [bad, bad, good],
                "provenance": "Authored controlled synthetic development fixture. Not real-model performance data.",
            }
        )
target = Path("datasets/development.jsonl")
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf8")
print(f"Wrote {len(rows)} synthetic examples to {target}")
