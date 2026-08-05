# Experiment Plan: `<short name>`

> Complete this before costly training or any confirmation run. Replace every
> placeholder. Use `N/A — <reason>` rather than deleting a section.

## 1. Identity

- Experiment ID:
- Process version: `ML-RIGOR-v1`
- Repository:
- Owner:
- Date opened:
- Status: `exploration | selection | confirmation | production`
- Strategy / trial family / trial:
- Parent experiment:
- Related issue/decision:

## 2. Hypothesis

### Decision being improved

`<What exact model or trading decision changes?>`

### Causal information set

`<What is observable at decision time?>`

### Mechanism

`<Why should this information contain incremental signal?>`

### Falsifiable claim

`<On matched temporal OOS data, X should improve Y over baseline Z.>`

### Stop/revise condition

`<What evidence would reject or materially revise the hypothesis?>`

## 3. Repository ownership

| Artifact or responsibility | Data/representation / application-model / deployment owner | Immutable identity |
|---|---|---|
| Source data | | |
| Foundation checkpoint or reusable representation | | |
| Application labels or RL rewards | | |
| Specialist, policy, or decision model | | |
| Simulation | | |
| Produced artifact | | |
| Live integration, safety, or risk | | |

Private or application-specific IP present? `yes/no`

If yes, identify the owning repository and confirm reusable packages do not contain it:

## 4. Executable decision contract

- Universe:
- Contract/roll rule:
- Session/timezone:
- Timeframe/bar timestamp meaning:
- Decision cadence:
- Lookback:
- Decision time:
- Execution lag and price:
- Outcome horizon/holding period:
- Direction rule:
- Target:
- Stop:
- Same-bar ambiguity:
- Position overlap/concurrency:
- Costs:
- Sizing/risk:
- Intended live interface:

Timeline:

```text
lookback -> decision -> execution -> outcome/exit
```

## 5. Data identity and eligibility

- Source manifest/hash:
- Date coverage:
- Streams:
- Schema version:
- Data build commit/config:
- Eligibility-mask definition/hash:
- Missing/invalid/extreme-value policy:
- Continuous-contract/session audit:
- Expected rows/events:
- Cache identity:
- Existing cache reuse decision and evidence:

## 6. Label contract

- Human-readable target:
- Mathematical target:
- Label code/version:
- Anchor:
- Horizon:
- Threshold fitting:
- Censoring:
- Ambiguity:
- Long/Short symmetry:
- Expected base rate:
- Mechanical/reference implementation:

Required pre-model audit:

- [ ] path fixtures
- [ ] vectorized/reference parity
- [ ] base rate by fold/stream/side
- [ ] MFE/MAE/time-to-event where relevant
- [ ] overlap/concurrency/effective sample size
- [ ] label/simulator execution parity
- [ ] fold-boundary purge test
- [ ] finite-input checks

## 7. Temporal design

| Role | Date range/schedule | Permitted use |
|---|---|---|
| Research/train | | Fit parameters |
| Inner validation | | Select architecture/hyperparameters/epoch/calibration/policy |
| Outer walk-forward | | Measure once per frozen outer fit |
| Sealed holdout | | One-use final confirmation |
| Shadow/canary | | Operational confirmation |

- Expanding or rolling:
- Inner-fold design:
- Outer-fold design:
- Purge:
- Embargo:
- Retraining cadence:
- Has any listed OOS/holdout period influenced prior development?:
- Evidence registry reference:

## 8. Baselines and matched variants

| Variant | Purpose | Only intended difference |
|---|---|---|
| No-skill/base-rate | | |
| Mechanical/simple | | |
| Direct frozen representation | | |
| New component | | |
| Shuffle/random control | | |

Locked across comparisons:

- [ ] rows and labels
- [ ] split roles
- [ ] checkpoint/cache lineage
- [ ] seed and budget
- [ ] preprocessing/calibration
- [ ] policy and costs
- [ ] metric code

## 9. Model and training

- Architecture:
- Frozen/trainable components:
- Input/output contract:
- Objective and weights:
- Sampling/weights:
- Optimizer/LR/schedule:
- Epoch budget/minimum/patience:
- Checkpoint-selection metric:
- Tie breaker:
- Calibration:
- Seed plan:
- Resource budget:
- Mocked end-to-end test:
- Retention probes, if representation fine-tuning:

## 10. Search plan

- Search needed?:
- Declared space:
- Categorical architecture coverage:
- Numeric refinement:
- Sampler/pruner:
- Minimum evidence before prune:
- Trial budget:
- Prior manual trials in this family:
- Study name/storage:
- Failure handling:
- Selection rule:

## 11. Metrics and acceptance

### Primary model metric

- Metric:
- Threshold/direction:
- Why it matches the decision:

### Economic metrics

- Exact truth:
- Net expectancy:
- Win rate:
- Average winning/losing R:
- Signals/day:
- Drawdown/tail:
- Costs:

### Operational metrics

- Latency/resource:
- Parity tolerance:
- Input rejection:

### Required slices

- [ ] outer fold
- [ ] ticker/timeframe
- [ ] Long/Short
- [ ] session/regime
- [ ] score quantile
- [ ] worst case

### Promotion thresholds

`<Binding only at the declared gate. During MVP, misses may be report-only.>`

## 12. MVP execution plan

1. Label/timing unit tests:
2. Mechanical audit:
3. Small data slice:
4. Smoke training:
5. One temporal OOS diagnostic:
6. Failure analysis:
7. One permitted change:

Only data-integrity, causality, or executable-contract faults block this MVP.
List non-blocking hardening in the backlog.

## 13. Promotion plan

- Full nested walk-forward:
- Sealed confirmation:
- Cost/latency stress:
- Golden-slice parity:
- `produce` command:
- Shadow/canary:
- Rollback:
- Monitoring:

## 14. Known risks and exceptions

| Rule/risk | Rationale | Compensating evidence | Approver | Expires/remediation |
|---|---|---|---|---|
| | | | | |

Exceptions cannot authorize leakage, unauthenticated data, misleading OOS
claims, or research/live contract divergence.

## 15. Commands and expected artifacts

```bash
# exact commands
```

Expected artifacts:

- `<artifact>`

## 16. Backlog outside current scope

- `<backlog item>`

## Approval to run

- Contract reviewed by:
- Date:
- G0 status: `PASS | BLOCKED`
- G1 preflight status: `PASS | BLOCKED`
