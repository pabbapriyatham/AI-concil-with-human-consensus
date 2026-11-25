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

Without a memory file, offline F uses synthetic oracle reviewer corrections for
repeated facts and live F starts with empty memory. Pass `--memory PATH` to use
a frozen JSONL snapshot in F. Each line supplies `claim`, `reviewer`,
`explanation` and a nonempty `evidence` array using the API evidence schema.
Freeze reviews before reviewers see the evaluation labels. The export records
the memory mode and snapshot hash.
Repetitions bypass the response caches in both engines. The development dataset
explicitly labels contradictions in the scripted answers. Contradiction metrics
are unavailable for live answers and systems that do not emit claim relations.
A human study must measure correction effectiveness with independently reviewed
memory. Baselines lack comparable full explanations and usage metadata.

## Held-out live study

1. Freeze the independently sourced development, calibration and held-out
   question sets. Give each question a stable ID and record its provenance and
   source dossier. Group near-duplicate questions by source or fact before
   splitting. Preregister the domain, sample size, scoring rubric, error budget,
   minimum meaningful gain, and rules for provider failures and abstention.
2. Collect reviewed memory independently of the held-out answer keys. With an
   approved provider budget, run the experiment using the explicit holdout and
   the previously frozen memory. Fixture responses are optional in live data.

   ```powershell
   python -m scripts.evaluate --live --dataset held-out.jsonl --development-dataset development.jsonl --memory reviewed.jsonl --output artifacts/held-out
   python -m scripts.study prepare artifacts/held-out/experiment.json artifacts/held-out-review
   ```

3. Share `reviewer-packet.json` and the same independent reference dossier with
   two reviewers. Keep `private-key.json` and `experiment.json` with the
   coordinator. Each candidate presents the question and extracted answer claims
   without system IDs, benchmark labels, or confidence scores. Reviewers judge
   whether the claims collectively answer the question correctly and sufficiently
   according to the frozen rubric. An empty claim list is an abstention.
   Provider failures are counted as errors automatically. Wording and answer
   length can still provide clues about the originating system.
4. Each reviewer submits a JSON object with the packet's `study_id` and
   `packet_sha256`, a distinct `reviewer` name, and a `verdicts` object
   mapping all candidate IDs to `CORRECT` or `INCORRECT`. Submit the two
   judgments independently. The score command lists disputed IDs and exits 2
   until a third reviewer supplies judgments for exactly those IDs.

   ```powershell
   python -m scripts.study score artifacts/held-out-review/private-key.json reviewer-1.json reviewer-2.json pending.json
   python -m scripts.study score artifacts/held-out-review/private-key.json reviewer-1.json reviewer-2.json scored.json --adjudication reviewer-3.json
   ```

5. Report adjudicated accuracy with Wilson intervals, coverage, error rate among
   answered questions, provider failures, initial reviewer agreement, and raw
   confidence diagnostics. The report includes paired gains and exact McNemar
   tests for F against A, B and E, with a three-comparison correction. Assess
   the effect size against the preregistered target. A gain on one corpus does
   not establish reliability across domains, model revisions, or future traffic.

For calibration, repeat the review workflow on the calibration dataset under the
same model and memory configuration. Export the two scored studies with
`python -m scripts.study calibration scored-train.json scored-holdout.json observations.jsonl --system F`
and run `python -m scripts.calibrate observations.jsonl`. The exporter checks
dataset hashes, duplicate question fingerprints and IDs. Near-duplicates and
independent reviewer identity still require protocol controls.
