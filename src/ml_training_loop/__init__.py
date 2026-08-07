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
    SurrogateAdvice,
    TrainingPlan,
)
from .interfaces import SurrogateAdvisor, SurrogateRequest
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
    "SurrogateAdvice",
    "SurrogateAdvisor",
    "SurrogateRequest",
    "TrainingLoop",
    "TrainingPlan",
]
