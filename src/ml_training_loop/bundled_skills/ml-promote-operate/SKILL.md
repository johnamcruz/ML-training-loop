---
name: ml-promote-operate
description: Deterministically produce, package, hand off, deploy, monitor, retrain, or roll back a frozen ML candidate after temporal and economic gates pass. Use for model bundles, model cards, artifact manifests, golden-slice research-to-live parity, cross-repository compatibility, shadow or canary rollout, live monitoring, drift triage, incidents, champion-challenger retraining, or rollback. If any model, threshold, checkpoint, or policy choice remains, return to selection instead of producing.
---

# ML Promotion and Operations

Production continues the research contract. It does not choose a winner.

## Produce deterministically

1. Verify G3 and G4 decision records and frozen recipe identity.
2. Refit only on predeclared allowed dates.
3. Perform no architecture, checkpoint, threshold, or policy search.
4. Fail closed on missing lineage, incompatible schema, non-finite output, or parity mismatch.
5. Emit an immutable complete bundle and assets/model-card.md.

The bundle includes model weights, parent checkpoints, preprocessing, mappings, calibration, feature and output schemas, lookbacks, policy and risk config, data and label manifests, split schedule, code and environment, command and seeds, evidence reports, compatibility, limitations, owner, and rollback target.

Final representation bundles must not depend on temporary SSL heads, optimizer state, or trainer state.

## Certify parity

Persist a golden temporal slice with source bars, normalized inputs, embeddings, upstream scores, calibration, final decision, order parameters, and state transition.

Replay it through:

1. research evaluator;
2. serialized produced artifact;
3. production replay or live inference path.

Compare in order and stop at the first divergence:

data -> features -> encoder -> specialist -> calibration -> policy -> execution -> risk

## Roll out

Use offline parity, historical production replay, paper or shadow, minimal-risk canary, phased scale, then approved live.

Verify hashes, feed and session identity, freshness, warmup, account and positions, margin and limits, idempotency, order routing, kill switch, telemetry, and rollback before each stage.

## Monitor four layers

- Data: freshness, ordering, gaps, schema, sessions, contracts, provider divergence, non-finites, warmup.
- Model: input and embedding drift, score distribution, calibration, side and abstention rates, unsupported regions, specialist disagreement.
- Strategy: candidates, frequency, turnover, exposure, realized versus expected R, costs, drawdown, tails, per-stream performance.
- System: latency, errors, resources, queues, APIs, order rejection, reconciliation, risk events, and serving version.

## Diagnose drift

Classify data, feature, concept, execution, and policy drift. First rule out data and pipeline defects. Account for outcome count and confidence before declaring statistical degradation.

Detection does not authorize retraining. Retraining follows its declared trigger, reproduces the incumbent, runs temporal champion-challenger evidence, passes parity, returns through shadow and canary, and requires approval.

## Incident and rollback

Use assets/incident-report.md. Preserve evidence, identify the first failed contract boundary, reconcile state, use the known-good rollback when authorized, and define safe resumption conditions.

Read references/production-operations-checklist.md for bundle, rollout, order-state, drift, and safety details.
