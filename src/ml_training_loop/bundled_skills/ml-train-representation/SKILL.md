---
name: ml-train-representation
description: Design, run, and evaluate self-supervised, foundation-model, encoder, LoRA, contrastive, masked-modeling, or representation-learning stages while preserving causal data, application-agnostic scope, checkpoint lineage, prior capabilities, and native downstream usability. Use for checkpoint training or fine-tuning, SSL curricula, auxiliary projection heads or decoders, representation-probe comparisons, forgetting checks, or choosing among representation checkpoints.
---

# ML Representation Training

Keep representation training strategy-agnostic and attributable.

## Freeze the stage

Declare the causal SSL objective, universe, sampling, window and reserve, split and sealed holdout, parent checkpoint hash, trainable parameters, seed and compute budget, current-task probes, retention suite, controls, and promotion tolerances.

Changing the objective, sampler, context, checkpoint, or stream universe creates a new artifact identity.

## Train one capability at a time

1. Authenticate raw market inputs and objective timing.
2. Run a small reference path, smoke, and matched parent or control.
3. Save stage checkpoints and exact lineage.
4. Compare REAL with matched time-shuffle, random, parent, and objective-specific ablations.
5. Report every ticker and timeframe, median and worst stream, and temporal folds.
6. Rerun prior-capability retention after every curriculum stage.

LoRA lowers trainable capacity and compute; it does not prevent forgetting. Select learning rate, adapter capacity, epochs, and patience inside temporal validation.

## Auxiliary modules are scaffolding

Projection heads, decoders, classifiers, and trainer state may optimize the objective, but the promoted encoder or LoRA checkpoint must work after they are removed.

Select and promote only when matched validation on the saved native representation confirms intended lift and acceptable retention. Fail closed when only the auxiliary head improves.

After successful finalization, downstream consumers must not require trainer state, optimizer state, or auxiliary modules. Keep trainer state only for exact resume of an interrupted or failed run.

## Evidence boundary

- Objective diagnostics show that training learned its task.
- Frozen representation probes show accessible information and retention.
- Private downstream economics are evaluated separately in the consuming repository.

Probe lift is not downstream application value. An application-specific outcome cannot silently become a reusable representation objective.

## Checkpoint tournament

Compare candidates under identical source rows, splits, train-only probe scaling, seed, controls, and evaluation periods. Treat differing lineages as diagnostic rather than clean objective lift.

Promote only a bundle containing checkpoint and parent hashes, data and objective provenance, config and seeds, temporal reports, per-stream results, controls, retention, input schema, timestamp semantics, compatibility, and a deterministic inference fixture.

Read references/representation-gate.md for the full promotion checklist.
