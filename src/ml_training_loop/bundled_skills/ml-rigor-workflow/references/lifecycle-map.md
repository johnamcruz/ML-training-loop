# ML-RIGOR lifecycle map

## Two speeds

MVP discovery tests one causal hypothesis cheaply: contract, representative authenticated data, simplest baseline, smoke, one temporal OOS diagnostic, one failure analysis, and one change.

Promotion evidence freezes all choices, uses nested temporal selection and untouched outer evidence, includes realistic costs and parity, produces immutable artifacts, and rolls out through shadow and canary.

MVP speed never weakens timing, labels, lineage, split isolation, or executable parity.

## Ownership

| Concern | Data/representation owner | Application-model owner | Deployment owner |
|---|---|---|---|
| Source data and integrity | Own | Consume authenticated artifacts | Consume approved feed or replay |
| Reusable representation learning | Own | Consume frozen identity | Do not silently retrain |
| Application labels, rewards, and objectives | Prohibited unless reusable | Own | Consume approved contract |
| Specialist, policy, or economic models | Reusable outputs only | Own | Load produced bundle |
| Temporal selection and evaluation | Representation evidence only | Own | Replay for parity |
| Serving or execution, safety, risk, and live state | Interfaces only | Simulate intended contract | Own |

## Evidence layers

1. Model: loss, discrimination, calibration, base rates, controls, uncertainty.
2. Economic: exact target-first truth, mean R, costs, frequency, turnover, drawdown, tails, temporal and stream stability.
3. Operational: latency, freshness, rejection, feature parity, score drift, fills, risk, and service health.

Each layer answers a different question.

## Severity

- P0 integrity blocker: unknown or invalid data or lineage, non-finite inputs, leakage, timing or split violation, executable mismatch, partial or mismatched cache, consumed holdout presented as sealed. Stop.
- P1 evidence blocker: exploration may continue, but confirmation or promotion lacks nested selection, controls, effective-sample evidence, calibration, uncertainty, costs, per-stream results, retention, parity, or rollout safeguards.
- P2 backlog: maintainability, scale, advanced methods, and infrastructure that do not invalidate the active result.

Missing effective-sample reporting is P1 for a safe smoke. Overlap that crosses splits or invalidates the claim is P0.

## Required immutable graph

source data -> eligibility and labels -> features or embeddings -> upstream scores -> calibration -> policy -> simulation -> produced bundle -> live adapter

Every edge carries row identity, temporal semantics, schema, parent hashes, code/config identity, and compatibility rules.

## Search and evidence ledger

Track strategy, trial family, trial, and run separately. Count manual, failed, retried, pruned, and automated alternatives. Tag every period as research, inner selection, outer evaluation, sealed confirmation, shadow, or live. Once a period influences a decision, it is consumed development evidence.

## Exceptions

Write an exception before affected evidence. State rule, scope, reason, risk, compensating evidence, approver, and expiry. Never waive leakage, unknown lineage, misleading holdout status, or research/live incompatibility.
