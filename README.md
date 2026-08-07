# ML Training Loop

A reusable, evidence-driven ML training workflow built on LangGraph. It
coordinates execution, validation, diagnosis, one controlled revision at a
time, retraining, and interruption-safe resume until the declared plan succeeds
or reaches a genuine blocker.

The core is deliberately model-family independent. Supervised learning,
reinforcement learning, representation learning, mechanical optimization, and
future workflows plug in through the same small adapter interfaces.

## Flow

```text
bootstrap required ML skills
            |
            v
      execute stage <--------------------------+
            |                                   |
            v                                   |
       evaluate gate                            |
            |                                   |
     +------+------+------+                     |
     |             |      |                     |
  PROCEED        REVISE  STOP/BLOCKED           |
     |             |                            |
 next stage   optional surrogate advice         |
                   |                            |
                   v                            |
             diagnose and authorize ------------+
```

`PROCEED`, `REVISE`, `STOP`, and `BLOCKED` are separate decisions. LangGraph
owns graph execution, conditional routing, checkpoint/resume, and reasoning
interrupts. Completed stage receipts retain their existing ML-specific format,
while LangGraph checkpoints execution in SQLite for filesystem-backed runs.

## External interface

Hosts construct a `TrainingLoop` with their adapters and submit an immutable
`TrainingPlan`:

```python
from pathlib import Path

from ml_training_loop import StageSpec, TrainingLoop, TrainingPlan
from ml_training_loop.adapters import DictAdapterRegistry
from ml_training_loop.skills import BundledSkillBootstrapper
from ml_training_loop.stores import JsonRunStore

plan = TrainingPlan(
    name="example",
    stages=(
        StageSpec("prepare", "my_prepare_adapter", "my_data_gate"),
        StageSpec("train", "my_trainer", "my_quality_gate"),
    ),
)

loop = TrainingLoop(
    adapters=DictAdapterRegistry(stages=stage_adapters, gates=gate_adapters),
    store=JsonRunStore(Path(".ml-training-loop/runs")),
    skills=BundledSkillBootstrapper(Path("path/to/bundled_skills")),
    reasoning=my_reasoning_adapter,
    surrogate=my_optional_surrogate_advisor,
)
state = loop.run(plan, run_id="experiment-001")
```

`run()` uses synchronous LangGraph durability by default, so a successful graph
step is checkpointed before the next step begins. Hosts do not need to change
their call sites. Ordinary adapter failures continue to fail closed; an adapter
may explicitly raise `RetryableInfrastructureError` for a transient
infrastructure fault that is safe to retry within the same declared ML attempt.

Durable history and recovery are available when an operator needs them:

```python
checkpoints = loop.history("experiment-001")
state = loop.recover(plan, "experiment-001", checkpoints[-2].checkpoint_id)
```

History is chronological and read-only. Recovery is deliberately explicit: it
branches from the selected checkpoint after verifying run and plan identity,
then resumes with the same synchronous durability. The framework never rewinds
a scientific campaign automatically.

The replaceable seams are `StageAdapter`, `GateAdapter`, `ReasoningAdapter`,
`SurrogateAdvisor`, `RunStore`, `SkillBootstrapper`, and `AdapterRegistry`.
Training libraries and model-specific decisions remain behind those seams. See
[CONTEXT.md](CONTEXT.md) for the domain boundary.

### Optional surrogate-augmented reasoning

At a `REVISE` checkpoint, a host may inject a `SurrogateAdvisor`. It receives
the immutable training plan, current receipt and gate, complete prior receipt
ledger, prior revisions, and effective configuration. It returns structured
`SurrogateAdvice`: a backend identity, diagnostics, candidate proposals, and
supporting evidence. The training loop authenticates that finite JSON payload
inside the reasoning request.

The advisor is deliberately read-only. It cannot execute training, mutate the
plan, select a proposal, or authorize a revision. The reasoning adapter may
accept, refine, or reject its proposals, and the host's existing revision
validator remains the final authority. Omitting the advisor preserves the
existing workflow exactly. A configured advisor that errors or returns a
malformed payload fails closed before reasoning.

This seam is inspired by *Agentic Bayesian Optimization through
Surrogate-Augmented Autoresearch* (Brunzema et al., 2026), which places a
reasoning agent in control while a Bayesian backend supplies uncertainty-aware
diagnostics and proposals:

https://arxiv.org/abs/2608.00316

The core package does not depend on BoTorch or Optuna. Hosts may implement the
same seam with a Gaussian-process backend, Optuna ask/tell, or a deterministic
fake. Search-space definitions and probabilistic modeling remain optional
integration concerns rather than orchestration dependencies.

### Unattended Codex reasoning

`CodexCliReasoningAdapter` is an optional adapter for campaigns that may revise
without a human handoff. It sends the current identity-hashed receipt and
failed-gate evidence to a schema-constrained Codex CLI run. The host supplies
domain instructions and validates the returned configuration override before
the state machine executes it. Every request, execution, response, and
authorization is retained as a durable receipt.

```python
from ml_training_loop.integrations import CodexCliReasoningAdapter

reasoning = CodexCliReasoningAdapter(
    repository_root=repository,
    receipt_root=run_root / "reasoning",
    prompt_builder=build_domain_revision_prompt,
    revision_validator=validate_domain_revision,
)
```

The optional integration defaults to `gpt-5.6-sol` with medium reasoning,
read-only sandboxing, and one schema-constrained response. A host must supply a
revision validator; prompt text is not treated as a safety policy. The training
plan still owns the maximum revision count. A malformed response or failed
Codex process fails closed as `BLOCKED`; declining a revision durably stops the
run. Completed reasoning receipts are replayed on resume only when their request
identity still matches.

The structured reasoning result is provider-neutral: `REVISE` carries one
validated configuration override, `STOP` ends a falsified scientific path, and
`BLOCKED` identifies an integrity, causality, lineage, or executable-contract
fault. A per-checkpoint process lock prevents duplicate provider calls, and a
completed invocation is recovered before a provider call is repeated.

`ClaudeCliReasoningAdapter` currently exists only as an explicit fail-closed
stub. It records an `unavailable` receipt and authorizes no revision. Its real
CLI invocation must not be enabled until the structured-output and sandbox
contract is implemented and tested.

## Foundation skills

The package carries a pinned, generic ML skill bundle. `TrainingLoop.run()`
checks and installs missing skills before any stage executes. Existing installed
skills are never overwritten. A missing skill or bundle hash mismatch blocks the
run before compute begins.

To bootstrap explicitly:

```bash
ml-training-loop bootstrap-skills
```

## Development

The tests use fake stage, gate, reasoning, and skill adapters to exercise the
real public state machine without ML compute:

```bash
python -m unittest discover -s tests -v
```

Current scope is the generic orchestration foundation. Supervised and RL
profiles will be added as adapters after the shared state machine is stable.
