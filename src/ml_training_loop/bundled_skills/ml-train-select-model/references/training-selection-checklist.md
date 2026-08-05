# Training and selection checklist

## Optimization diagnosis

Inspect whether train loss moves, validation improves then degrades, the selected metric names the true best epoch, classes or scores collapse, gradients and embeddings remain finite, and learning differs by stream, side, or class.

More epochs are not evidence. Patience selects; it does not prove transfer.

## Objective choices

- Calibrated binary loss for event probability.
- Ordinal or survival loss for ordered barriers.
- Pairwise or listwise ranking for fixed-frequency selection.
- Regression or quantile loss for magnitude and uncertainty.
- Contrastive or reconstruction loss for representation learning.
- Multi-task only when each auxiliary has a retained, audited purpose.

Checkpoint selection must prioritize the deployed event. Ordered probabilities must be logically consistent.

## Imbalance and weighting

Report natural base rates and PR-AUC for rare events. Distinguish class, concurrency, stream, recency, and economic weights. Log the effective training distribution. Calibrate later on a population resembling deployment.

For multi-stream data, declare bar-proportional, uniform-stream, or staged curriculum and report samples seen per stream.

## Calibration

Fit on fold-safe later inner data. Report reliability bins and counts, Brier or log loss, slope, intercept, expected calibration error, and behavior by fold, stream, side, and base rate.

Long and Short experts are comparable only when event semantics and calibration populations match. If they do not, compare expected value in common units.

## Search exposure

Persist study identity, search space, sampler and pruner, seeds, trial states, objectives, constraints, data and split identity, configurations, metrics, selection reason, and prior manual trials. Large searches need selection-aware uncertainty.

## Architecture discipline

Give one specialist one auditable target and explicit output. Keep economic policy and execution separate. Dependency injection or deterministic mocks should catch side inversion, stale artifacts, stream mismaps, and schema drift.

Before adding a head, distinguish representation failure, extraction failure, calibration failure, and consumer or economic-policy failure.

## Uncertainty

Use fold and seed dispersion, block or session bootstrap, sparse-bin calibration uncertainty, and abstention for unsupported regions. Fit uncertainty methods on temporal calibration data and re-evaluate under shift.

## Checkpoint report

Persist best and final epoch, curves, per-stream diagnostics, control comparison, calibration, hash and parent, selected rule, seed dispersion, and regressions.
