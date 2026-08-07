from ml_training_loop import (
    ExperimentLedger,
    Phase,
    Revision,
    RunState,
    StageReceipt,
)


SHA_A = "a" * 64
SHA_B = "b" * 64


def test_experiment_ledger_maps_each_attempt_to_its_effective_revision():
    state = RunState(
        run_id="campaign-1",
        plan_identity="plan-sha",
        phase=Phase.FAILED_GATE,
        attempts={"entry": 2},
        receipts=(
            StageReceipt(
                stage="entry",
                attempt=1,
                status="complete",
                outputs={
                    "artifact_evidence": {
                        "/artifacts/baseline.json": {
                            "kind": "json",
                            "sha256": SHA_A,
                        }
                    },
                    "metrics": {"auc": 0.61},
                },
            ),
            StageReceipt(
                stage="entry",
                attempt=2,
                status="complete",
                outputs={
                    "artifact_evidence": {
                        "/artifacts/revised.json": {
                            "kind": "json",
                            "sha256": SHA_B,
                        }
                    },
                    "metrics": {"auc": 0.66},
                },
            ),
        ),
        revisions=(Revision(
            stage="entry",
            rationale="change the loss",
            config_override={"loss": "focal"},
        ),),
    )

    ledger = ExperimentLedger.from_run_state(state)

    assert len(ledger.entries) == 2
    assert ledger.entries[0].revision is None
    assert ledger.entries[1].revision == state.revisions[0]
    assert ledger.entries[1].outputs["metrics"] == {"auc": 0.66}
    assert ledger.entries[1].artifacts[0].sha256 == SHA_B
    assert ledger.identity


def test_experiment_ledger_rejects_malformed_authenticated_evidence():
    state = RunState(
        run_id="campaign-1",
        plan_identity="plan-sha",
        phase=Phase.FAILED_GATE,
        receipts=(StageReceipt(
            stage="entry",
            attempt=1,
            status="complete",
            outputs={
                "artifact_evidence": {
                    "/artifacts/report.json": {
                        "kind": "json",
                        "sha256": "invalid",
                    }
                }
            },
        ),),
    )

    try:
        ExperimentLedger.from_run_state(state)
    except ValueError as error:
        assert "artifact evidence SHA-256" in str(error)
    else:
        raise AssertionError("malformed artifact evidence was accepted")
