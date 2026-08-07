"""Replaceable interfaces at the training loop's external seams."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol

from .domain import (
    GateResult,
    ReasoningOutcome,
    Revision,
    RunState,
    SkillBootstrapReceipt,
    StageReceipt,
    StageSpec,
    SurrogateAdvice,
    TrainingPlan,
)
from .ledger import ExperimentLedger


@dataclass(frozen=True)
class StageRequest:
    run_id: str
    plan_identity: str
    stage: StageSpec
    attempt: int
    prior_receipts: tuple[StageReceipt, ...]
    config_override: Mapping[str, Any]


@dataclass(frozen=True)
class GateRequest:
    run_id: str
    plan_identity: str
    stage: StageSpec
    receipt: StageReceipt
    prior_receipts: tuple[StageReceipt, ...]


@dataclass(frozen=True)
class ReasoningRequest:
    run_id: str
    plan: TrainingPlan
    stage: StageSpec
    receipt: StageReceipt
    gate: GateResult
    revision_number: int
    required_skills: tuple[str, ...]
    prior_revisions: tuple[Revision, ...] = ()
    effective_config_override: Mapping[str, Any] = field(default_factory=dict)
    surrogate_advice: SurrogateAdvice | None = None
    experiment_ledger: ExperimentLedger | None = None


@dataclass(frozen=True)
class SurrogateRequest:
    run_id: str
    plan: TrainingPlan
    stage: StageSpec
    receipt: StageReceipt
    gate: GateResult
    revision_number: int
    prior_receipts: tuple[StageReceipt, ...]
    prior_revisions: tuple[Revision, ...] = ()
    effective_config_override: Mapping[str, Any] = field(default_factory=dict)
    experiment_ledger: ExperimentLedger | None = None


class StageAdapter(Protocol):
    def execute(self, request: StageRequest) -> StageReceipt: ...


class GateAdapter(Protocol):
    def evaluate(self, request: GateRequest) -> GateResult: ...


class ReasoningAdapter(Protocol):
    def revise(
        self, request: ReasoningRequest
    ) -> ReasoningOutcome | Revision | None: ...


class SurrogateAdvisor(Protocol):
    def advise(self, request: SurrogateRequest) -> SurrogateAdvice | None: ...


class SkillBootstrapper(Protocol):
    def ensure(self, required: tuple[str, ...]) -> SkillBootstrapReceipt: ...


class RunStore(Protocol):
    def load(self, run_id: str) -> RunState | None: ...

    def save(self, state: RunState) -> None: ...


class AdapterRegistry(Protocol):
    def stage(self, name: str) -> StageAdapter: ...

    def gate(self, name: str) -> GateAdapter: ...
