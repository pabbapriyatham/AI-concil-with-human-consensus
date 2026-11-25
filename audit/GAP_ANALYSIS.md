# Gap analysis

| Feature | Current state | Target state | Missing work | Priority |
|---|---|---|---|---|
| Runtime configuration | Startup can succeed with invalid pricing. Blank pricing breaks execution. Local dotenv selects live/default. | Predictable mock demo and clear config errors | Validate pricing and model strings before requests, explicitly select demo mode | P0 |
| Claim and relation quality | Rule splitter, lexical similarity, numeric/negation matches | Atomic propositions and accurate directed relations on unseen text | Label compounds, units, time, negation and paraphrases; measure per-class errors | P0 |
| Research validity | Generated fixtures, cached repeats, category-derived contradiction truth, oracle memory | Independent judgments, fair repeated trials | Freeze splits, blind reviewers, label relations directly and bypass cache for repeats | P0 |
| Evidence trust | Context becomes stored, reusable evidence; source quality is caller supplied | Traceable scoped material with justified weights | Define source ownership, trust tiers and evidence eligibility | P0 for shared use |
| Retrieval | Entire eligible SQL corpus re-encoded/upserted per query | Incremental indexing and reliable retrieval | Index on change, test deletion/version handling and measure recall at k | P1 |
| Decision and confidence | Explanation available, fixed coefficients, raw scores | Calibrated, reviewable decisions | Fit on held-out splits, measure abstention and calibration against empirical correctness | P1 |
| Corrections | Append-only versions and current-only reuse, self-declared reviewer | Authenticated review, conflicts and retirement | Link identity, cross-entry conflicts and explicit supersession; verify race and failure recovery | P1 |
| Orchestration and operations | Shared cache/provider adapters, two similar modes, tests use mocks | Observable live failure behavior and maintainable deployment | Exercise isolated service stack, bound retry budgets, test restore, monitor capacity | P1 |
| Synthesis | Lists accepted claims and pooled sources | Reader can inspect support and refutation per conclusion | Expose matched excerpts and evidence verdict beside each claim | P2 |

## Five largest technical risks

1. **A misleading research result.** app/evaluation/runner.py injects gold into F and reuses cached C–F calls for consistency repeats. A/B do not get comparable repeated-observation measurements. Score differences cannot justify claims about real model or human performance.
2. **Semantic errors propagate into evidence and confidence.** RelationEngine.compare_text underlies both claim comparison and EvidenceEngine.assess. One missed contradiction can affect both agreement and source assessment. The on/off counterexample reproduced this limitation.
3. **Trust crosses requests.** ConsensusEngine persists plain request context and RetrievalService reads the global evidence pool. The shared bearer and typed reviewer name provide limited separation. Define ownership before multi-user deployment.
4. **Retrieval and graph work grow with corpus and response size.** RetrievalService.retrieve recomputes all eligible vectors for each query; RelationEngine.graph compares pairs. The 120-claim truncation retains earlier models first. Measure latency and representation by model.
5. **Partial writes and untested service recovery.** Evidence and review candidates commit before save_execution. ReviewService adds evidence to the catalog after the review transaction. Retries after failure can duplicate candidates or leave inconsistent visibility. Actual PostgreSQL/Qdrant recovery is unverified.

Reuse the browser UI, provider contracts, normalized records, review history, SSE and evaluation exports. The old chairman flow is valuable as a baseline. Avoid maintaining a second research decision implementation inside the legacy pipeline. Both transports already share adapters but keep separate caches.
