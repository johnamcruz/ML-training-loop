"""Public interface for the generic ML training loop."""

from .artifacts import (
    ArtifactContract,
    ArtifactEvidence,
    ArtifactKind,
    ArtifactSnapshot,
    inspect_artifacts,
)
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
from .ledger import ExperimentEntry, ExperimentLedger
from .loop import TrainingLoop

__all__ = [
    "ArtifactContract",
    "ArtifactEvidence",
    "ArtifactKind",
    "ArtifactSnapshot",
    "Decision",
    "ExperimentEntry",
    "ExperimentLedger",
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
    "inspect_artifacts",
]
