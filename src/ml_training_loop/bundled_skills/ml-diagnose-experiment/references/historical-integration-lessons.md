# Historical integration lessons

These are reusable lessons from prior Pivot, Expansion, Trend, and Entry experiments.

## Decision and execution timing

A feature available only at next-bar execution cannot be used by a decision-close model. Keep next-open values in label or simulation code only. If the next open gaps through the fixed stop, retain the candidate under the declared no-fill or gap rule rather than filtering it with future knowledge.

## Oracle versus causal signal

Future truth conditioned on an event can show that the setup has economic potential. It does not show that a causal model identifies that event. Require OOF score-to-outcome discrimination and matched economics.

## Shared event semantics

A generic all-bar Expansion or Trend target may be learnable yet refer to different anchors, sides, stops, horizons, or row populations than Entry. For integration, define every specialist from the same causal event identity when the hypothesis requires it.

## Training and inference population

Do not train or calibrate a conditional specialist only on rows selected by future truth and then emit it on every live row. Either:

- train a joint event on the full inference population; or
- expose the conditional model only after a causal condition selects the same population.

Population mismatch can produce apparently valid specialist metrics and unusable probabilities.

## Separate probabilities

Launch and Persistence answer different questions. Emit and calibrate them separately. Do not multiply probabilities unless the conditional decomposition and calibration population make the product mathematically and empirically valid. Let the final economic model learn interactions from fold-safe OOF values.

## Component metric versus Entry lift

A specialist can beat prevalence and shuffle on its own target while adding no exact target-before-stop lift to Entry. Diagnose representation, extraction, calibration, semantic alignment, consumer wiring, exposure, and costs in order. Stop repeated scalar transforms when matched OOS evidence remains absent.

## Multi-timeframe learning

Multi-stream or multi-timeframe training can improve component AP, AUC, or calibration. It still must improve the primary stream on identical rows and exact economics. Pooled lift cannot authorize the final strategy.

## Threshold inspection

An attractive cell found after reviewing a threshold grid is selection evidence. Freeze the resulting policy and use a later outer interval before describing it as deployable.

## Side asymmetry

Report Long and Short independently. Do not force symmetry merely for appearance, but do not hide a one-side dependency. A one-side candidate requires a predeclared scope and matched temporal evidence.

## Failure interpretation

Distinguish:

- BLOCKED: lineage, causality, data, cache, or executable-contract defect;
- FAILED_GATE: valid experiment produced negative evidence;
- PROCEED: specific next component earned evidence;
- STOP: repeated valid tests falsified the path.

Negative evidence should simplify the next experiment, not trigger unrelated components.
