# Raw confidence and calibration

Raw claim confidence is the aggregation score, capped at .49 without supporting
evidence >=.5, .2 with strong contrary evidence, and .5 for subjective/uncertain claims.
Answer confidence averages supported candidates and scales by successful model coverage.
It is a heuristic score, not an empirically calibrated probability.

Calibration implements Brier score, ECE, reliability bins/SVG diagrams, isotonic PAV,
and regularized logistic Platt fitting. At least 10 train / 4 test observations with
disjoint IDs are required by the experiment helper, but much larger independent
samples are needed for defensible claims. JSON artifacts avoid unsafe pickle loads.
Calibration experiments persist in SQL and export diagnostics. No fitted calibrator
is automatically enabled in the production pipeline.

Evaluation calibration excludes abstentions: a successful refusal is not a factual
prediction with a correctness probability. A/B use an explicitly uninformative .5
baseline rather than inventing confidence from their text.
