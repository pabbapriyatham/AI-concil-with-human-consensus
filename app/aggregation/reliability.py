from collections import defaultdict


class ReliabilityProfiles:
    """Empirical per-model/domain/category profiles with sample counts."""
    def __init__(self, observations=()):
        self.observations = list(observations)

    def observe(self, model, domain, category, correct):
        self.observations.append({"model": model, "domain": domain, "category": category, "correct": bool(correct)})

    def profile(self, model, domain="general", category="factual"):
        rows = [r for r in self.observations if r["model"] == model and r["domain"] == domain and r["category"] == category]
        correct = sum(r["correct"] for r in rows)
        return {"model": model, "domain": domain, "category": category, "samples": len(rows),
                "accuracy": correct / len(rows) if rows else None,
                "weight": (correct + 1) / (len(rows) + 2), "method": "beta-1-1-posterior"}

    def summary(self):
        keys = defaultdict(list)
        for row in self.observations:
            keys[(row["model"], row["domain"], row["category"])].append(row)
        return [self.profile(*key) for key in keys]
