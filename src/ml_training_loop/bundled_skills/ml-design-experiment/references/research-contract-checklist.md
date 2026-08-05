# Research contract checklist

## Hypothesis grammar

At a declared decision event, causal information X should add matched chronological OOS information about exact outcome Y over baseline Z. Reject or revise when the predeclared metric, stability, or executable economics fail.

Avoid tool-first claims such as trying a larger model and desire-only claims such as increasing win rate.

## Decision-time table

Record:

lookback start -> final observable input -> decision/reference time -> first executable price -> target end

Decision cadence, lookback, prediction horizon, holding period, and retraining cadence are different quantities.

## Temporal roles

- Research or train: fit parameters.
- Inner validation: choose architecture, hyperparameters, epoch, calibration, and policy.
- Outer walk-forward: measure the frozen inner procedure once.
- Sealed holdout: open once after every choice and acceptance rule is frozen.
- Shadow or canary: confirm operations, not research selection.

Repeatedly inspected outer or holdout data becomes development data.

## Baseline and attribution

Only the hypothesized component changes. If checkpoint, label, universe, rows, target, or split changes, call it a diagnostic comparison rather than clean lift.

For stacked models, each upstream component needs its own target, calibration, OOF construction, mocked consumer contract, and matched incremental economic test.

## Search

Track strategy, trial family, trial, and run. Count manual, failed, pruned, restarted, and automated alternatives. Select architecture intent by domain reasoning, compare valid categorical alternatives, then refine numerical parameters. Confirmation begins only after freezing the winner.

## Metrics

Model: objective, discrimination, calibration, base rate, control lift, uncertainty.

Economic: exact event truth, count and effective sample, frequency, win rate, mean R after costs, turnover, exposure, drawdown, tails, and temporal or stream stability.

Operational: latency, resource budget, input rejection, parity, retraining, rollback.

Do not combine unrelated metrics into an opaque score unless terms and weights are declared.

## Stop rules

Stop immediately for unknown data or lineage, non-finite values, leakage, invalid split, impossible labels, or research/live timing mismatch. Performance misses can support one bounded diagnostic only when explicitly declared. Do not broaden scope while the active hypothesis remains unresolved.
