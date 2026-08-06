"""Public interface for the generic ML training loop."""

from .domain import (
    Decision,
    GateResult,
    Phase,
    ReasoningOutcome,
    RetryableInfrastructureError,
    Revision,
    RunCheckpoint,
    RunState,
    StageReceipt,
    StageSpec,
    TrainingPlan,
)
from .loop import TrainingLoop

__all__ = [
    "Decision",
    "GateResult",
    "Phase",
    "ReasoningOutcome",
    "RetryableInfrastructureError",
    "Revision",
    "RunCheckpoint",
    "RunState",
    "StageReceipt",
    "StageSpec",
    "TrainingLoop",
    "TrainingPlan",
]
