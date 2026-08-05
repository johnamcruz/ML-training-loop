# Domain context

ML Training Loop is a model-family-independent orchestration library. It owns
control flow and durable run state, not training algorithms.

## Ubiquitous language

- **Training plan**: an immutable ordered declaration of stages, adapters,
  required skills, and revision limits.
- **Stage**: one bounded action performed by a host adapter, such as preparing
  data, fitting a model, evaluating it, or packaging an accepted candidate.
- **Receipt**: immutable evidence that a stage attempt completed and the outputs
  it produced. A receipt is not a claim that the quality gate passed.
- **Gate**: an adapter that evaluates one receipt and returns exactly one
  decision: `PROCEED`, `REVISE`, `STOP`, or `BLOCKED`.
- **Revision**: one evidence-backed configuration override for the current
  failed stage. It does not silently alter the frozen training plan.
- **Reasoning checkpoint**: a pause after `REVISE` where an injected reasoning
  adapter may authorize one controlled revision.
- **Run state**: the durable state-machine snapshot used to resume without
  repeating completed work.
- **Profile**: a future host-owned assembly of adapters for a model family such
  as supervised learning or reinforcement learning. Profiles do not fork the
  core state machine.

## Ownership boundary

The core owns deterministic transitions, skill bootstrapping, receipts,
revision budgets, and interruption-safe resume. Hosts own datasets, trainers,
evaluators, model-specific metrics, compute environments, notifications, and
promotion policy through adapters.

The core must not import PyTorch, an RL framework, a data platform, or a model
provider. A host may use any of them behind an adapter.
