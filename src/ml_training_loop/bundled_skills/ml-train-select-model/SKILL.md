---
name: ml-train-select-model
description: Train, calibrate, compare, and select a supervised or downstream ML model using only research and inner-selection data. Use for model baselines, downstream heads, specialists, epoch or patience choices, imbalance handling, calibration, checkpoint selection, architecture grids, Optuna, or hyperparameter search after the research contract and data-label gate pass. Do not use outer folds or sealed holdouts to tune.
---

# ML Training and Selection

Produce a frozen recipe, not a generalization or promotion claim.

## Preconditions

Require a passed G0 contract and G1 data-label audit. Freeze data, rows, labels, temporal roles, checkpoint and cache lineage, seed plan, budget, costs, and metric implementation.

## Train in this order

1. No-skill or base-rate baseline.
2. Simple linear, logistic, tree, persistence, or mechanical baseline.
3. Direct frozen representation model.
4. One new specialist or context component.
5. Combined architecture only after each required component works and has a mocked consumer test.

Complexity must earn matched evidence.

## Fold-safe pipeline

Fit inside each training role:

- normalization and imputation;
- feature selection or dimensionality reduction;
- sampling, class or uniqueness weights;
- data-derived label thresholds;
- model parameters and early stopping;
- calibration;
- score-to-action policy.

Validation used for early stopping, calibration, or policy is selection data.

## Training contract

Predeclare objective, selection metric, tie breaker, minimum evidence budget, maximum epochs, patience, calibration protocol, seed plan, resource ceiling, and retained capabilities.

Log every epoch with train and validation objective, learning rate, task metrics, effective exposure, throughput, best marker, and early-stopping state. Save the best checkpoint atomically and support exact resume.

Match loss to the deployed question. Calibration cannot repair missing discrimination. Scores in the interval zero to one are not comparable unless they predict the same event, population, horizon, units, costs, and loss convention.

## Search

1. Validate target and baseline.
2. Prove mandatory components independently.
3. Compare declared categorical architecture choices fairly.
4. Refine numeric parameters.
5. Rerun finalists across seeds and inner folds.
6. Freeze the recipe before outer evaluation.

Log all manual, completed, failed, retried, and pruned trials. Prune only after a declared minimum budget and record why.

## G2 verdict

Proceed to temporal evaluation only when:

- optimization is finite, stable, and reproducible;
- the model beats its declared no-skill or control on selection data;
- checkpoint selection followed the frozen rule;
- score semantics and calibration are valid;
- every required side, stream, and class remains represented;
- the serialized model works through a deterministic mocked consumer.

Weak performance may justify one small temporal diagnostic only when explicitly labeled. It cannot support promotion.

Read references/training-selection-checklist.md for detailed diagnostics.
