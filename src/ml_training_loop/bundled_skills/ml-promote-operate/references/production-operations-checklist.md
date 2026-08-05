# Production and operations checklist

## Immutable bundle

Include artifact and parent hashes, source and split manifests, label and execution contract, private specialists, feature names and schema, preprocessing and calibration, action and risk policy, code and environment, command and seeds, selection rule, walk-forward and confirmation records, supported universe, compatibility range, limitations, model card, owner, and rollback artifact.

Binary storage alone is not lineage.

## Shared decision core

Research replay and live should share bar normalization, feature or embedding creation, model loading, calibration, action policy, sizing, risk, and state transitions. Environment adapters may differ. Interface changes require consumer compatibility tests.

## Order state

Model:

intent -> submitted -> acknowledged -> partial or filled

and rejected, cancelled, or expired paths.

Handle duplicate requests and idempotency, partial fills, cancel-replace races, disconnect and reconnect, stale acknowledgements, session reconciliation, broker versus local mismatch, restart recovery, and contract roll. Never assume a fill before confirmation.

## Drift classes

- Data drift: source or input distribution or construction changed.
- Feature drift: representation or readout behavior changed.
- Concept drift: context-to-outcome relationship changed.
- Execution drift: fills, costs, or latency changed.
- Policy drift: serving configuration differs from approval.

Use rolling and reference windows appropriate to outcome frequency.

## Retraining

Triggers may be schedule, sufficient authenticated data, meaningful degradation, source change, or approved model update. Never auto-promote. Reproduce incumbent, retrain under the frozen process, compare champion and challenger on temporal OOS, certify parity, shadow, canary, approve, register, and preserve rollback.

## Circuit breakers

Keep stale or malformed data stops, non-finite model stops, duplicate-signal stops, order and fill divergence stops, trade and daily loss limits, exposure and margin limits, latency and connectivity stops, statistical alerts, and manual emergency stop outside the model.

## Incident response

Record identity, first affected time, evidence, expected and observed behavior, first mismatch, scope, risk impact, immediate action, root cause, control gap, fix, replay, reinstatement criteria, monitoring changes, and approval.

No backtest can waive parity, safety, or rollback.
