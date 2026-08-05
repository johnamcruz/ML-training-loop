---
name: ml-design-experiment
description: Turn an ML idea into a frozen, falsifiable research contract and smallest valid experiment. Use before meaningful compute for a new or materially changed model, objective, specialist, label, policy, data universe, split, checkpoint, search family, or acceptance rule; when a run lacks an explicit falsifier or matched baseline; or when asked what ML experiment to run next.
---

# ML Experiment Design

Produce G0 evidence before costly compute.

## Gather facts

Inspect repository instructions, prior plans and decisions, source manifests, current artifacts, search history, and exposed date ranges. Do not ask the user for facts available in the environment.

When unresolved choices materially change the experiment, invoke $grilling and resolve one decision at a time with a recommended answer.

## Freeze the contract

Use assets/experiment-plan.md. Fill every section or write N/A with a reason.

1. State the decision, causal information set, mechanism, exact outcome, falsifiable claim, and stop or revise condition.
2. Freeze universe, sessions, roll rule, timestamp meaning, lookback, decision time, execution lag and price, horizon, target, stop, ambiguity, concurrency, costs, risk, and live interface.
3. Assign every date to research, inner selection, outer measurement, sealed confirmation, shadow, or live. Record prior exposure.
4. Lock comparison identity: rows, labels, splits, checkpoint and cache lineage, seed, budget, preprocessing, calibration, policy, costs, and metric code.
5. Declare the baseline ladder:
   - no-skill or base rate;
   - simple mechanical or linear model;
   - direct frozen representation;
   - one new component;
   - combination only after components work alone.
6. Define one primary metric, secondary constraints, diagnostics, required slices, and binding gate.
7. Declare search space and accounting before results. Prove categorical architecture choices before numeric refinement.
8. Name the exact integrity faults that stop immediately and the performance result that falsifies the claim.
9. Assign artifact ownership across data/representation, application-model, and deployment repositories.

## Preserve MVP speed

Plan the smallest authenticated slice, deterministic label proof, smoke, and one chronological OOS diagnostic. Do not add refactors, generalized infrastructure, unrelated heads, broad robustness suites, or production hardening unless they are required to interpret the result.

Promotion planning can be listed, but it must not block discovery.

## Gate verdict

G0 passes only when another developer can determine without oral context:

- what decision changes;
- what is observable and executable;
- what data selects and what remains untouched;
- what baseline and one component differ;
- what metric decides;
- what evidence stops, revises, or proceeds;
- which repository owns each artifact.

If a field changes after results, create a new experiment identity. Do not rewrite the original contract.

Read references/research-contract-checklist.md for detailed design checks.
