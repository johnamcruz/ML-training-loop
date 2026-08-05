# ML Training Loop

A reusable, evidence-driven state machine for ML training. It coordinates
execution, validation, diagnosis, one controlled revision at a time, retraining,
and interruption-safe resume until the declared plan succeeds or reaches a
genuine blocker.

The core is deliberately model-family independent. Supervised learning,
reinforcement learning, representation learning, mechanical optimization, and
future workflows plug in through the same small adapter interfaces.

## Flow

```text
bootstrap required ML skills
            |
            v
      execute stage <------------------+
            |                           |
            v                           |
       evaluate gate                    |
            |                           |
     +------+------+------+             |
     |             |      |             |
  PROCEED        REVISE  STOP/BLOCKED   |
     |             |                    |
 next stage   diagnose and authorize ---+
```

`PROCEED`, `REVISE`, `STOP`, and `BLOCKED` are separate decisions. Completed
stage receipts and state transitions are persisted so a resumed run does not
repeat completed compute.

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
)
state = loop.run(plan, run_id="experiment-001")
```

The replaceable seams are `StageAdapter`, `GateAdapter`, `ReasoningAdapter`,
`RunStore`, `SkillBootstrapper`, and `AdapterRegistry`. Training libraries and
model-specific decisions remain behind those seams. See [CONTEXT.md](CONTEXT.md)
for the domain boundary.

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
