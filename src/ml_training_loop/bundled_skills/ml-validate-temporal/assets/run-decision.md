# Run Decision: `<experiment ID / candidate>`

> Complete after every experiment that affects the project direction. This is
> the durable handoff and evidence record.

## 1. Decision

- Date:
- Owner:
- Process version: `ML-RIGOR-v1`
- Status: `PROCEED | REVISE | STOP | INVALID | PROMOTE | ROLLBACK`
- One-sentence decision:
- Next authorized action:
- Actions explicitly not authorized:

## 2. Contract and identity

- Experiment plan:
- Strategy / trial family / trial / run:
- Exploration/selection/confirmation/production:
- Code commit(s):
- Environment lock:
- Config hash:
- Data manifest/hash:
- Label and execution contract hash:
- Eligibility mask/hash:
- Foundation checkpoint or representation hash:
- Private model/checkpoint hash:
- Cache hash:
- Split schedule:
- Seeds:
- Command/log:

## 3. Integrity results

| Check | Result | Evidence |
|---|---|---|
| Source/continuous-data integrity | | |
| Finite inputs | | |
| Label path fixtures | | |
| Vectorized/reference parity | | |
| Decision/execution/outcome timing | | |
| Purge/embargo | | |
| OOF specialist construction | | |
| Cache identity/completeness | | |
| Label/simulator parity | | |

Any G1 fault is blocking.

## 4. Data and effective sample

- Raw eligible rows:
- Positive/base rate:
- Trades/candidates:
- Distinct days/sessions:
- Average/max concurrency:
- Effective sample size:
- Censoring/exclusion:
- Coverage by fold/stream:

## 5. Training result

- Best epoch and selection metric:
- Final epoch:
- Train/validation behavior:
- Control/shuffle result:
- Calibration:
- Seed dispersion:
- Retention regression, if applicable:
- Training anomalies:

## 6. Temporal OOS results

| Fold | Stream/side | N | Signals/day | Primary model metric | Win rate | Mean R net | Drawdown/tail | Calibration | Notes |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| | | | | | | | | | |

Aggregate:

- Primary metric:
- Net expectancy:
- Win rate:
- Average winning/losing R:
- Costs/turnover:
- Worst fold:
- Worst stream/side:
- Confidence interval/dispersion:
- Performance concentration:

## 7. Baseline and attribution

| Variant | Matched rows? | Primary metric | Economic metric | Frequency | Interpretation |
|---|---|---:|---:|---:|---|
| No-skill/simple | | | | | |
| Direct frozen representation | | | | | |
| New candidate | | | | | |
| Shuffle/control | | | | | |
| Component ablation | | | | | |

What specifically caused lift or regression?

## 8. Search exposure

- Total strategies considered:
- Trial families:
- Manual trials:
- Optuna/grid completed:
- Pruned:
- Failed/retried:
- Outer/holdout inspections:
- Multiple-testing adjustment or limitation:

## 9. Error analysis

### Where it worked

- `<observation>`

### Where it failed

- `<observation>`

### Most likely failure boundary

`data | label | representation | specialist extraction | calibration |
economic policy | simulation | costs | production parity`

Evidence:

### Alternative explanations / falsification checks

- timing placebo:
- shuffle/shared-driver control:
- regime stability:
- neighboring-parameter stability:
- cost/latency sensitivity:

## 10. Gate verdicts

| Gate | PASS / FAIL / NOT RUN | Reason |
|---|---|---|
| G0 Research contract | | |
| G1 Data and causality | | |
| G2 MVP learnability | | |
| G3 Temporal transfer | | |
| G4 Economic validity | | |
| G5 Production parity | | |
| G6 Live promotion | | |

## 11. Decision rationale

`<Explain why the evidence supports proceed, revise, stop, promote, or
rollback. Separate facts from inference.>`

## 12. Exceptions and limitations

| Rule/limitation | Risk | Compensating evidence | Approver | Remediation |
|---|---|---|---|---|
| | | | | |

## 13. Artifacts retained and cleanup

Retain:

- `<artifact>`

Delete/expire:

- `<artifact>`

Large temporary artifacts MUST NOT be retained without a stated reuse purpose.

## 14. Next experiment

- New hypothesis:
- One intended change:
- Contract fields that remain locked:
- New selection data, if any:
- Confirmation data remaining untouched:
- Backlog items not part of next MVP:

## 15. Durable updates

- [ ] repository README/WF ledger updated
- [ ] local runbook updated
- [ ] search registry updated
- [ ] artifact registry updated
- [ ] monitoring/rollback docs updated if promoted
