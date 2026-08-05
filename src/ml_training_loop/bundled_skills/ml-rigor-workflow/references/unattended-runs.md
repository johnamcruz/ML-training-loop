# Unattended ML runs

## Freeze before launch

Record repository commits and cleanliness requirements, data and checkpoint hashes, cache and label identities, split boundary, seed, device, workload policy, exact stage order, acceptance gates, log paths, output root, and resume behavior.

## Queue design

- Authenticate every frozen input before creating output.
- Execute dependent stages sequentially unless resource and lineage independence are proven.
- Make each stage resumable and idempotent.
- Persist a stage receipt before advancing.
- Use atomic best checkpoints and incomplete markers for partial caches.
- Keep standard and error logs visible.
- Print batch or epoch progress at useful intervals.
- Preserve original errors and archive only startup-only failures with clear identity.

## Terminal states

Write machine-readable terminal evidence:

- COMPLETE for all declared stages and final reports;
- FAILED_GATE for a valid experiment that missed a performance gate;
- BLOCKED for data, lineage, causality, malformed artifact, or unexpected runtime failure.

Do not call negative evidence a crash or infrastructure failure.

## Monitoring

Do not spend interaction budget polling when the user requests an unattended run. Provide stable log and artifact paths and inspect only on explicit request or terminal notification.

When status is requested, check the process, recent standard and error logs, output receipts, last completed stage, and terminal marker. Report observed facts, not ETA guesses unsupported by throughput.

## Resume

Resume only from receipts whose input identity and code/config still match. If an upstream identity changed, invalidate dependent stages only. Never reuse a partial cache or checkpoint because its filename exists.

## Resource safety

Measure disk and memory before launch. Keep reproducible cache cleanup narrowly targeted and preserve checkpoints, reports, logs, source, and run records. Benchmark batch or worker changes on a bounded slice before applying them to the full run.
