# Representation checkpoint gate

## Public scope

Allowed: authenticated market data, causal OHLCV windows, strategy-agnostic corruption or prediction or contrastive targets, reusable encoders and decoders, temporal transfer, controls, and inference contracts.

Disallowed: private entries, stops, targets, R multiples, sizing, routing, or brokerage behavior.

## Objective timing

Self-supervision is not exempt from leakage. Future bars may form targets only after the observable anchor and inside the same temporal split. Related inputs must be closed by the primary reference time. Fit normalization and thresholds on training roles only.

## Sampling

Bar-proportional learns natural exposure. Uniform-stream equalizes expected stream influence. A staged curriculum is another intervention. Persist the policy and samples seen per stream.

## Controls and transfer

Require parent, random, matched time-shuffle, and task-specific ablations as appropriate. Report chronological folds, sample counts and base rates, ticker and timeframe metrics, median and worst stream, stability, known regime failures, and uncertainty.

## Retention and forgetting

Define a fixed parent atlas before training. After every stage, show current-task delta and prior-task delta. Do not promote pooled current-task lift that hides stream failures or erased capabilities.

## Native artifact rule

Load the saved checkpoint in a fresh inference path with every temporary module absent. Recompute matched frozen representations and direct probes. Verify tensor schema, channel order, scaling, timestamps, and deterministic fixture. Auxiliary-only success is failure.

## Downstream handoff

Consumers verify checkpoint identity and must not reinterpret input normalization, channel order, time alignment, output shape, or calibration. Any incompatible change creates a new contract version.

## Promotion

Freeze the recipe before final temporal evaluation. Open a sealed holdout once only after objective, checkpoint selection, probe suite, tolerances, and handoff contract are frozen.
