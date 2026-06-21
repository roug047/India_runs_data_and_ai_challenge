# Stage 4 — Honeypot Audit

Detects the ~80 "subtly impossible" honeypot profiles planted in the pool. The organizers
DISQUALIFY any submission with >10% honeypots in the top 100, so this is high-stakes —
but the bigger risk is **over-firing**: a false honeypot flag removes a real candidate from
the top 100 and costs NDCG. So this stage is precision-first.

## The exact patterns (README §7)

> "8 years of experience at a company founded 3 years ago; 'expert' proficiency in 10 skills
> with 0 years used. These are forced to relevance tier 0 in the ground truth."

~80 honeypots in 100K = **0.08%**. So the correct flag rate is tiny. If Stage 4 flags 5%+,
it's wrong — it's catching real people, not honeypots.

## Files

| File | Does |
|------|------|
| `honeypot_signals.py` | 7 impossibility signals → `honeypot_score` in (0,1], `is_likely_honeypot` if <0.15 |
| `40_run_honeypot.py` | Applies signals across the pool, writes scores into the feature table, runs a synthetic recall test + precision report |

## The 7 signals (all gross-impossibility only)

1. Single role longer than total experience +2yr, or >25 years — proxy for "8yr at a 3yr company".
2. Sum of role tenures grossly exceeds career length (×1.5 slack).
3. ≥4 advanced/expert skills with 0 months used — "expert in 10 skills, 0 years".
4. A single skill claimed >3yr beyond the entire career.
5. ≥2 roles whose `duration_months` disagrees with their own dates by >12mo.
6. YOE exceeds the career date-span by 4+ years.
7. Large skill list (≥8) ALL with zero duration.

## Calibration: why no mild-overrun signal

Real-data finding: "skill duration slightly exceeds career" fires on ~14% of candidates,
**including the genuine strong fit CAND_0000031**. So that mild pattern is deliberately NOT a
standalone signal — only gross, self-contradictory impossibilities count. Single decisive
signals push score <0.15; borderline ones (3 zero-duration expert skills) apply a soft 0.6
nudge that can't flag a clean candidate alone.

## Validation

- **Recall:** 5 synthetic impossible profiles, all flagged (score <0.15).
- **Precision:** 0% of the 50-row real sample flagged; CAND_0000031 (real fit) stays clean.

## Run

```bash
python stage4/40_run_honeypot.py --sample    # recall test + precision check
python stage4/40_run_honeypot.py             # full pool
```

After the full run, check `flag_rate_pct` in the report — it should be well under 1%. If it's
above ~3%, the script warns you: thresholds are catching real candidates and need loosening.

## Consumed downstream

- `honeypot_score` → Stage 5 (multiplies the final score, sinking honeypots) and Stage 7
  `rank.py` (final honeypot guard before the top 100).
- `is_likely_honeypot` → validator (keeps top-100 honeypot rate under the 10% DQ line).
