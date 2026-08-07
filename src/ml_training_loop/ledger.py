"""Authenticated, domain-neutral experiment history."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Mapping

from .artifacts import ArtifactEvidence
from .domain import Revision, RunState


@dataclass(frozen=True)
class ExperimentEntry:
    run_id: str
    plan_identity: str
    stage: str
    attempt: int
    status: str
    revision: Revision | None
    outputs: Mapping[str, Any]
    artifacts: tuple[ArtifactEvidence, ...]


@dataclass(frozen=True)
class ExperimentLedger:
    """Replayable evidence from every completed attempt in one run."""

    entries: tuple[ExperimentEntry, ...]

    @classmethod
    def from_run_state(cls, state: RunState) -> "ExperimentLedger":
        if not isinstance(state, RunState):
            raise TypeError("experiment ledger requires a RunState")
        revisions_by_stage: dict[str, list[Revision]] = {}
        for revision in state.revisions:
            revisions_by_stage.setdefault(revision.stage, []).append(revision)
        expected_attempt: dict[str, int] = {}
        entries = []
        for receipt in state.receipts:
            next_attempt = expected_attempt.get(receipt.stage, 0) + 1
            if receipt.attempt != next_attempt:
                raise ValueError(
                    f"receipt attempts are not contiguous for stage {receipt.stage}"
                )
            expected_attempt[receipt.stage] = receipt.attempt
            stage_revisions = revisions_by_stage.get(receipt.stage, [])
            revision_index = receipt.attempt - 2
            if revision_index >= len(stage_revisions):
                raise ValueError(
                    f"receipt attempt {receipt.attempt} lacks its stage revision"
                )
            revision = (
                None if revision_index < 0 else stage_revisions[revision_index]
            )
            artifacts = _artifact_evidence(receipt.outputs)
            entries.append(ExperimentEntry(
                run_id=state.run_id,
                plan_identity=state.plan_identity,
                stage=receipt.stage,
                attempt=receipt.attempt,
                status=receipt.status,
                revision=revision,
                outputs=receipt.outputs,
                artifacts=artifacts,
            ))
        return cls(entries=tuple(entries))

    @property
    def identity(self) -> str:
        payload = [asdict(entry) for entry in self.entries]
        encoded = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode()
        return hashlib.sha256(encoded).hexdigest()


def _artifact_evidence(outputs: Mapping[str, Any]) -> tuple[ArtifactEvidence, ...]:
    raw = outputs.get("artifact_evidence", {})
    if not isinstance(raw, Mapping):
        raise ValueError("receipt artifact_evidence must be an object")
    evidence = []
    for path, item in sorted(raw.items()):
        if not isinstance(path, str) or not isinstance(item, Mapping):
            raise ValueError("receipt artifact evidence entry is malformed")
        if set(item) != {"kind", "sha256"}:
            raise ValueError("receipt artifact evidence fields are malformed")
        evidence.append(ArtifactEvidence(
            path=path,
            kind=item["kind"],
            sha256=item["sha256"],
        ))
    return tuple(evidence)
