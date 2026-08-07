# Domain context

ML Training Loop is a model-family-independent orchestration library. LangGraph
owns graph execution, routing, checkpoints, resume, and interrupts. This
package owns the ML-specific contracts and policies layered onto that runtime,
not training algorithms.

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
- **Reasoning outcome**: one provider-neutral `REVISE`, `STOP`, or `BLOCKED`
  disposition. Only `REVISE` carries a host-validated configuration override.
- **Surrogate advice**: optional read-only diagnostics and candidate proposals
  derived from the authenticated trial ledger. Advice informs reasoning but
  never authorizes or executes a revision.
- **Run state**: the durable state-machine snapshot used to resume without
  repeating completed work.
- **Profile**: a future host-owned assembly of adapters for a model family such
  as supervised learning or reinforcement learning. Profiles do not fork the
  core state machine.

## Ownership boundary

The core owns skill bootstrapping, ML receipts, revision budgets, and the graph
nodes that apply those policies. LangGraph owns transition execution,
checkpointing, routing, and interruption-safe resume. Hosts own datasets,
trainers, evaluators, model-specific metrics, compute environments,
notifications, and promotion policy through adapters.

An optional surrogate advisor may inspect receipts, gate evidence, and prior
revisions at a reasoning checkpoint. The core authenticates its structured
advice into the reasoning request. Hosts own the optimization implementation,
search space, posterior model, and interpretation of model-family metrics.

The core must not import PyTorch, an RL framework, a data platform, or a model
provider. A host may use any of them behind an adapter.
