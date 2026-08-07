"""Optional Codex CLI adapter for bounded, evidence-driven revisions."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import fcntl
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from typing import Callable, Mapping, Protocol
from uuid import uuid4

from ..domain import Decision, ReasoningOutcome, Revision
from ..interfaces import ReasoningRequest


_RESPONSE_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "required": ["decision", "rationale", "config_override_json"],
    "properties": {
        "decision": {"enum": ["REVISE", "STOP", "BLOCKED"]},
        "rationale": {"type": "string", "minLength": 1},
        "config_override_json": {"type": "string"},
    },
}


@dataclass(frozen=True)
class CodexExecutionRequest:
    repository_root: Path
    artifact_directory: Path
    prompt: str
    model: str
    reasoning_effort: str
    sandbox: str
    writable_roots: tuple[Path, ...]
    timeout_seconds: int


@dataclass(frozen=True)
class CodexExecution:
    command: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str
    response: str


class CodexExecutor(Protocol):
    @property
    def identity(self) -> Mapping: ...

    def execute(self, request: CodexExecutionRequest) -> CodexExecution: ...


class SubprocessCodexExecutor:
    """Invoke a local Codex CLI with a schema-constrained final response."""

    def __init__(self, executable: str | Path = "codex") -> None:
        self._executable = str(executable)

    @property
    def identity(self) -> Mapping:
        return {
            "kind": "subprocess_codex_executor_v1",
            "executable": self._executable,
        }

    def execute(self, request: CodexExecutionRequest) -> CodexExecution:
        request.artifact_directory.mkdir(parents=True, exist_ok=True)
        schema_path = request.artifact_directory / "response.schema.json"
        response_path = request.artifact_directory / "response.json"
        _atomic_json(schema_path, _RESPONSE_SCHEMA)
        executable = shutil.which(self._executable)
        if executable is None:
            raise FileNotFoundError(f"Codex executable not found: {self._executable}")
        command = [
            executable,
            "exec",
            "--ephemeral",
            "--model",
            request.model,
            "--config",
            f'model_reasoning_effort="{request.reasoning_effort}"',
            "--sandbox",
            request.sandbox,
            "--cd",
            str(request.repository_root),
        ]
        for root in request.writable_roots:
            command.extend(("--add-dir", str(root)))
        command.extend((
            "--output-schema",
            str(schema_path),
            "--output-last-message",
            str(response_path),
            "-",
        ))
        completed = subprocess.run(
            command,
            input=request.prompt,
            cwd=request.repository_root,
            text=True,
            capture_output=True,
            timeout=request.timeout_seconds,
            check=False,
        )
        _atomic_json(request.artifact_directory / "exit.json", {
            "returncode": completed.returncode,
        })
        response = response_path.read_text() if response_path.is_file() else ""
        return CodexExecution(
            command=tuple(command),
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
            response=response,
        )


class CodexCliReasoningAdapter:
    """Turn one reasoning checkpoint into one validated revision or a decline.

    The host owns domain instructions and revision-policy validation. This
    adapter owns the generic evidence envelope, Codex invocation, strict
    response parsing, and durable receipts.
    """

    def __init__(
        self,
        *,
        repository_root: Path,
        receipt_root: Path,
        prompt_builder: Callable[[ReasoningRequest], str],
        revision_validator: Callable[[Revision], None],
        executor: CodexExecutor | None = None,
        model: str = "gpt-5.6-sol",
        reasoning_effort: str = "medium",
        sandbox: str = "read-only",
        writable_roots: tuple[Path, ...] = (),
        timeout_seconds: int = 1800,
    ) -> None:
        self._repository_root = repository_root.expanduser().resolve()
        self._receipt_root = receipt_root.expanduser().resolve()
        self._prompt_builder = prompt_builder
        self._revision_validator = revision_validator
        self._executor = executor or SubprocessCodexExecutor()
        self._model = model
        self._reasoning_effort = reasoning_effort
        self._sandbox = sandbox
        self._writable_roots = tuple(
            root.expanduser().resolve() for root in writable_roots
        )
        if timeout_seconds <= 0:
            raise ValueError("reasoning timeout_seconds must be positive")
        self._timeout_seconds = timeout_seconds

    def revise(self, request: ReasoningRequest) -> ReasoningOutcome:
        directory = _reasoning_directory(self._receipt_root, request)
        directory.mkdir(parents=True, exist_ok=True)
        with _exclusive_lock(directory / "reasoning.lock"):
            return self._revise_locked(request, directory)

    def _revise_locked(
        self,
        request: ReasoningRequest,
        directory: Path,
    ) -> ReasoningOutcome:
        canonical_receipt = directory / "receipt.json"
        invocation = directory / f"invocation-{uuid4().hex}"
        request_sha256: str | None = None
        try:
            envelope = _evidence_envelope(request)
            host_instructions = self._prompt_builder(request).strip()
            if not host_instructions:
                raise ValueError("reasoning prompt builder returned empty instructions")
            request_payload = {
                "schema": "ml-training-loop-codex-reasoning-request-v1",
                "evidence": envelope,
                "host_instructions": host_instructions,
                "execution_policy": {
                    "repository_root": str(self._repository_root),
                    "sandbox": self._sandbox,
                    "writable_roots": [
                        str(root) for root in self._writable_roots
                    ],
                    "timeout_seconds": self._timeout_seconds,
                    "executor": self._executor.identity,
                },
                "model": self._model,
                "reasoning_effort": self._reasoning_effort,
            }
            request_sha256 = _json_sha256(request_payload)
            if canonical_receipt.is_file():
                return self._replay(canonical_receipt, request_sha256)
            recovered = self._recover_completed_invocation(
                directory,
                canonical_receipt,
                request,
                request_sha256,
            )
            if recovered is not None:
                return recovered
            invocation.mkdir()
            prompt = (
                "You are at one bounded ML training-loop reasoning checkpoint. "
                "Use the required skills, diagnose the first failed boundary, and "
                "choose REVISE for at most one causal revision, STOP when the "
                "scientific path is falsified, or BLOCKED for integrity, causality, "
                "lineage, or executable-contract faults. Do not change the frozen "
                "objective, evaluator, temporal roles, or sealed evidence. "
                "Treat surrogate diagnostics and proposals as advisory evidence, "
                "not authorization; reject any proposal that violates the host "
                "contract. Return "
                "only the schema-constrained response. Encode the configuration "
                "override as a JSON-object string in config_override_json; use "
                "the string '{}' for STOP or BLOCKED.\n\n"
                f"Evidence envelope:\n{json.dumps(envelope, indent=2, sort_keys=True)}\n\n"
                f"Host instructions:\n{host_instructions}\n"
            )
            _atomic_json(invocation / "request.json", request_payload)
            execution = self._executor.execute(CodexExecutionRequest(
                repository_root=self._repository_root,
                artifact_directory=invocation,
                prompt=prompt,
                model=self._model,
                reasoning_effort=self._reasoning_effort,
                sandbox=self._sandbox,
                writable_roots=self._writable_roots,
                timeout_seconds=self._timeout_seconds,
            ))
            _atomic_json(invocation / "execution.json", {
                "command": list(execution.command),
                "returncode": execution.returncode,
                "stdout": execution.stdout,
                "stderr": execution.stderr,
                "response": execution.response,
            })
            if execution.returncode != 0:
                raise RuntimeError(f"Codex reasoning exited {execution.returncode}")
            payload = _parse_response(execution.response)
            response_sha256 = hashlib.sha256(execution.response.encode()).hexdigest()
            outcome = _outcome_from_payload(
                payload,
                stage=request.stage.name,
                revision_validator=self._revision_validator,
            )
            receipt = _outcome_receipt(
                outcome,
                request_sha256=request_sha256,
                response_sha256=response_sha256,
            )
            _publish_receipt(invocation, canonical_receipt, receipt)
            return outcome
        except Exception as error:
            invocation.mkdir(exist_ok=True)
            failure = {
                "status": "failed",
                "error_type": type(error).__name__,
                "reason": str(error),
                "request_sha256": request_sha256,
            }
            _atomic_json(invocation / "receipt.json", failure)
            if not canonical_receipt.exists():
                _atomic_json(canonical_receipt, failure)
            raise

    def _recover_completed_invocation(
        self,
        directory: Path,
        canonical_receipt: Path,
        request: ReasoningRequest,
        request_sha256: str,
    ) -> ReasoningOutcome | None:
        for invocation in sorted(directory.glob("invocation-*")):
            request_path = invocation / "request.json"
            execution_path = invocation / "execution.json"
            exit_path = invocation / "exit.json"
            response_path = invocation / "response.json"
            if not request_path.is_file():
                continue
            saved_request = json.loads(request_path.read_text())
            if _json_sha256(saved_request) != request_sha256:
                continue
            response = None
            if execution_path.is_file():
                execution = json.loads(execution_path.read_text())
                if execution.get("returncode") == 0:
                    response = execution.get("response")
            elif exit_path.is_file() and response_path.is_file():
                # The executor persists the child exit status before returning
                # to the adapter. A response alone is never authorization.
                exit_status = json.loads(exit_path.read_text())
                if exit_status.get("returncode") == 0:
                    response = response_path.read_text()
            if not isinstance(response, str) or not response.strip():
                continue
            outcome = _outcome_from_payload(
                _parse_response(response),
                stage=request.stage.name,
                revision_validator=self._revision_validator,
            )
            receipt = _outcome_receipt(
                outcome,
                request_sha256=request_sha256,
                response_sha256=hashlib.sha256(response.encode()).hexdigest(),
                recovered=True,
            )
            _publish_receipt(invocation, canonical_receipt, receipt)
            return outcome
        return None

    def _replay(self, path: Path, request_sha256: str) -> ReasoningOutcome:
        saved = json.loads(path.read_text())
        if saved.get("request_sha256") != request_sha256:
            raise ValueError("completed reasoning receipt identity drifted")
        decision = saved.get("decision")
        rationale = saved.get("rationale")
        config_override = (
            saved.get("revision", {}).get("config_override", {})
            if isinstance(saved.get("revision"), dict)
            else {}
        )
        outcome = _outcome_from_payload(
            {
                "decision": decision,
                "rationale": rationale,
                "config_override": config_override,
            },
            stage=(
                saved.get("revision", {}).get("stage")
                if isinstance(saved.get("revision"), dict)
                else ""
            ) or "unknown",
            revision_validator=self._revision_validator,
        )
        return outcome


class ClaudeCliReasoningAdapter:
    """Fail-closed placeholder for a future schema-constrained Claude CLI.

    The class intentionally satisfies the reasoning seam without guessing at
    an unauthenticated or unstable CLI contract.
    """

    def __init__(
        self,
        *,
        repository_root: Path,
        receipt_root: Path,
        prompt_builder: Callable[[ReasoningRequest], str],
    ) -> None:
        self._repository_root = repository_root.expanduser().resolve()
        self._receipt_root = receipt_root.expanduser().resolve()
        self._prompt_builder = prompt_builder

    def revise(self, request: ReasoningRequest) -> Revision | None:
        directory = _reasoning_directory(self._receipt_root, request)
        instructions = self._prompt_builder(request).strip()
        if not instructions:
            raise ValueError("reasoning prompt builder returned empty instructions")
        _atomic_json(directory / "receipt.json", {
            "status": "unavailable",
            "provider": "claude_cli",
            "reason": (
                "Claude CLI reasoning adapter is not implemented; no revision "
                "was authorized"
            ),
            "repository_root": str(self._repository_root),
        })
        raise NotImplementedError(
            "Claude CLI reasoning adapter is not implemented"
        )


def _evidence_envelope(request: ReasoningRequest) -> dict:
    return {
        "run_id": request.run_id,
        "plan": {
            "name": request.plan.name,
            "identity": request.plan.identity,
            "max_revisions_per_stage": request.plan.max_revisions_per_stage,
        },
        "stage": {
            "name": request.stage.name,
            "config": _redact(request.stage.config),
            "effective_config_override": _redact(
                request.effective_config_override
            ),
            "attempt": request.receipt.attempt,
            "required_skills": list(request.required_skills),
        },
        "receipt": {
            "status": request.receipt.status,
            "outputs": _redact(request.receipt.outputs),
        },
        "gate": {
            "decision": request.gate.decision.value,
            "reason": request.gate.reason,
            "evidence": _redact(request.gate.evidence),
        },
        "prior_revisions": [
            {
                **_revision_payload(revision),
                "config_override": _redact(revision.config_override),
            }
            for revision in request.prior_revisions
        ],
        "experiment_ledger": (
            {
                "identity": request.experiment_ledger.identity,
                "entries": [
                    {
                        "run_id": entry.run_id,
                        "plan_identity": entry.plan_identity,
                        "stage": entry.stage,
                        "attempt": entry.attempt,
                        "status": entry.status,
                        "revision": (
                            _revision_payload(entry.revision)
                            if entry.revision is not None
                            else None
                        ),
                        "outputs": _redact(entry.outputs),
                        "artifacts": [
                            {
                                "path": artifact.path,
                                "kind": artifact.kind.value,
                                "sha256": artifact.sha256,
                            }
                            for artifact in entry.artifacts
                        ],
                    }
                    for entry in request.experiment_ledger.entries
                ],
            }
            if request.experiment_ledger is not None
            else None
        ),
        "surrogate_advice": (
            {
                "backend": request.surrogate_advice.backend,
                "diagnostics": _redact(request.surrogate_advice.diagnostics),
                "proposals": _redact(request.surrogate_advice.proposals),
                "evidence": _redact(request.surrogate_advice.evidence),
            }
            if request.surrogate_advice is not None
            else None
        ),
        "receipt_identity_sha256": _json_sha256({
            "stage": request.receipt.stage,
            "attempt": request.receipt.attempt,
            "status": request.receipt.status,
            "outputs": request.receipt.outputs,
        }),
        "revision_number": request.revision_number,
    }


def _reasoning_directory(root: Path, request: ReasoningRequest) -> Path:
    return (
        root
        / request.run_id
        / request.stage.name
        / f"revision-{request.revision_number}"
    )


def _revision_payload(revision: Revision) -> dict:
    return {
        "stage": revision.stage,
        "rationale": revision.rationale,
        "config_override": revision.config_override,
    }


def _outcome_from_payload(
    payload: Mapping,
    *,
    stage: str,
    revision_validator: Callable[[Revision], None],
) -> ReasoningOutcome:
    decision = Decision(payload["decision"])
    revision = None
    if decision is Decision.REVISE:
        revision = Revision(
            stage=stage,
            rationale=payload["rationale"],
            config_override=payload["config_override"],
        )
        revision_validator(revision)
    return ReasoningOutcome(
        decision=decision,
        rationale=payload["rationale"],
        revision=revision,
    )


def _outcome_receipt(
    outcome: ReasoningOutcome,
    *,
    request_sha256: str,
    response_sha256: str,
    recovered: bool = False,
) -> dict:
    statuses = {
        Decision.REVISE: "authorized",
        Decision.STOP: "stopped",
        Decision.BLOCKED: "blocked",
    }
    return {
        "status": statuses[outcome.decision],
        "decision": outcome.decision.value,
        "rationale": outcome.rationale,
        "request_sha256": request_sha256,
        "response_sha256": response_sha256,
        "recovered_completed_invocation": recovered,
        "revision": (
            _revision_payload(outcome.revision)
            if outcome.revision is not None
            else None
        ),
    }


def _publish_receipt(invocation: Path, canonical: Path, payload: Mapping) -> None:
    _atomic_json(invocation / "receipt.json", payload)
    if canonical.exists():
        raise FileExistsError(f"reasoning receipt already exists: {canonical}")
    _atomic_json(canonical, payload)


@contextmanager
def _exclusive_lock(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+") as stream:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def _json_sha256(payload: Mapping) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def _redact(value):
    sensitive = ("secret", "token", "password", "credential", "api_key")
    if isinstance(value, Mapping):
        return {
            str(key): (
                "[REDACTED]"
                if any(marker in str(key).lower() for marker in sensitive)
                else _redact(item)
            )
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_redact(item) for item in value]
    return value


def _parse_response(raw: str) -> dict:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as error:
        raise ValueError("Codex reasoning response is not valid JSON") from error
    required = {"decision", "rationale", "config_override_json"}
    if not isinstance(payload, dict) or set(payload) != required:
        raise ValueError("Codex reasoning response has unexpected fields")
    if payload["decision"] not in {"REVISE", "STOP", "BLOCKED"}:
        raise ValueError("reasoning decision must REVISE, STOP, or BLOCK")
    if not isinstance(payload["rationale"], str) or not payload["rationale"].strip():
        raise ValueError("reasoning rationale must be non-empty")
    if not isinstance(payload["config_override_json"], str):
        raise ValueError("config_override_json must be a string")
    try:
        config_override = json.loads(payload["config_override_json"])
    except json.JSONDecodeError as error:
        raise ValueError("config_override_json is not valid JSON") from error
    if not isinstance(config_override, dict):
        raise ValueError("config_override_json must encode an object")
    if payload["decision"] == "REVISE" and not config_override:
        raise ValueError("REVISE requires non-empty config_override")
    if payload["decision"] != "REVISE" and config_override:
        raise ValueError("STOP and BLOCKED must not include config_override")
    return {
        "decision": payload["decision"],
        "rationale": payload["rationale"],
        "config_override": config_override,
    }


def _atomic_json(path: Path, payload: Mapping) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    temporary.replace(path)
