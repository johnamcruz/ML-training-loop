---
name: ml-rigor-workflow
description: Coordinate temporal or production ML work through ML-RIGOR gates from hypothesis to monitored deployment. Use when planning, resuming, reviewing, or promoting an ML experiment; when ownership or the current evidence gate is unclear; or when a task spans more than one of experiment design, data and labels, training, temporal validation, production, or monitoring.
---

# ML Rigor Workflow

Route the work; do not replace the proof owned by each stage.

## Start

1. Inspect repository instructions, current branch, run records, artifacts, processes, and evidence before asking questions.
2. Identify the exact decision being improved and the active lifecycle gate.
3. Assign ownership:
   - data and representation owners: authenticated sources, reusable encoders, and representation evidence;
   - application-model owners: labels, specialists, objectives, evaluation, and candidate bundles;
   - deployment owners: serving or execution adapters, safety, telemetry, replay, and rollback.
4. If a material design choice remains, use $grilling one decision at a time. Look up facts instead of asking for them.
5. Route to the narrowest stage skill:
   - G0: $ml-design-experiment
   - G1: $ml-audit-data-labels
   - G2 downstream training: $ml-train-select-model
   - G2 representation or SSL training: $ml-train-representation
   - G3 and G4: $ml-validate-temporal
   - failed or confusing evidence: $ml-diagnose-experiment
   - G5 and G6: $ml-promote-operate

## Preserve the evidence boundary

- Run the smallest causal end-to-end test that can falsify the claim.
- Interrupt an MVP only for a blocker or a data-integrity, causality, label, split, artifact-identity, or executable-contract fault.
- Put optional hardening, refactors, adjacent objectives, and production architecture in the backlog until the MVP produces useful evidence and is adopted.
- Change one causal component at a time. Hold rows, labels, splits, checkpoint lineage, seed, budget, calibration, policy, costs, and metrics fixed.
- Treat inspected selection or holdout evidence as development data.
- Never substitute training fit for temporal transfer, probe lift for economic edge, backtest edge for production parity, or uptime for model health.

## Gate sequence

| Gate | Required output | Failure action |
|---|---|---|
| G0 Research contract | Frozen hypothesis, timing, target, data roles, baselines, metrics, and stop rule | Clarify before compute |
| G1 Data and causality | Authenticated lineage, finite inputs, causal labels, split safety, cache identity, executable parity | Stop and repair |
| G2 MVP learnability | Stable optimization, selected checkpoint, controls, calibration, mocked consumer | Diagnose or revise |
| G3 Temporal transfer | Frozen recipe on untouched chronological outer folds | Revise or stop |
| G4 Economic validity | Exact executable economics with costs, frequency, dependence, and tail risk | Revise or stop |
| G5 Production parity | Immutable bundle and golden-slice research-to-live parity | Stop and repair |
| G6 Live promotion | Shadow/canary evidence, monitoring, risk controls, and proven rollback | Remain staged |

## End every meaningful run

Record:

- PROCEED, REVISE, STOP, INVALID, PROMOTE, or ROLLBACK;
- exact data, checkpoint, cache, code, config, split, seed, command, and artifact identities;
- per-fold and per-stream evidence, controls, uncertainty, and known limitations;
- the first failed boundary, if any;
- one authorized next experiment and actions not authorized;
- deferred cleanup and hardening.

Read references/lifecycle-map.md when sequencing work or deciding which gate owns a requirement. Read references/methods-catalog.md before introducing a new data source, model family, validation method, production technique, or agentic workflow. Read references/unattended-runs.md before launching or resuming long training, cache, walk-forward, or queue jobs.
