from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from ml_training_loop import Decision, GateResult, StageReceipt, StageSpec, TrainingPlan
from ml_training_loop.interfaces import ReasoningRequest
from ml_training_loop.integrations.reasoning import (
    ClaudeCliReasoningAdapter,
    CodexCliReasoningAdapter,
    CodexExecution,
)


class FakeCodexExecutor:
    def __init__(self, payload: dict):
        self.payload = payload
        self.requests = []

    @property
    def identity(self):
        return {"kind": "fake_codex_executor_v1"}

    def execute(self, request):
        self.requests.append(request)
        return CodexExecution(
            command=("codex", "exec"),
            returncode=0,
            stdout="",
            stderr="",
            response=json.dumps(self.payload),
        )


def reasoning_request() -> ReasoningRequest:
    stage = StageSpec(
        name="entry",
        stage_adapter="trainer",
        gate_adapter="economics",
        required_skills=("ml-train-select-model",),
    )
    return ReasoningRequest(
        run_id="campaign-1",
        plan=TrainingPlan(name="pivot", stages=(stage,), max_revisions_per_stage=3),
        stage=stage,
        receipt=StageReceipt(
            stage="entry",
            attempt=1,
            status="complete",
            outputs={
                "report_path": "/evidence/entry.json",
                "api_token": "must-not-reach-provider",
            },
        ),
        gate=GateResult(
            Decision.REVISE,
            "short expectancy failed",
            {"short_mean_r": -0.18, "win_rate": 0.26},
        ),
        revision_number=1,
        required_skills=("ml-rigor-workflow", "ml-diagnose-experiment"),
    )


