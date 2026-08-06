"""Run-state adapters."""
from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import sqlite3

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver

from .domain import Decision, GateResult, Phase, Revision, RunState, StageReceipt


class InMemoryRunStore:
    def __init__(self) -> None:
        self._states: dict[str, RunState] = {}
        self._checkpointer = InMemorySaver()

    def load(self, run_id: str) -> RunState | None:
        return self._states.get(run_id)

    def save(self, state: RunState) -> None:
        self._states[state.run_id] = state

    def _langgraph_checkpointer(self) -> InMemorySaver:
        return self._checkpointer


class JsonRunStore:
    """Atomic filesystem state suitable for interruption and resume."""

    def __init__(self, root: Path) -> None:
        self._root = root.resolve()
        self._checkpointer: SqliteSaver | None = None
        self._checkpoint_connection: sqlite3.Connection | None = None

    def load(self, run_id: str) -> RunState | None:
        path = self._path(run_id)
        if not path.is_file():
            return None
        raw = json.loads(path.read_text())
        gate = raw.get("last_gate")
        return RunState(
            run_id=raw["run_id"],
            plan_identity=raw["plan_identity"],
            phase=Phase(raw["phase"]),
            stage_index=int(raw["stage_index"]),
            attempts={key: int(value) for key, value in raw["attempts"].items()},
            receipts=tuple(StageReceipt(**item) for item in raw["receipts"]),
            revisions=tuple(Revision(**item) for item in raw["revisions"]),
            last_gate=(
                None
                if gate is None
                else GateResult(
                    decision=Decision(gate["decision"]),
                    reason=gate["reason"],
                    evidence=gate.get("evidence", {}),
                )
            ),
            message=raw.get("message", ""),
        )

    def save(self, state: RunState) -> None:
        path = self._path(state.run_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = asdict(state)
        payload["phase"] = state.phase.value
        if state.last_gate is not None:
            payload["last_gate"]["decision"] = state.last_gate.decision.value
        temporary = path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n"
        )
        temporary.replace(path)

    def _path(self, run_id: str) -> Path:
        supported = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
        if not run_id or any(character not in supported for character in run_id):
            raise ValueError("run id contains unsupported characters")
        return self._root / run_id / "state.json"

    def _langgraph_checkpointer(self) -> SqliteSaver:
        """Return the private durable runtime used by LangGraph.

        ``state.json`` remains the stable ML-facing receipt/state format. The
        SQLite database is LangGraph-owned execution state and is intentionally
        not exposed through the public ``RunStore`` interface.
        """
        if self._checkpointer is None:
            self._root.mkdir(parents=True, exist_ok=True)
            self._checkpoint_connection = sqlite3.connect(
                self._root / "langgraph-checkpoints.sqlite",
                check_same_thread=False,
            )
            self._checkpointer = SqliteSaver(self._checkpoint_connection)
        return self._checkpointer
