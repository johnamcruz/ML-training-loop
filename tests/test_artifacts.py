import hashlib
import json
from pathlib import Path

import pytest

from ml_training_loop import ArtifactContract, ArtifactKind, inspect_artifacts


def test_inspect_artifacts_authenticates_json_identity_and_hash(tmp_path: Path):
    report = tmp_path / "report.json"
    report.write_text(json.dumps({"identity": {"checkpoint": "mask-v1"}}))
    expected_sha256 = hashlib.sha256(report.read_bytes()).hexdigest()

    snapshot = inspect_artifacts((ArtifactContract(
        path=report,
        kind=ArtifactKind.JSON,
        expected={"identity.checkpoint": "mask-v1"},
        expected_sha256=expected_sha256,
    ),))

    assert snapshot.ready
    assert snapshot.failures == {}
    evidence = snapshot.evidence[str(report.resolve())]
    assert evidence.kind is ArtifactKind.JSON
    assert evidence.sha256 == expected_sha256
    assert snapshot.receipt_evidence == {
        str(report.resolve()): {"kind": "json", "sha256": expected_sha256}
    }


def test_inspect_artifacts_reports_directory_contract_failures(tmp_path: Path):
    artifact = tmp_path / "bundle"
    artifact.mkdir()
    (artifact / "model.pt").write_bytes(b"weights")

    snapshot = inspect_artifacts((ArtifactContract(
        path=artifact,
        kind=ArtifactKind.DIRECTORY,
        required_files=("model.pt", "manifest.json"),
    ),))

    assert not snapshot.ready
    assert str(artifact.resolve()) in snapshot.failures
    assert "manifest.json" in snapshot.failures[str(artifact.resolve())]


def test_artifact_contract_rejects_invalid_sha256(tmp_path: Path):
    with pytest.raises(ValueError, match="SHA-256"):
        ArtifactContract(path=tmp_path / "model.pt", expected_sha256="not-a-hash")