class CodexCliReasoningAdapterTests(unittest.TestCase):
    def test_authorizes_one_structured_revision_and_persists_receipt(self):
        executor = FakeCodexExecutor({
            "decision": "REVISE",
            "rationale": "isolate Long and Short optimization",
            "config_override_json": json.dumps({
                "command": [".venv/bin/python", "temp/train_side_experts.py"],
                "changed_settings": {
                    "entry_architecture": {"from": "shared", "to": "side_specific"}
                },
            }),
        })
        validated = []
        with tempfile.TemporaryDirectory() as temporary:
            adapter = CodexCliReasoningAdapter(
                repository_root=Path(temporary),
                receipt_root=Path(temporary) / "reasoning",
                prompt_builder=lambda request: "Use the host's frozen evaluator.",
                revision_validator=lambda revision: validated.append(revision),
                executor=executor,
            )

            outcome = adapter.revise(reasoning_request())
            revision = outcome.revision

            self.assertEqual(revision.stage, "entry")
            self.assertEqual(revision.config_override["command"][1], "temp/train_side_experts.py")
            self.assertEqual(validated, [revision])
            execution_request = executor.requests[0]
            self.assertEqual(execution_request.model, "gpt-5.6-sol")
            self.assertEqual(execution_request.reasoning_effort, "medium")
            self.assertEqual(execution_request.sandbox, "read-only")
            self.assertIn("short expectancy failed", execution_request.prompt)
            self.assertIn("Use the host's frozen evaluator.", execution_request.prompt)
            self.assertNotIn("must-not-reach-provider", execution_request.prompt)
            self.assertIn("[REDACTED]", execution_request.prompt)
            receipt = (
                Path(temporary)
                / "reasoning/campaign-1/entry/revision-1/receipt.json"
            )
            saved = json.loads(receipt.read_text())
            self.assertEqual(saved["status"], "authorized")
            self.assertEqual(saved["revision"]["stage"], "entry")

    def test_scientific_stop_is_durable_and_replayed(self):
        executor = FakeCodexExecutor({
            "decision": "STOP",
            "rationale": "evidence identifies a causal data blocker",
            "config_override_json": "{}",
        })
        with tempfile.TemporaryDirectory() as temporary:
            adapter = CodexCliReasoningAdapter(
                repository_root=Path(temporary),
                receipt_root=Path(temporary) / "reasoning",
                prompt_builder=lambda request: "Stop on integrity faults.",
                revision_validator=lambda revision: None,
                executor=executor,
            )

            self.assertEqual(adapter.revise(reasoning_request()).decision, Decision.STOP)
            self.assertEqual(adapter.revise(reasoning_request()).decision, Decision.STOP)
            self.assertEqual(len(executor.requests), 1)

            receipt = json.loads((
                Path(temporary)
                / "reasoning/campaign-1/entry/revision-1/receipt.json"
            ).read_text())
            self.assertEqual(receipt["status"], "stopped")

    def test_malformed_authorization_fails_closed(self):
        executor = FakeCodexExecutor({
            "decision": "REVISE",
            "rationale": "missing override",
            "config_override_json": "{}",
        })
        with tempfile.TemporaryDirectory() as temporary:
            adapter = CodexCliReasoningAdapter(
                repository_root=Path(temporary),
                receipt_root=Path(temporary) / "reasoning",
                prompt_builder=lambda request: "One change only.",
                revision_validator=lambda revision: None,
                executor=executor,
            )

            with self.assertRaisesRegex(ValueError, "REVISE requires"):
                adapter.revise(reasoning_request())
            receipt = json.loads((
                Path(temporary)
                / "reasoning/campaign-1/entry/revision-1/receipt.json"
            ).read_text())
            self.assertEqual(receipt["status"], "failed")

    def test_authorized_revision_replays_without_a_second_codex_call(self):
        executor = FakeCodexExecutor({
            "decision": "REVISE",
            "rationale": "one bounded change",
            "config_override_json": '{"budget": 2}',
        })
        with tempfile.TemporaryDirectory() as temporary:
            adapter = CodexCliReasoningAdapter(
                repository_root=Path(temporary),
                receipt_root=Path(temporary) / "reasoning",
                prompt_builder=lambda request: "Keep the evaluator frozen.",
                revision_validator=lambda revision: None,
                executor=executor,
            )

            first = adapter.revise(reasoning_request())
            second = adapter.revise(reasoning_request())

            self.assertEqual(first, second)
            self.assertEqual(len(executor.requests), 1)

    def test_completed_invocation_recovers_before_repeating_codex(self):
        executor = FakeCodexExecutor({
            "decision": "REVISE",
            "rationale": "one bounded change",
            "config_override_json": '{"budget": 2}',
        })
        with tempfile.TemporaryDirectory() as temporary:
            receipt_root = Path(temporary) / "reasoning"
            adapter = CodexCliReasoningAdapter(
                repository_root=Path(temporary),
                receipt_root=receipt_root,
                prompt_builder=lambda request: "Keep the evaluator frozen.",
                revision_validator=lambda revision: None,
                executor=executor,
            )
            adapter.revise(reasoning_request())
            revision_root = receipt_root / "campaign-1/entry/revision-1"
            (revision_root / "receipt.json").unlink()
            for invocation in revision_root.glob("invocation-*"):
                (invocation / "receipt.json").unlink()
                (invocation / "execution.json").unlink()
                (invocation / "response.json").write_text(
                    json.dumps(executor.payload) + "\n"
                )
                (invocation / "exit.json").write_text(
                    '{"returncode": 0}\n'
                )

            recovered = adapter.revise(reasoning_request())

            self.assertEqual(recovered.decision, Decision.REVISE)
            self.assertEqual(len(executor.requests), 1)
            saved = json.loads((revision_root / "receipt.json").read_text())
            self.assertTrue(saved["recovered_completed_invocation"])

    def test_replay_rejects_execution_policy_drift(self):
        executor = FakeCodexExecutor({
            "decision": "REVISE",
            "rationale": "one bounded change",
            "config_override_json": '{"budget": 2}',
        })
        with tempfile.TemporaryDirectory() as temporary:
            common = {
                "repository_root": Path(temporary),
                "receipt_root": Path(temporary) / "reasoning",
                "prompt_builder": lambda request: "Keep the evaluator frozen.",
                "revision_validator": lambda revision: None,
                "executor": executor,
            }
            CodexCliReasoningAdapter(**common).revise(reasoning_request())

            changed = CodexCliReasoningAdapter(
                **common,
                sandbox="workspace-write",
            )
            with self.assertRaisesRegex(ValueError, "identity drifted"):
                changed.revise(reasoning_request())

    def test_revision_validator_is_required(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(TypeError, "revision_validator"):
                CodexCliReasoningAdapter(
                    repository_root=Path(temporary),
                    receipt_root=Path(temporary) / "reasoning",
                    prompt_builder=lambda request: "Keep the evaluator frozen.",
                    executor=FakeCodexExecutor({}),
                )

    def test_claude_stub_fails_closed_with_a_durable_receipt(self):
        with tempfile.TemporaryDirectory() as temporary:
            adapter = ClaudeCliReasoningAdapter(
                repository_root=Path(temporary),
                receipt_root=Path(temporary) / "reasoning",
                prompt_builder=lambda request: "One change only.",
            )

            with self.assertRaisesRegex(NotImplementedError, "not implemented"):
                adapter.revise(reasoning_request())

            receipt = json.loads((
                Path(temporary)
                / "reasoning/campaign-1/entry/revision-1/receipt.json"
            ).read_text())
            self.assertEqual(receipt["status"], "unavailable")
            self.assertEqual(receipt["provider"], "claude_cli")


if __name__ == "__main__":
    unittest.main()
