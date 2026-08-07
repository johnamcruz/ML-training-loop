"""Model- and workflow-independent artifact authentication."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence


class ArtifactKind(StrEnum):
    FILE = "file"
    DIRECTORY = "directory"
    JSON = "json"


@dataclass(frozen=True)
class ArtifactContract:
    """What must exist before an artifact may be trusted or reused."""

    path: Path
    kind: ArtifactKind = ArtifactKind.FILE
    expected: Mapping[str, Any] = field(default_factory=dict)
    required_files: tuple[str, ...] = ()
    expected_sha256: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", Path(self.path).expanduser().resolve())
        try:
            object.__setattr__(self, "kind", ArtifactKind(self.kind))
        except ValueError as error:
            raise ValueError(f"unsupported artifact kind: {self.kind}") from error
        if self.kind is not ArtifactKind.DIRECTORY and self.required_files:
            raise ValueError("required_files apply only to directory artifacts")
        if self.kind is not ArtifactKind.JSON and self.expected:
            raise ValueError("expected fields apply only to JSON artifacts")
        if any(
            not isinstance(item, str)
            or not item
            or Path(item).is_absolute()
            or ".." in Path(item).parts
            for item in self.required_files
        ):
            raise ValueError("required_files must be safe relative paths")
        if self.expected_sha256 is not None:
            _validate_sha256(self.expected_sha256, name="expected SHA-256")


@dataclass(frozen=True)
class ArtifactEvidence:
    path: str
    kind: ArtifactKind
    sha256: str

    def __post_init__(self) -> None:
        if not isinstance(self.path, str) or not self.path:
            raise ValueError("artifact evidence path must be non-empty")
        try:
            object.__setattr__(self, "kind", ArtifactKind(self.kind))
        except ValueError as error:
            raise ValueError(
                f"unsupported artifact evidence kind: {self.kind}"
            ) from error
        _validate_sha256(self.sha256, name="artifact evidence SHA-256")


@dataclass(frozen=True)
class ArtifactSnapshot:
    evidence: Mapping[str, ArtifactEvidence]
    failures: Mapping[str, str]

    @property
    def ready(self) -> bool:
        return not self.failures

    @property
    def receipt_evidence(self) -> dict[str, dict[str, str]]:
        """Return the canonical JSON shape consumed by experiment ledgers."""

        return {
            path: {"kind": item.kind.value, "sha256": item.sha256}
            for path, item in self.evidence.items()
        }


def inspect_artifacts(
    contracts: Sequence[ArtifactContract],
) -> ArtifactSnapshot:
    """Authenticate declared artifacts without raising for contract failures."""

    evidence: dict[str, ArtifactEvidence] = {}
    failures: dict[str, str] = {}
    for contract in contracts:
        if not isinstance(contract, ArtifactContract):
            raise TypeError("artifact inspection requires ArtifactContract values")
        path = contract.path
        failure = _contract_failure(contract)
        key = str(path)
        if failure is not None:
            failures[key] = failure
            continue
        sha256 = _tree_sha256(path) if path.is_dir() else _file_sha256(path)
        if contract.expected_sha256 is not None and sha256 != contract.expected_sha256:
            failures[key] = (
                f"SHA-256 expected {contract.expected_sha256} "
                f"but received {sha256}: {path}"
            )
            continue
        evidence[key] = ArtifactEvidence(
            path=key,
            kind=contract.kind,
            sha256=sha256,
        )
    return ArtifactSnapshot(evidence=evidence, failures=failures)


def _contract_failure(contract: ArtifactContract) -> str | None:
    path = contract.path
    if contract.kind is ArtifactKind.DIRECTORY:
        if not path.is_dir():
            return f"directory is missing: {path}"
        for relative in contract.required_files:
            required = path / relative
            if not required.is_file():
                return f"required file is missing: {required}"
        return None
    if not path.is_file():
        return f"file is missing: {path}"
    if contract.kind is not ArtifactKind.JSON:
        return None
    try:
        payload = json.loads(path.read_text())
        _validate_finite_json(payload)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        return f"JSON is unreadable or non-finite: {path}: {error}"
    if not isinstance(payload, Mapping):
        return f"JSON root is not an object: {path}"
    for field_name, expected in contract.expected.items():
        found, actual = _lookup(payload, field_name)
        if not found or actual != expected:
            return (
                f"field {field_name!r} expected {expected!r} "
                f"but received {actual!r}: {path}"
            )
    return None


def _lookup(payload: Mapping[str, Any], field_name: str) -> tuple[bool, Any]:
    value: Any = payload
    for part in field_name.split("."):
        if not isinstance(value, Mapping) or part not in value:
            return False, None
        value = value[part]
    return True, value


def _validate_finite_json(value: Any) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("JSON contains a non-finite number")
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError("JSON object keys must be strings")
            _validate_finite_json(item)
    elif isinstance(value, list):
        for item in value:
            _validate_finite_json(item)


def _validate_sha256(value: str, *, name: str) -> None:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{name} must be a lowercase hexadecimal digest")


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _tree_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    files = sorted(
        candidate for candidate in path.rglob("*") if candidate.is_file()
    )
    for item in files:
        digest.update(item.relative_to(path).as_posix().encode())
        with item.open("rb") as source:
            for block in iter(lambda: source.read(1 << 20), b""):
                digest.update(block)
    return digest.hexdigest()
