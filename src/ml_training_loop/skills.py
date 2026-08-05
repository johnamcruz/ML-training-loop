"""Install missing Codex skills from an SSD-resident, pinned bundle."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import shutil
from uuid import uuid4

from .domain import SkillBootstrapReceipt, SkillStatus


FOUNDATION_SKILLS = (
    "ml-rigor-workflow",
    "ml-design-experiment",
    "ml-audit-data-labels",
    "ml-train-select-model",
    "ml-train-representation",
    "ml-validate-temporal",
    "ml-diagnose-experiment",
    "ml-promote-operate",
)


def directory_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    for file in sorted(item for item in path.rglob("*") if item.is_file()):
        digest.update(file.relative_to(path).as_posix().encode())
        digest.update(file.read_bytes())
    return digest.hexdigest()


@dataclass(frozen=True)
class SkillManifestEntry:
    name: str
    sha256: str


class BundledSkillBootstrapper:
    """Copy only missing pinned skills; never overwrite an installed skill."""

    def __init__(
        self,
        bundle: Path,
        destination: Path | None = None,
    ) -> None:
        self._bundle = bundle.resolve()
        codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
        self._destination = (destination or codex_home / "skills").resolve()
        manifest_path = self._bundle / "skills.lock.json"
        payload = json.loads(manifest_path.read_text())
        if payload.get("schema") != "ml-training-loop-skills-lock-v1":
            raise ValueError("unsupported skills manifest schema")
        self._entries = {
            item["name"]: SkillManifestEntry(**item)
            for item in payload.get("skills", ())
        }

    def ensure(self, required: tuple[str, ...]) -> SkillBootstrapReceipt:
        statuses = []
        self._destination.mkdir(parents=True, exist_ok=True)
        for name in dict.fromkeys(required):
            entry = self._entries.get(name)
            source = self._bundle / name
            destination = self._destination / name
            if destination.exists():
                statuses.append(SkillStatus(
                    name=name,
                    status="already_present",
                    destination=str(destination),
                ))
                continue
            if entry is None or not source.is_dir():
                statuses.append(SkillStatus(name=name, status="missing_from_bundle"))
                continue
            if directory_sha256(source) != entry.sha256:
                statuses.append(SkillStatus(
                    name=name,
                    status="bundle_hash_mismatch",
                    source=str(source),
                ))
                continue
            temporary = self._destination / f".{name}.{uuid4().hex}.tmp"
            shutil.copytree(source, temporary)
            temporary.replace(destination)
            statuses.append(SkillStatus(
                name=name,
                status="installed",
                source=str(source),
                destination=str(destination),
            ))
        return SkillBootstrapReceipt(tuple(statuses))


class NoopSkillBootstrapper:
    """Explicit adapter for hosts that manage Codex skills externally."""

    def ensure(self, required: tuple[str, ...]) -> SkillBootstrapReceipt:
        return SkillBootstrapReceipt(tuple(
            SkillStatus(name=name, status="already_present") for name in required
        ))
