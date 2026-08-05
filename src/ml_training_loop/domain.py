"""Model-family-independent language for a resumable training loop."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
import hashlib
import json
from typing import Any, Mapping


class Decision(StrEnum):
    PROCEED = "PROCEED"
    REVISE = "REVISE"
    STOP = "STOP"
    BLOCKED = "BLOCKED"


class Phase(StrEnum):
    BOOTSTRAPPING = "BOOTSTRAPPING"
    EXECUTING = "EXECUTING"
    VALIDATING = "VALIDATING"
    NEEDS_REASONING = "NEEDS_REASONING"
    COMPLETE = "COMPLETE"
    FAILED_GATE = "FAILED_GATE"
    STOPPED = "STOPPED"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class StageSpec:
    """One declared action and the adapter names used at its seams."""

    name: str
    stage_adapter: str
    gate_adapter: str
    config: Mapping[str, Any] = field(default_factory=dict)
    required_skills: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.name or not self.stage_adapter or not self.gate_adapter:
            raise ValueError("stage name and adapter names must be non-empty")


@dataclass(frozen=True)
class TrainingPlan:
    """Frozen declaration consumed by the shared state machine."""

    name: str
    stages: tuple[StageSpec, ...]
    required_skills: tuple[str, ...] = ()
    max_revisions_per_stage: int = 1

    def __post_init__(self) -> None:
        names = [stage.name for stage in self.stages]
        if not self.name or not self.stages:
            raise ValueError("training plan requires a name and at least one stage")
        if len(names) != len(set(names)):
            raise ValueError("training plan stage names must be unique")
        if self.max_revisions_per_stage < 0:
            raise ValueError("max revisions must be nonnegative")

    @property
    def identity(self) -> str:
        payload = {
            "name": self.name,
            "required_skills": list(self.required_skills),
            "max_revisions_per_stage": self.max_revisions_per_stage,
            "stages": [
                {
                    "name": stage.name,
                    "stage_adapter": stage.stage_adapter,
                    "gate_adapter": stage.gate_adapter,
                    "config": stage.config,
                    "required_skills": list(stage.required_skills),
                }
                for stage in self.stages
            ],
        }
        try:
            encoded = json.dumps(
                payload, sort_keys=True, separators=(",", ":")
            ).encode()
        except TypeError as error:
            raise ValueError("training plan config must be JSON serializable") from error
        return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class StageReceipt:
    stage: str
    attempt: int
    status: str
    outputs: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GateResult:
    decision: Decision
    reason: str
    evidence: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Revision:
    stage: str
    rationale: str
    config_override: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SkillStatus:
    name: str
    status: str
    source: str | None = None
    destination: str | None = None


@dataclass(frozen=True)
class SkillBootstrapReceipt:
    statuses: tuple[SkillStatus, ...]

    @property
    def ready(self) -> bool:
        return all(item.status in {"installed", "already_present"} for item in self.statuses)


@dataclass(frozen=True)
class RunState:
    run_id: str
    plan_identity: str
    phase: Phase
    stage_index: int = 0
    attempts: Mapping[str, int] = field(default_factory=dict)
    receipts: tuple[StageReceipt, ...] = ()
    revisions: tuple[Revision, ...] = ()
    last_gate: GateResult | None = None
    message: str = ""

    @property
    def terminal(self) -> bool:
        return self.phase in {
            Phase.COMPLETE,
            Phase.FAILED_GATE,
            Phase.STOPPED,
            Phase.BLOCKED,
        }
