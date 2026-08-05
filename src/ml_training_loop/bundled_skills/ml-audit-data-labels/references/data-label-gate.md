# Data and label gate

## Authenticated source

Require provider and schema version, immutable source IDs or hashes, universe, contracts and roll rule, sessions, timeframe, timezone, timestamp semantics, partial-bar policy, correction lineage, build commit and config, row counts, bounds, and integrity manifest.

Continuous futures must prove deterministic contract selection, no overlapping timestamps, explicit adjustment behavior, consistent volume and sessions, retained contract metadata, correct last date, and append or update equivalence to a clean rebuild.

Classify calendar or session gaps before calling them corruption. Never interpolate, splice, deduplicate, or repair silently.

## Causal examples

At decision time, every input is fully observable and every input bar is closed. Targets begin after the declared anchor. Input plus target reserve remain within one temporal role. Related series contain only bars closed by the primary reference time.

If timestamps mark bar opens, availability is timestamp plus timeframe.

## Target types

- Fixed horizon for a value or state at a future time.
- Barrier or event labels for event ordering.
- Ranking for selecting among simultaneous candidates.
- Survival or hazard for time-to-event and censoring.
- Meta-label only when a primary direction or candidate already exists.

Record human and mathematical definition, anchor, eligibility, horizon, threshold fitting, units, censoring, ambiguity, code identity, and distributions by fold, stream, side, and regime.

## Executable parity fixtures

Test Long and Short symmetry, target-first, stop-first, same-bar collision, gaps, timeout, censoring, next-open or configured lag, session end, contract roll, incomplete future reserve, fold-boundary purging, and future mutation of model inputs.

Optimized or vectorized labels must exactly match a trusted scalar reference.

## Dependence

Report average and maximum concurrent labels, sample uniqueness, effective sample size, distinct days or sessions or events, and horizon distribution. Choose event sampling, uniqueness weights, clustered uncertainty, or non-overlapping confirmation samples as appropriate.

Purge training rows whose label outcome reaches a later role. Apply embargo when split topology allows feature or outcome overlap around a validation interval.

## Eligibility

Treat the mask as a hashed artifact with causal construction and exclusion counts. A matched comparison uses identical eligible rows. Censor only under a declared rule.

## Values and transforms

Reject invalid rows. Preserve meaningful missingness explicitly. Retain legitimate tails unless a train-fitted robust transform is declared. Check finiteness before cache creation, training, calibration, and inference.

Fit normalization, clipping, imputation, dimensionality reduction, feature selection, label thresholds, sampling ratios, and class weights inside each training fold.

## Derived representations

Embedding cache identity includes authenticated source, immutable checkpoint hash, lookback, channel order, preprocessing, row identity, split role, dtype, and code/config. Upstream predictions used by another model must be fold-safe OOF.

## Cache identity

Include source manifest, row universe, sessions, label and feature code, checkpoint, lookback and horizon, execution contract, dtype and shape, sampling, split eligibility, command, environment, code and config, and completeness marker. Path or filename similarity is never identity.

Optimize only after exact parity with a correct reference. FP16, memmaps, vectorization, and stream-wise resumability require preserved identity and tolerance evidence.

## Pre-model report

Persist timeline, representative paths, base rates and coverage, MFE or MAE or time-to-event where relevant, overlap and effective sample, mechanical economics, cache row checksum, leakage tests, and reference parity.
