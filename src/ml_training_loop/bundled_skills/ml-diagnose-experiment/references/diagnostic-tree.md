# ML diagnostic tree

## Can the run be identified and reproduced?

If no, the result is untraceable. Resolve code, config, data, cache, checkpoint, split, seed, and command identity before diagnosing performance.

## Does G1 pass?

Check authenticated source, timestamp semantics, finite inputs, label timing, label and simulator parity, target reserve at boundaries, train-only transforms, OOF upstream scores, consumed holdout status, and cache identity.

Any failure is P0. Repair and rebuild only affected derived artifacts.

## Did optimization execute correctly?

Check:

- labels and eligibility are non-empty and have expected base rates;
- features or embeddings have finite variance and correct shapes;
- side or class masks route loss correctly;
- objective matches target;
- gradients reach intended trainable parameters;
- frozen parameters stay frozen;
- learning rate, batch, precision, and device are stable;
- best checkpoint follows the declared metric;
- serialization and reload reproduce scores.

## Did selection generalize?

If train improves and inner validation does not, test label noise, insufficient effective sample, distribution shift, weighting, overcapacity, and metric mismatch.

If inner validation improves and outer OOS fails, first test leakage, repeated selection exposure, unstable calibration, regime dependence, and hidden trial count before changing architecture.

## Where is information lost?

1. Direct frozen representation probe fails: representation or target learnability.
2. Probe succeeds but specialist fails: extraction architecture, optimization, or row mapping.
3. Specialist ranks but calibrates poorly: population, base-rate, or calibrator failure.
4. Calibrated score works but Entry does not: semantic mismatch, consumer, policy, frequency, or economics.
5. Backtest works but replay differs: parity or execution defect.

Strong future truth conditional on an event is oracle evidence, not proof that the causal score identifies that event.

## Frequency and imbalance

Show unfiltered score and opportunity distributions. A higher win rate from almost no trades may be thresholding rather than better learning. Report common-row results at matched exposure.

## Temporal and stream failure

Identify whether one year, side, ticker, or timeframe carries the result. Compare natural exposure with sampling policy. Do not average away unsupported streams.

## Performance and runtime

First determine whether time is spent in cache extraction, label construction, CPU transfer, device training, calibration, or evaluation. Optimize the dominant stage only after correctness parity. Increasing batch or workers is an experiment with memory and numerical behavior; benchmark on a bounded slice.

## Resume rule

Resume only when the first failed boundary has direct evidence of repair, dependent artifacts are invalidated by identity, and the original contract remains unchanged. Otherwise create a revised experiment.
