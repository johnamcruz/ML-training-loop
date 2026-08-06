from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from ml_training_loop import (
    Decision,
    GateResult,
    Phase,
    ReasoningOutcome,
    RetryableInfrastructureError,
    Revision,
    RunState,
    StageReceipt,
    StageSpec,
    TrainingLoop,
    TrainingPlan,
)
from ml_training_loop.adapters import DictAdapterRegistry
from ml_training_loop.domain import SkillBootstrapReceipt, SkillStatus
from ml_training_loop.stores import InMemoryRunStore, JsonRunStore


class RecordingSkills:
    def __init__(self, events, *, ready=True):
        self.events = events
        self.ready = ready
        self.required = ()

    def ensure(self, required):
        self.events.append("skills")
        self.required = required
        status = "already_present" if self.ready else "missing_from_bundle"
        return SkillBootstrapReceipt(tuple(
            SkillStatus(name=name, status=status) for name in required
        ))


class ScoreStage:
    def __init__(self, events, scores):
        self.events = events
        self.scores = iter(scores)
        self.requests = []

    def execute(self, request):
        self.events.append(f"stage:{request.stage.name}:{request.attempt}")
        self.requests.append(request)
        return StageReceipt(
            stage=request.stage.name,
            attempt=request.attempt,
            status="complete",
            outputs={"score": next(self.scores)},
        )


class ThresholdGate:
    def __init__(self, events, threshold=0.8):
        self.events = events
        self.threshold = threshold

    def evaluate(self, request):
        self.events.append(f"gate:{request.stage.name}:{request.receipt.attempt}")
        score = request.receipt.outputs["score"]
        return GateResult(
            decision=Decision.PROCEED if score >= self.threshold else Decision.REVISE,
            reason="threshold passed" if score >= self.threshold else "score too low",
            evidence={"score": score},
        )


class FixedGate:
    def __init__(self, decision):
        self.decision = decision

    def evaluate(self, request):
        return GateResult(self.decision, f"gate returned {self.decision.value}")


class OneRevisionReasoner:
    def __init__(self):
        self.requests = []

    def revise(self, request):
        self.requests.append(request)
        return Revision(
            stage=request.stage.name,
            rationale="increase declared budget once",
            config_override={"budget": 2},
        )


def plan(*stages, revisions=1):
    return TrainingPlan(
        name="generic-test",
        stages=tuple(stages),
        max_revisions_per_stage=revisions,
    )


