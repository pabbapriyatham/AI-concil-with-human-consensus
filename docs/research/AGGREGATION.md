# Aggregation

Four interchangeable strategies: majority baseline, empirical weighted agreement,
evidence-aware, knowledge-aware. The default is knowledge-aware, not majority.

Weighted profiles use observed model/domain/category outcomes with a Beta(1,1)
prior and visible sample counts; unknown profiles have no empirical accuracy.
Evidence-aware score: 0.15 + 0.25 agreement + 0.6 strongest source support -
0.6 strongest source contradiction - 0.2 model contradiction. Knowledge-aware adds
0.6 validated-memory support and subtracts 0.8 contrary validated memory.

Duplicate snippets from one source do not multiply support. Recency gently discounts
dated evidence over a ten-year scale; missing publication dates get no guessed age.
These coefficients are hypotheses, not learned optimal weights. Subjective/uncertain
claims are identified and confidence capped. Memory-derived candidates are excluded
from the model-vote denominator. Evidence and model agreement are separate factors.

Evidence text does not establish source authenticity; source quality is an input
estimate. Calibrate/compare weights on held-out data. Production model reliability
learning uses persisted labeled experiment observations, deduplicated by dataset
hash/example/model; profiles are neutral until matching domain/category outcomes
exist. Mock-model fixture observations never become real provider profiles.
