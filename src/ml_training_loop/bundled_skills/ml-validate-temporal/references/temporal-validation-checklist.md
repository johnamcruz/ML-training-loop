# Temporal validation checklist

## Split design

Predeclare research start, expanding or rolling window, inner schedule, outer dates and step, purge and embargo, calibration window, retraining cadence, sealed holdout, and final production fit interval.

Expanding versus rolling is part of the hypothesis. Inner folds select; outer folds measure.

## Simulation fidelity

Implement completed-bar timing, order lag and type, time in force, gaps, stop and target ordering, conservative intrabar ambiguity, partial-fill assumption, overlapping positions, session and holidays, contract rolls, fees, spread, slippage, impact, capital, margin, leverage, risk, stale-data behavior, and rejection handling at the rigor required by the current stage.

Use simple conservative costs during MVP and calibrated cost, latency, and capacity stress before promotion.

## Required views

- Every outer fold and aggregate.
- Every ticker, timeframe, side, session, and important regime.
- Candidate and selected counts, signals per day, turnover, and overlap.
- Raw rows and effective sample or clustered uncertainty.
- Exact target-first win rate, mean and median R, average win and loss R.
- Costs, break-even cost, exposure, drawdown, and tail loss.
- Ranking and calibration at the operating point and by score quantile.
- Worst temporal and stream result.

## Controls

Use no-skill, mechanical, direct representation, label shuffle or random, incumbent, component-off, and cost or latency controls when relevant. Match opportunity and selection rate. Ask whether lift is discrimination, calibration, expectancy, or merely lower frequency.

## Search awareness

Report how many variants were tried. Use block or session bootstrap, fold-sign stability, neighboring-parameter sensitivity, cost stress, and selection-adjusted statistics when search breadth warrants. Reject isolated optima.

## Strategy acceptance

Require positive net expectancy, adequate independent trades and frequency, no single fold carrying the result, acceptable worst-fold and drawdown behavior, useful OOS ranking or calibration, cost and latency robustness, seed reproducibility, and no unresolved parity or lineage issue.

Desired win rate or frequency may guide discovery but must not be hidden behind an unreported hard filter.

## Representation checkpoint evaluation

Require all intended streams or domains, matched frozen-backbone controls, current learning and prior retention, temporal transfer, worst-case slices, calibration where probabilities are exposed, and application-agnostic probes. A probe-suite result never authorizes downstream deployment value.

## RL

Match observation, action, reward, execution, costs, sessions, risk, warmup, and recurrent state to production. Select on temporal OOS episodes, compare deterministic and stochastic policies, stress slippage, latency, missing bars, rejections, roll, and API interruption, and replay the produced policy through the production path.

## Parity slice

Persist source bars, normalized inputs, upstream outputs, calibration, final score, action, order, and simulated state transition. Later compare it through research, serialized model, and live replay.