class TrainingLoopTests(unittest.TestCase):
    def test_retryable_infrastructure_failure_retries_without_new_attempt(self):
        class TransientStage:
            def __init__(self):
                self.calls = 0

            def execute(self, request):
                self.calls += 1
                if self.calls == 1:
                    raise RetryableInfrastructureError("temporary SSD disconnect")
                return StageReceipt(
                    stage=request.stage.name,
                    attempt=request.attempt,
                    status="complete",
                    outputs={"score": 0.9},
                )

        events = []
        stage = TransientStage()
        result = TrainingLoop(
            adapters=DictAdapterRegistry(
                stages={"fit": stage}, gates={"quality": ThresholdGate(events)}
            ),
            store=InMemoryRunStore(),
            skills=RecordingSkills(events),
        ).run(plan(StageSpec("train", "fit", "quality")), "retry-run")

        self.assertEqual(result.phase, Phase.COMPLETE)
        self.assertEqual(stage.calls, 2)
        self.assertEqual(result.attempts, {"train": 1})
        self.assertEqual(len(result.receipts), 1)

    def test_untyped_stage_failure_is_not_retried(self):
        class BrokenStage:
            def __init__(self):
                self.calls = 0

            def execute(self, request):
                self.calls += 1
                raise RuntimeError("invalid training contract")

        events = []
        stage = BrokenStage()
        result = TrainingLoop(
            adapters=DictAdapterRegistry(
                stages={"fit": stage}, gates={"quality": ThresholdGate(events)}
            ),
            store=InMemoryRunStore(),
            skills=RecordingSkills(events),
        ).run(plan(StageSpec("train", "fit", "quality")), "no-retry-run")

        self.assertEqual(result.phase, Phase.BLOCKED)
        self.assertEqual(stage.calls, 1)

    def test_history_and_recovery_resume_after_execute_without_repeating_stage(self):
        events = []
        stage = ScoreStage(events, [0.9])
        store = InMemoryRunStore()
        training_plan = plan(StageSpec("train", "fit", "quality"))
        loop = TrainingLoop(
            adapters=DictAdapterRegistry(
                stages={"fit": stage}, gates={"quality": ThresholdGate(events)}
            ),
            store=store,
            skills=RecordingSkills(events),
        )
        completed = loop.run(training_plan, "recovery-run")
        self.assertEqual(completed.phase, Phase.COMPLETE)

        history = loop.history("recovery-run")
        validating = next(
            checkpoint
            for checkpoint in history
            if checkpoint.state.phase is Phase.VALIDATING
            and checkpoint.next_nodes == ("validate",)
        )
        recovered = loop.recover(
            training_plan,
            "recovery-run",
            validating.checkpoint_id,
        )

        self.assertEqual(recovered.phase, Phase.COMPLETE)
        self.assertEqual(len(stage.requests), 1)
        self.assertEqual(
            [checkpoint.created_at for checkpoint in history],
            sorted(checkpoint.created_at for checkpoint in history),
        )

    def test_json_history_and_recovery_survive_process_reconstruction(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            events = []
            stage = ScoreStage(events, [0.9])
            adapters = DictAdapterRegistry(
                stages={"fit": stage}, gates={"quality": ThresholdGate(events)}
            )
            training_plan = plan(StageSpec("train", "fit", "quality"))
            first = TrainingLoop(
                adapters=adapters,
                store=JsonRunStore(root),
                skills=RecordingSkills(events),
            )
            self.assertEqual(
                first.run(training_plan, "durable-recovery").phase,
                Phase.COMPLETE,
            )
            checkpoint_id = next(
                item.checkpoint_id
                for item in first.history("durable-recovery")
                if item.state.phase is Phase.VALIDATING
                and item.next_nodes == ("validate",)
            )

            reconstructed = TrainingLoop(
                adapters=adapters,
                store=JsonRunStore(root),
                skills=RecordingSkills(events),
            )
            recovered = reconstructed.recover(
                training_plan,
                "durable-recovery",
                checkpoint_id,
            )

            self.assertEqual(recovered.phase, Phase.COMPLETE)
            self.assertEqual(len(stage.requests), 1)

    def test_recovery_from_reasoning_interrupt_uses_the_reasoning_adapter(self):
        events = []
        stage = ScoreStage(events, [0.4, 0.9])
        store = InMemoryRunStore()
        adapters = DictAdapterRegistry(
            stages={"fit": stage}, gates={"quality": ThresholdGate(events)}
        )
        training_plan = plan(StageSpec("train", "fit", "quality"))
        paused_loop = TrainingLoop(
            adapters=adapters,
            store=store,
            skills=RecordingSkills(events),
        )
        self.assertEqual(
            paused_loop.run(training_plan, "reasoning-recovery").phase,
            Phase.NEEDS_REASONING,
        )
        checkpoint_id = next(
            item.checkpoint_id
            for item in reversed(paused_loop.history("reasoning-recovery"))
            if item.state.phase is Phase.NEEDS_REASONING
        )

        recovered = TrainingLoop(
            adapters=adapters,
            store=store,
            skills=RecordingSkills(events),
            reasoning=OneRevisionReasoner(),
        ).recover(training_plan, "reasoning-recovery", checkpoint_id)

        self.assertEqual(recovered.phase, Phase.COMPLETE)
        self.assertEqual([request.attempt for request in stage.requests], [1, 2])

    def test_installs_foundation_skills_before_executing_stages(self):
        events = []
        skills = RecordingSkills(events)
        stage = ScoreStage(events, [0.9])
        loop = TrainingLoop(
            adapters=DictAdapterRegistry(
                stages={"fit": stage}, gates={"quality": ThresholdGate(events)}
            ),
            store=InMemoryRunStore(),
            skills=skills,
        )

        result = loop.run(plan(StageSpec("train", "fit", "quality")), "run-1")

        self.assertEqual(result.phase, Phase.COMPLETE)
        self.assertEqual(events, ["skills", "stage:train:1", "gate:train:1"])
        self.assertIn("ml-rigor-workflow", skills.required)
        self.assertIn("ml-validate-temporal", skills.required)

    def test_two_model_family_agnostic_stages_share_one_state_machine(self):
        events = []
        stage = ScoreStage(events, [0.9, 0.95])
        loop = TrainingLoop(
            adapters=DictAdapterRegistry(
                stages={"action": stage}, gates={"quality": ThresholdGate(events)}
            ),
            store=InMemoryRunStore(),
            skills=RecordingSkills(events),
        )

        result = loop.run(plan(
            StageSpec("prepare", "action", "quality"),
            StageSpec("train", "action", "quality"),
        ), "run-2")

        self.assertEqual(result.phase, Phase.COMPLETE)
        self.assertEqual(result.stage_index, 2)
        self.assertEqual([receipt.stage for receipt in result.receipts], ["prepare", "train"])

    def test_one_controlled_revision_reruns_only_the_failed_stage(self):
        events = []
        stage = ScoreStage(events, [0.4, 0.9])
        reasoner = OneRevisionReasoner()
        loop = TrainingLoop(
            adapters=DictAdapterRegistry(
                stages={"fit": stage}, gates={"quality": ThresholdGate(events)}
            ),
            store=InMemoryRunStore(),
            skills=RecordingSkills(events),
            reasoning=reasoner,
        )

        result = loop.run(plan(StageSpec("train", "fit", "quality")), "run-3")

        self.assertEqual(result.phase, Phase.COMPLETE)
        self.assertEqual(result.attempts["train"], 2)
        self.assertEqual(len(result.revisions), 1)
        self.assertEqual(stage.requests[-1].config_override, {"budget": 2})
        self.assertEqual(reasoner.requests[0].required_skills, (
            "ml-rigor-workflow",
            "ml-diagnose-experiment",
            "ml-design-experiment",
        ))

    def test_reasoning_adapter_failure_blocks_instead_of_crashing(self):
        class BrokenReasoner:
            def revise(self, request):
                raise RuntimeError("Codex response was malformed")

        events = []
        loop = TrainingLoop(
            adapters=DictAdapterRegistry(
                stages={"fit": ScoreStage(events, [0.4])},
                gates={"quality": ThresholdGate(events)},
            ),
            store=InMemoryRunStore(),
            skills=RecordingSkills(events),
            reasoning=BrokenReasoner(),
        )

        result = loop.run(plan(StageSpec("train", "fit", "quality")), "run-bad-reasoning")

        self.assertEqual(result.phase, Phase.BLOCKED)
        self.assertIn("reasoning adapter failed", result.message)

    def test_reasoning_decline_stops_and_is_persisted(self):
        class DecliningReasoner:
            def revise(self, request):
                return None

        events = []
        store = InMemoryRunStore()
        loop = TrainingLoop(
            adapters=DictAdapterRegistry(
                stages={"fit": ScoreStage(events, [0.4])},
                gates={"quality": ThresholdGate(events)},
            ),
            store=store,
            skills=RecordingSkills(events),
            reasoning=DecliningReasoner(),
        )

        result = loop.run(plan(StageSpec("train", "fit", "quality")), "run-declined")

        self.assertEqual(result.phase, Phase.STOPPED)
        self.assertEqual(store.load("run-declined"), result)
        self.assertIn("declined", result.message)

    def test_reasoning_blocker_is_distinct_from_scientific_stop(self):
        class DispositionReasoner:
            def __init__(self, decision):
                self.decision = decision

            def revise(self, request):
                return ReasoningOutcome(
                    decision=self.decision,
                    rationale=f"reasoning chose {self.decision.value}",
                )

        for decision, phase in (
            (Decision.STOP, Phase.STOPPED),
            (Decision.BLOCKED, Phase.BLOCKED),
        ):
            with self.subTest(decision=decision):
                events = []
                result = TrainingLoop(
                    adapters=DictAdapterRegistry(
                        stages={"fit": ScoreStage(events, [0.4])},
                        gates={"quality": ThresholdGate(events)},
                    ),
                    store=InMemoryRunStore(),
                    skills=RecordingSkills(events),
                    reasoning=DispositionReasoner(decision),
                ).run(
                    plan(StageSpec("train", "fit", "quality")),
                    f"reasoning-{decision.value.lower()}",
                )
                self.assertEqual(result.phase, phase)

    def test_reasoning_checkpoint_resumes_without_repeating_completed_attempt(self):
        events = []
        stage = ScoreStage(events, [0.4, 0.9])
        store = InMemoryRunStore()
        adapters = DictAdapterRegistry(
            stages={"fit": stage}, gates={"quality": ThresholdGate(events)}
        )
        training_plan = plan(StageSpec("train", "fit", "quality"))
        paused = TrainingLoop(
            adapters=adapters,
            store=store,
            skills=RecordingSkills(events),
        ).run(training_plan, "run-4")

        self.assertEqual(paused.phase, Phase.NEEDS_REASONING)
        self.assertEqual(len(stage.requests), 1)

        resumed = TrainingLoop(
            adapters=adapters,
            store=store,
            skills=RecordingSkills(events),
            reasoning=OneRevisionReasoner(),
        ).run(training_plan, "run-4")

        self.assertEqual(resumed.phase, Phase.COMPLETE)
        self.assertEqual(len(stage.requests), 2)
        self.assertEqual(stage.requests[-1].attempt, 2)

    def test_missing_foundation_skill_blocks_before_execution(self):
        events = []
        stage = ScoreStage(events, [0.9])
        loop = TrainingLoop(
            adapters=DictAdapterRegistry(
                stages={"fit": stage}, gates={"quality": ThresholdGate(events)}
            ),
            store=InMemoryRunStore(),
            skills=RecordingSkills(events, ready=False),
        )

        result = loop.run(plan(StageSpec("train", "fit", "quality")), "run-5")

        self.assertEqual(result.phase, Phase.BLOCKED)
        self.assertEqual(events, ["skills"])

    def test_stop_and_blocked_gate_decisions_are_distinct_terminal_states(self):
        for decision, expected in (
            (Decision.STOP, Phase.STOPPED),
            (Decision.BLOCKED, Phase.BLOCKED),
        ):
            with self.subTest(decision=decision):
                events = []
                loop = TrainingLoop(
                    adapters=DictAdapterRegistry(
                        stages={"fit": ScoreStage(events, [0.9])},
                        gates={"decision": FixedGate(decision)},
                    ),
                    store=InMemoryRunStore(),
                    skills=RecordingSkills(events),
                )
                result = loop.run(
                    plan(StageSpec("train", "fit", "decision")),
                    f"run-{decision.value.lower()}",
                )
                self.assertEqual(result.phase, expected)

    def test_invalid_stage_receipt_fails_closed(self):
        class InvalidStage:
            def execute(self, request):
                return StageReceipt("different-stage", request.attempt, "complete")

        events = []
        loop = TrainingLoop(
            adapters=DictAdapterRegistry(
                stages={"invalid": InvalidStage()},
                gates={"quality": ThresholdGate(events)},
            ),
            store=InMemoryRunStore(),
            skills=RecordingSkills(events),
        )

        result = loop.run(
            plan(StageSpec("train", "invalid", "quality")), "run-invalid"
        )

        self.assertEqual(result.phase, Phase.BLOCKED)
        self.assertIn("invalid receipt", result.message)

    def test_terminal_resume_still_checks_required_skills_first(self):
        events = []
        store = InMemoryRunStore()
        training_plan = plan(StageSpec("train", "fit", "quality"))
        completed = TrainingLoop(
            adapters=DictAdapterRegistry(
                stages={"fit": ScoreStage(events, [0.9])},
                gates={"quality": ThresholdGate(events)},
            ),
            store=store,
            skills=RecordingSkills(events),
        ).run(training_plan, "terminal-run")
        self.assertEqual(completed.phase, Phase.COMPLETE)

        resume_events = []
        resumed = TrainingLoop(
            adapters=DictAdapterRegistry(),
            store=store,
            skills=RecordingSkills(resume_events),
        ).run(training_plan, "terminal-run")

        self.assertEqual(resumed.phase, Phase.COMPLETE)
        self.assertEqual(resume_events, ["skills"])

    def test_json_state_resumes_revision_without_repeating_completed_attempt(self):
        with tempfile.TemporaryDirectory() as temporary:
            events = []
            stage = ScoreStage(events, [0.4, 0.9])
            adapters = DictAdapterRegistry(
                stages={"fit": stage}, gates={"quality": ThresholdGate(events)}
            )
            store = JsonRunStore(Path(temporary))
            training_plan = plan(StageSpec("train", "fit", "quality"))

            paused = TrainingLoop(
                adapters=adapters,
                store=store,
                skills=RecordingSkills(events),
            ).run(training_plan, "durable-run")
            self.assertEqual(paused.phase, Phase.NEEDS_REASONING)

            resumed = TrainingLoop(
                adapters=adapters,
                store=JsonRunStore(Path(temporary)),
                skills=RecordingSkills(events),
                reasoning=OneRevisionReasoner(),
            ).run(training_plan, "durable-run")

            self.assertEqual(resumed.phase, Phase.COMPLETE)
            self.assertEqual([request.attempt for request in stage.requests], [1, 2])

    def test_pre_langgraph_json_state_migrates_without_repeating_completed_attempt(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            training_plan = plan(StageSpec("train", "fit", "quality"))
            JsonRunStore(root).save(RunState(
                run_id="legacy-run",
                plan_identity=training_plan.identity,
                phase=Phase.NEEDS_REASONING,
                attempts={"train": 1},
                receipts=(StageReceipt(
                    stage="train",
                    attempt=1,
                    status="complete",
                    outputs={"score": 0.4},
                ),),
                last_gate=GateResult(
                    decision=Decision.REVISE,
                    reason="score too low",
                    evidence={"score": 0.4},
                ),
                message="score too low",
            ))
            events = []
            stage = ScoreStage(events, [0.9])

            resumed = TrainingLoop(
                adapters=DictAdapterRegistry(
                    stages={"fit": stage},
                    gates={"quality": ThresholdGate(events)},
                ),
                store=JsonRunStore(root),
                skills=RecordingSkills(events),
                reasoning=OneRevisionReasoner(),
            ).run(training_plan, "legacy-run")

            self.assertEqual(resumed.phase, Phase.COMPLETE)
            self.assertEqual([request.attempt for request in stage.requests], [2])

    def test_run_id_cannot_resume_with_a_different_plan(self):
        events = []
        store = InMemoryRunStore()
        adapters = DictAdapterRegistry(
            stages={"fit": ScoreStage(events, [0.9])},
            gates={"quality": ThresholdGate(events)},
        )
        loop = TrainingLoop(
            adapters=adapters,
            store=store,
            skills=RecordingSkills(events),
        )
        loop.run(plan(StageSpec("train", "fit", "quality")), "identity-run")

        with self.assertRaisesRegex(ValueError, "different training plan"):
            loop.run(plan(StageSpec("different", "fit", "quality")), "identity-run")


if __name__ == "__main__":
    unittest.main()
