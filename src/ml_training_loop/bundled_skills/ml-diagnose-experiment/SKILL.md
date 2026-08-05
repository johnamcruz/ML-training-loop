---
name: ml-diagnose-experiment
description: Diagnose temporal ML crashes, hangs, slow runs, non-learning, overfitting, weak generalization, calibration collapse, checkpoint regression, per-stream failures, or disagreement between model metrics and economics. Use when an ML run fails or behaves unexpectedly, when a component learns its own target but does not improve the strategy, or when research, serialized, replay, and live results diverge. Freeze lineage, rule out integrity faults first, localize the first failed boundary, and propose one smallest matched falsifying test.
---

# ML Experiment Diagnosis

Diagnose before changing the experiment. Do not tune around an integrity fault.

## Freeze evidence

Capture exact command, logs, process state, code and config, environment, data and cache identities, checkpoint lineage, splits, seeds, metric artifacts, and latest successful boundary. Do not overwrite the failed run.

If the problem is an implementation bug, use $diagnosing-bugs after locating the ML boundary.

## Classify severity

- P0_BLOCKED: data, causality, label, split, lineage, non-finite, cache, or executable-parity fault. Stop compute and repair.
- P1_NO_PROMOTE: interpretable exploration, but missing controls, nested selection, calibration, uncertainty, costs, per-stream transfer, retention, or parity.
- P2_BACKLOG: speed, maintainability, broader observability, or infrastructure that does not invalidate evidence.
- PERFORMANCE_FAILURE: valid experiment falsified or underperformed. Do not call it infrastructure failure.

## Localize the first failed boundary

Follow:

data -> labels -> splits -> cache and row identity -> representation -> specialist extraction -> calibration -> economic policy -> simulation and costs -> production parity

Stop at the first boundary with evidence of failure. Later symptoms may be consequences.

## Diagnose common patterns

- Crash, NaN, shape, or load error: schema, masks, row map, cache completeness, dtype, device, environment.
- Training does not learn: label base rate, eligibility, feature variance, target-loss agreement, gradient flow, learning rate, capacity.
- Training strong, temporal OOS weak: leakage check, dependence and effective sample, search exposure, shift, overcapacity, wrong selection metric.
- Probe or specialist strong, economics weak: semantic target mismatch, wrong event population, stale or non-OOF score, calibration, consumer dilution, frequency, costs, execution.
- Pooled strong, primary stream weak: exposure and sampler, stream calibration, per-stream transfer; reject pooled-only promotion.
- SSL task improves, parent capability regresses: forgetting and native-checkpoint validation.
- Long and Short scores disagree: event semantics, base rates, calibration population, units, side routing.
- Research and replay differ: compare golden slice at data, transforms, encoder, specialist, calibration, policy, execution, and risk.

## Choose one diagnostic

Form competing hypotheses, rank by evidence, and run the smallest matched test that separates them. Keep rows, labels, splits, checkpoint, seed, budget, and evaluator fixed. Do not introduce a new architecture family before the failed boundary is understood.

## Output

Report:

- observed symptom and exact evidence;
- severity and maximum allowed lifecycle stage;
- first failed boundary;
- ruled-out explanations;
- most likely cause and confidence;
- one repair or falsifying test;
- conditions to resume;
- whether the original experiment remains valid, must be revised, or is invalid.

Read references/diagnostic-tree.md for the detailed decision tree. Read references/historical-integration-lessons.md when a specialist, multi-timeframe component, or representation appears useful alone but fails in the final consumer.
