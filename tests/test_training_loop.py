from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from ml_training_loop import (
    Decision,
    GateResult,
    Phase,
    Revision,
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
