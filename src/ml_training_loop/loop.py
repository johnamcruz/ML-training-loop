"""The shared deterministic state machine."""
from __future__ import annotations

from dataclasses import replace
from typing import Mapping
from uuid import uuid4

from .domain import (
    Decision,
    Phase,
    ReasoningOutcome,
    Revision,
    RunState,
    StageReceipt,
    TrainingPlan,
)
from .interfaces import (
    AdapterRegistry,
    GateRequest,
    ReasoningAdapter,
    ReasoningRequest,
    RunStore,
    SkillBootstrapper,
    StageRequest,
)
from .skills import FOUNDATION_SKILLS


class TrainingLoop:
    """Run or resume a frozen plan through injected model-family adapters."""

    def __init__(
        self,
        *,
        adapters: AdapterRegistry,
        store: RunStore,
        skills: SkillBootstrapper,
        reasoning: ReasoningAdapter | None = None,
        baseline_skills: tuple[str, ...] = FOUNDATION_SKILLS,
    ) -> None:
        self._adapters = adapters
        self._store = store
        self._skills = skills
        self._reasoning = reasoning
        self._baseline_skills = baseline_skills

    def run(self, plan: TrainingPlan, run_id: str | None = None) -> RunState:
        run_id = run_id or uuid4().hex
        existing = self._store.load(run_id)
        if existing is not None and existing.plan_identity != plan.identity:
            raise ValueError("run id belongs to a different training plan")

        state = existing or RunState(
            run_id=run_id,
            plan_identity=plan.identity,
            phase=Phase.BOOTSTRAPPING,
        )
        self._store.save(state)

        required = tuple(dict.fromkeys(
            self._baseline_skills
            + plan.required_skills
            + tuple(skill for stage in plan.stages for skill in stage.required_skills)
        ))
        skill_receipt = self._skills.ensure(required)
        if not skill_receipt.ready:
            return self._finish(
                state,
                Phase.BLOCKED,
                "required Codex skills are unavailable",
            )
        if existing is not None and existing.terminal:
            return existing

        while state.stage_index < len(plan.stages):
            stage = plan.stages[state.stage_index]
            receipt = self._current_receipt(state, stage.name)

            if state.phase is Phase.NEEDS_REASONING:
                state = self._reason(plan, state, stage, receipt)
                if state.phase is Phase.NEEDS_REASONING or state.terminal:
                    return state
                receipt = None

            if receipt is None or state.phase is not Phase.VALIDATING:
                attempt = state.attempts.get(stage.name, 0) + 1
                override = self._override_for(state.revisions, stage.name)
                state = replace(state, phase=Phase.EXECUTING, last_gate=None)
                self._store.save(state)
                try:
                    receipt = self._adapters.stage(stage.stage_adapter).execute(
                        StageRequest(
                            run_id=run_id,
                            plan_identity=plan.identity,
                            stage=stage,
                            attempt=attempt,
                            prior_receipts=state.receipts,
                            config_override=override,
                        )
                    )
                except Exception as error:
                    return self._finish(
                        state,
                        Phase.BLOCKED,
                        f"stage {stage.name} failed: {type(error).__name__}: {error}",
                    )
                if (
                    receipt.stage != stage.name
                    or receipt.attempt != attempt
                    or receipt.status != "complete"
                ):
                    return self._finish(
                        state,
                        Phase.BLOCKED,
                        f"stage {stage.name} returned an invalid receipt",
                    )
                attempts = {**state.attempts, stage.name: attempt}
                state = replace(
                    state,
                    phase=Phase.VALIDATING,
                    attempts=attempts,
                    receipts=state.receipts + (receipt,),
                    last_gate=None,
                )
                self._store.save(state)

            gate = state.last_gate
            if gate is None:
                try:
                    gate = self._adapters.gate(stage.gate_adapter).evaluate(
                        GateRequest(
                            run_id=run_id,
                            plan_identity=plan.identity,
                            stage=stage,
                            receipt=receipt,
                            prior_receipts=state.receipts[:-1],
                        )
                    )
                except Exception as error:
                    return self._finish(
                        state,
                        Phase.BLOCKED,
                        f"gate {stage.gate_adapter} failed: {type(error).__name__}: {error}",
                    )
                state = replace(state, last_gate=gate)
                self._store.save(state)

            if gate.decision is Decision.PROCEED:
                state = replace(
                    state,
                    phase=Phase.EXECUTING,
                    stage_index=state.stage_index + 1,
                    last_gate=None,
                )
                self._store.save(state)
                continue
            if gate.decision is Decision.BLOCKED:
                return self._finish(state, Phase.BLOCKED, gate.reason)
            if gate.decision is Decision.STOP:
                return self._finish(state, Phase.STOPPED, gate.reason)

            state = replace(
                state,
                phase=Phase.NEEDS_REASONING,
                message=gate.reason,
            )
            self._store.save(state)
            state = self._reason(plan, state, stage, receipt)
            if state.phase is Phase.NEEDS_REASONING or state.terminal:
                return state

        return self._finish(state, Phase.COMPLETE, "all stages proceeded")

    def status(self, run_id: str) -> RunState | None:
        return self._store.load(run_id)

    @staticmethod
    def _override_for(revisions: tuple[Revision, ...], stage: str) -> Mapping:
        for revision in reversed(revisions):
            if revision.stage == stage:
                return revision.config_override
        return {}

    @staticmethod
    def _current_receipt(state: RunState, stage: str) -> StageReceipt | None:
        if state.receipts and state.receipts[-1].stage == stage:
            return state.receipts[-1]
        return None

    def _reason(
        self,
        plan: TrainingPlan,
        state: RunState,
        stage,
        receipt: StageReceipt | None,
    ) -> RunState:
        gate = state.last_gate
        if receipt is None or gate is None or gate.decision is not Decision.REVISE:
            return self._finish(
                state,
                Phase.BLOCKED,
                "reasoning checkpoint lacks a valid receipt or REVISE gate",
            )
        revisions = sum(item.stage == stage.name for item in state.revisions)
        if revisions >= plan.max_revisions_per_stage:
            return self._finish(
                state,
                Phase.FAILED_GATE,
                f"stage {stage.name} exhausted its controlled revisions",
            )
        if self._reasoning is None:
            return state
        try:
            reasoned = self._reasoning.revise(
                ReasoningRequest(
                    run_id=state.run_id,
                    plan=plan,
                    stage=stage,
                    receipt=receipt,
                    gate=gate,
                    revision_number=revisions + 1,
                    required_skills=tuple(dict.fromkeys((
                        "ml-rigor-workflow",
                        "ml-diagnose-experiment",
                        "ml-design-experiment",
                        *stage.required_skills,
                    ))),
                    prior_revisions=state.revisions,
                    effective_config_override=self._override_for(
                        state.revisions, stage.name
                    ),
                )
            )
        except Exception as error:
            return self._finish(
                state,
                Phase.BLOCKED,
                f"reasoning adapter failed: {type(error).__name__}: {error}",
            )
        if reasoned is None:
            return self._finish(
                state,
                Phase.STOPPED,
                "reasoning adapter declined a further revision",
            )
        if isinstance(reasoned, ReasoningOutcome):
            if reasoned.decision is Decision.STOP:
                return self._finish(state, Phase.STOPPED, reasoned.rationale)
            if reasoned.decision is Decision.BLOCKED:
                return self._finish(state, Phase.BLOCKED, reasoned.rationale)
            revision = reasoned.revision
            if revision is None:
                return self._finish(
                    state,
                    Phase.BLOCKED,
                    "REVISE reasoning outcome omitted its revision",
                )
        elif isinstance(reasoned, Revision):
            revision = reasoned
        else:
            return self._finish(
                state,
                Phase.BLOCKED,
                "reasoning adapter returned an unsupported outcome",
            )
        if revision.stage != stage.name:
            return self._finish(
                state,
                Phase.BLOCKED,
                "reasoning adapter attempted to revise a different stage",
            )
        revised = replace(
            state,
            phase=Phase.EXECUTING,
            revisions=state.revisions + (revision,),
            last_gate=None,
            message=revision.rationale,
        )
        self._store.save(revised)
        return revised

    def _finish(self, state: RunState, phase: Phase, message: str) -> RunState:
        finished = replace(state, phase=phase, message=message)
        self._store.save(finished)
        return finished
