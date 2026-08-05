---
name: ml-validate-temporal
description: Evaluate a frozen ML recipe with chronological outer folds, sealed confirmation, matched controls, calibration, dependence-aware uncertainty, exact simulation, costs, and per-stream economics. Use for walk-forward, temporal OOS, holdout, backtesting, representation transfer, checkpoint comparison, strategy profitability, ablations, or RL sim-to-real evidence after all selection choices are frozen. Never tune on evaluated rows.
---

# ML Temporal Validation

Measure future-like behavior without changing the recipe.

## Preconditions

Require G0, G1, and G2 artifacts. Hash the frozen recipe, data, labels, rows, splits, checkpoint, preprocessing, calibration procedure, policy, costs, seeds, and evaluator.

## Evaluate chronologically

1. Run inner selection only inside each outer training window.
2. Refit the frozen selected recipe on allowed outer training data.
3. Purge unresolved outcomes at every boundary and embargo when split topology requires it.
4. Score the untouched outer interval once.
5. Record every date inspected. Open a sealed holdout once after all choices and gates are frozen.

## Preflight

Before expensive simulation, verify:

- timing: every feature, upstream score, and execution price is available;
- coverage: rows, classes, dates, streams, missingness, and exclusions match;
- intensity: candidates, trades per day, turnover, and overlap are plausible.

## Matched evidence

Compare no-skill, simple baseline, direct frozen representation, incumbent, candidate, shuffle or random control, and component-off ablation as appropriate.

Hold rows, labels, folds, seeds, budget, calibration, policy, costs, and metric code fixed. When eligibility changes, report both common-row attribution and the full-system effect.

## Report

Show each outer fold and aggregate; ticker, timeframe, side, session, and regime; counts, base rates, effective sample, and uncertainty; exact primary truth; discrimination and calibration; frequency and score quantiles; mean R before and after costs; turnover, exposure, drawdown, tails, and temporal worst case.

If the objective is exact target-before-stop, report that event rather than eventual MFE or another proxy.

Separate evaluation modes:

- representation learning: objective diagnostics, frozen representation access, controls, retention, and per-stream or per-domain transfer;
- supervised learning: exact application outcomes, calibration, policy or decision utility, and simulation where relevant;
- reinforcement learning: production-semantic replay, environment parity, actions, rewards, latency, safety, and risk.

## Decision

Use assets/run-decision.md and record PROCEED, REVISE, STOP, INVALID, PROMOTE, or ROLLBACK. A pooled win, tiny sample, one dominant fold, narrow parameter optimum, or hidden search exposure does not pass G3 or G4.

Read references/temporal-validation-checklist.md for simulation and acceptance details.
