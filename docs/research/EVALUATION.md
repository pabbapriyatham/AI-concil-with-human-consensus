# Reproducible evaluation

A: single provider. B: original anonymous-review council. C: claim graph and weighted
aggregation. D: C + evidence, confidence subsystem disabled. E: D + confidence.
F: E + prior validated-memory retrieval. Separate databases isolate ablations.

Run python -m scripts.evaluate for free development fixtures. --live opts into paid
configured providers; repeated consistency calls can add cost. Live synthetic registry
questions assess supplied-evidence handling, not real-world knowledge. Replace/extend
the dataset before substantive research. Mock chairman output is a fixture, not an
estimate of actual council synthesis performance.

Outputs: experiment.json, results.csv, reliability-A..F.svg. SQL stores experiment
config/dataset SHA-256/results and numeric metrics. Metrics include exact claim-set
correctness, abstention coverage, precision/recall/F1, contradiction/error detection,
Brier/ECE on answered examples, repeated prediction consistency, schema-coverage
explanation proxy, latency, tokens and known/unknown costs.

F uses synthetic oracle reviewer corrections for repeated facts; this is clearly labeled
and must not be reported as real human performance. Baselines lack comparable full
explanations/usage metadata. Confidence and explanation metrics are not substitutes
for independently labeled correctness or human usability studies.
