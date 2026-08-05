# ML method adoption catalog

Use a technique only when a current failure mode and a matched experiment justify its complexity.

| Area | Adopt now | Apply when relevant or backlog |
|---|---|---|
| Research process | Decision-first hypothesis, evidence boundary, durable lineage, stage gates | None |
| Financial data | Point-in-time sources, revisions, contracts, sessions, provenance | Parquet or Arrow migration after MVP |
| Microstructure | Bar timing, tradable execution, conservative ambiguity, basic costs | Calibrated impact and capacity before promotion |
| Alternative data | Point-in-time availability and licensing if used | Defer until a specific hypothesis needs it |
| Synthetic data | Deterministic path fixtures and operational stress | Fold-safe augmentation only with real OOS gate |
| Temporal research | Walk-forward, nested selection, sealed holdout, search ledger | CPCV only for justified path-dependence analysis |
| Learning targets | Executable labels, overlap and effective sample, causal masks | Survival, ranking, or meta-labels only when decision requires them |
| Feature engineering | Causal train-only transforms and simple diagnostics | New feature families must earn matched lift |
| Model-derived features | Frozen identity, OOF predictions, stable row mapping | Wider stacking only after each component works |
| Text | Publication time, revisions, corpus and tokenizer identity | Outside current OHLCV MVP |
| Classical ML | Linear and tree baselines, regularization, calibration | Advanced tabular models when baseline gap warrants |
| Deep time series | Baseline first, task-driven architecture, uncertainty, latency | Larger transformers or SSMs only for a diagnosed bottleneck |
| Latent factors | Train-only fitting and stability when used | Multi-instrument portfolio work |
| Causal ML | Precise predictive language, timing placebos, regime checks | Treatment-effect models only with defensible assumptions |
| Simulation | Exact executable timing, costs, controls, dependence, stress | More detailed fills as stage requires |
| Portfolio | Separate signal from sizing and risk | Advanced optimization after single-strategy evidence |
| Transaction costs | Conservative MVP costs and break-even stress | Calibrated impact and capacity for promotion |
| Risk | Layered limits, tails, drawdown, external circuit breakers | Advanced portfolio risk when needed |
| Strategy synthesis | Modular contracts and matched end-to-end attribution | Combine strategies only after independent evidence |
| Reinforcement learning | Temporal OOS environments and sim-to-real parity | Use only for an explicitly owned RL objective |
| RAG | Temporal source provenance and separate retrieval evaluation | Not part of market-model MVP |
| Knowledge graphs | Temporal validity and versioned schema if adopted | Unnecessary for active MVP |
| Agents | Explicit state, typed tools, replay, provenance, bounded authority | Autonomous trading agents are backlog |
| Live systems | Shared decision core, order state, idempotency, reconciliation | Scale only after staged rollout |
| MLOps | Layered monitoring, drift diagnosis, champion/challenger, rollback | Heavy platforms only when scale justifies |
| Systematic practice | Prioritize the current bottleneck and preserve learning | Reject novelty without evidence |

## Reusable representations

Keep reusable objectives application-agnostic. Validate accessible information with matched controls, per-stream or per-domain transfer, retention, and native checkpoint evidence. Probe quality is not downstream application value.

## Application-specific models

Define the exact decision, action space, objective, timing, costs or utility, and abstention behavior where applicable. Validate application labels, rewards, and OOF upstream scores in the owning repository. Claimed lift must come from matched temporal OOS evidence.

## Live operation

Keep operational state, safety limits, external side effects, and rollback outside the predictive model. A high score or reward cannot override external safety controls.
