---
name: ml-audit-data-labels
description: Audit temporal ML source data, features, labels, eligibility masks, OOF scores, and caches for authenticated lineage, causal observability, split safety, executable parity, non-finite values, overlap, and exact identity. Use before cache generation or reuse, training, walk-forward, replay, or production; when data or label code changes; when loading multi-stream or multi-timeframe data; or when leakage, corruption, row mismatch, cache drift, or label/backtest disagreement is suspected.
---

# ML Data and Label Audit

G1 is blocking. Diagnose read-only first and fail closed on uncertainty.

## Audit in order

1. Resolve the experiment contract. Do not invent missing decision, execution, target, ambiguity, session, or split semantics.
2. Authenticate source identity:
   - provider, schema, raw hashes, build code and config;
   - tickers, contracts, rolls, timeframes, sessions, timezone, and timestamp meaning;
   - ordering, duplicates, overlap, gaps, finite OHLCV, valid bar geometry, coverage, and append versus clean-rebuild parity.
3. Materialize the timeline for every example:
   - lookback;
   - final observable closed bar;
   - decision time;
   - first executable price;
   - full target reserve and resolution.
4. Prove label, simulator, and intended live parity for lag, fills, target, stop, gaps, same-bar collisions, timeout, sessions, rolls, costs, and censoring.
5. Verify every fitted transform, threshold, sampler, calibrator, and feature selector uses allowed training data only.
6. Verify stacked or specialist training inputs are genuinely OOF for every scored row.
7. Audit eligibility masks and exclusion reasons. Never silently remove losses, unresolved cases, difficult regimes, or missing sessions.
8. Report raw rows, class counts, base rates, distinct events and sessions, concurrency, uniqueness, effective sample size, and per-fold or per-stream coverage.
9. Authenticate cache identity and completeness. Reuse only on an exact content match.
10. Run deterministic path, boundary, symmetry, causality, and reference-parity tests.

## Stop conditions

Return P0_BLOCKED for:

- unknown, malformed, overlapping, duplicated, non-finite, or stale source data;
- future-observability or split-boundary violation;
- globally fitted transform or non-OOF stacked score;
- unresolved label/execution ambiguity;
- label, simulator, or live timing disagreement;
- mismatched source, checkpoint, row map, label, split, schema, code, or cache identity;
- partial cache or incomplete future reserve;
- consumed evidence represented as sealed.

Do not tune, rebuild downstream heads, or optimize performance around a G1 fault.

## Output

Emit a durable report with:

- PASS or P0_BLOCKED;
- exact identities and temporal contract;
- coverage and non-finite audit;
- label examples and parity results;
- concurrency and effective sample evidence;
- cache reuse verdict;
- first failed boundary and smallest repair;
- maximum authorized next stage.

Read references/data-label-gate.md for the full checklist.
