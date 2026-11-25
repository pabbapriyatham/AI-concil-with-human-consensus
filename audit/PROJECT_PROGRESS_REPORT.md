# Mahthildis project progress

24 November 2026 · main at 4cd4ec5 · Advanced prototype

**Overall completion estimate: 64.5%.** The local product runs from a browser question through model fixtures, claim comparison, evidence, human correction and reuse. Its largest open question is whether these decisions improve accuracy on unseen material from real models. The user-facing confidence is explicitly raw.

| Component | Weight | Score | Weighted points |
|---|---:|---:|---:|
| User interface and input | 5 | 90% | 4.50 |
| Multi-model orchestration | 10 | 75% | 7.50 |
| Provider/API integration | 5 | 75% | 3.75 |
| Response normalization | 5 | 90% | 4.50 |
| Claim extraction | 10 | 50% | 5.00 |
| Claim comparison and contradiction detection | 10 | 50% | 5.00 |
| Evidence verification and RAG | 10 | 50% | 5.00 |
| Intelligent aggregation | 10 | 75% | 7.50 |
| Confidence and uncertainty | 10 | 50% | 5.00 |
| Human-in-the-loop validation | 5 | 75% | 3.75 |
| Persistent knowledge base and memory | 10 | 75% | 7.50 |
| Final synthesis and explainability | 5 | 75% | 3.75 |
| Evaluation and experiments | 5 | 50% | 2.50 |
| Engineering quality and reliability | 5 | 50% | 2.50 |

The supplied weights total 105. Their literal formula gives 67.75 weighted points out of 105. Dividing 6,775 by 105 produces 64.52%, rounded to 64.5%. No category was dropped. Scores are auditor judgments against the supplied anchors. A passing component status describes the demonstrated path, while the score measures the wider target. A 50 indicates an implemented core with material limitations. A 75 indicates an integrated, exercised path. A 90 indicates complete core behavior with narrower gaps.

## Separate progress measures

- **Software breadth: 14/14 (100%)** of specified components have executable code called by an application or evaluation entry point. For depth, the unweighted mean of component scores is **66.4%**. Breadth counts a component once regardless of maturity.
- **Functional verification: 10/16 (62.5%)** of specified audit acceptance checks passed. The denominator and each result are in TEST_RESULTS.md. The automated Python suite separately passed 38 of 39 collected items, with one skip. Neither ratio measures code coverage.
- **Research milestones: 3/8 (37.5%)** on an equally weighted checklist: implemented dataset and metric schema, reproducible fixture baseline runs, offline calibration experiment. Open: independently labeled evaluation set, uncached real-provider baselines, blinded human-memory study, out-of-sample deployment calibration, and uncertainty/significance analysis. These milestones measure the method and evidence, independently of software depth.

No external provider call was made. Live accuracy, billing and service behavior are NOT VERIFIED. See FEATURE_IMPLEMENTATION_MATRIX.md for evidence and DEVELOPMENT_ROADMAP.md for sequencing.
