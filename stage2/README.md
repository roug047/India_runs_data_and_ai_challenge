# Stage 2 — Candidate Feature Engineering

Produces `features_100k.parquet`, the master table every downstream stage rides on. Pure
pandas/Python, no GPU. ~52 features per candidate, all recency keyed to the frozen Stage 0
reference date.

## The core idea (why this beats keyword-matching)

The JD's central instruction: *"A candidate who has all the AI keywords listed as skills but
whose title is 'Marketing Manager' is not a fit... if their career history shows they built a
recommendation system, they're a fit."* So requirement coverage blends two sources with
career evidence dominating:

```
coverage = 0.65 * career_description_evidence + 0.35 * (skill_list_claim * credibility)
```

And `credibility` is **lowered when on-platform assessment scores contradict the claimed
skills**. A candidate who lists "Milvus, advanced" but scores 38/100 on the assessment gets
their skill claims discounted. This is the mechanism that makes the keyword trap backfire.

## Files

| File | Role |
|------|------|
| `features_core.py` | Pure feature functions: requirement coverage, production evidence, trajectory, experience fit, title signal, education, behavioral availability, logistics |
| `disqualifiers.py` | The 7 JD disqualifier flags with rescue logic, aggregated to one `disqualifier_penalty` |
| `20_build_features.py` | Runner: streams candidates, writes the parquet + feature list + report |

## Run

```bash
python stage2/20_build_features.py --sample    # dry run on 50 rows first
python stage2/20_build_features.py             # full 100K -> features_100k.parquet
```

## Key feature groups (52 total)

- **Requirement coverage** (`cov_*`, `weighted_hard_req_coverage`, `weighted_soft_req_coverage`) — career-weighted, credibility-adjusted.
- **The trap signature** (`keyword_evidence_gap`, `hard_req_keyword_count` vs `hard_req_career_count`) — high skill keywords + low career evidence = stuffer.
- **Production evidence** (`production_evidence_score`, `shipped_relevant_system`) — JD's #1 priority.
- **Trajectory** (`services_ratio`, `consulting_penalty` recency-weighted, `pure_consulting_career`).
- **Disqualifiers** (7 flags + `disqualifier_penalty`, `disqualifier_hit`) — most-severe-wins aggregation, with rescue conditions so legit pivots aren't over-penalized.
- **Behavioral availability** (`availability_multiplier`, `days_inactive`, `recruiter_response_rate`) — JD explicitly asks to down-weight inactive/unresponsive candidates.
- **Logistics** (`location_score`, `notice_score`) — outside-India-won't-relocate ≈ 0.05.

## Validated on the sample

On the 50-row sample, a provisional score (preview of Stage 5) puts a real fit
(CAND_0000031: strong coverage, production evidence, preferred location) at rank 1, while the
two keyword-traps land at ranks 42 and 39 of 50. The trap backfires exactly as intended.

## Disqualifier rescue logic (so we don't over-fire)

- **cv_speech_robotics_only** fires only if CV/speech/robotics is heavy AND NLP/IR is thin.
- **langchain_only_under_12mo** fires only without substantial pre-LLM ML production.
- **pure_consulting_career** needs ~entire career at services firms (recent product stint rescues).
- **closed_source_no_validation** rescued by any open-source/paper/GitHub signal.

## Consumed downstream

- `features_100k.parquet` → Stage 3 (adds hybrid_score), Stage 4 (honeypot), Stage 5/6/7.
- `feature_list.json` → Stage 6 (LightGBM feature columns).
