"""LangGraph-backed orchestration behind the stable training-loop interface."""
from __future__ import annotations

from dataclasses import replace
from typing import Any, Literal, Mapping, TypedDict
from uuid import uuid4

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, RetryPolicy, interrupt

from .domain import (
    Decision,
    Phase,
    ReasoningOutcome,
    RetryableInfrastructureError,
    Revision,
    RunCheckpoint,
    RunState,
    StageReceipt,
    SurrogateAdvice,
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
    SurrogateAdvisor,
    SurrogateRequest,
)
from .ledger import ExperimentLedger
from .skills import FOUNDATION_SKILLS
from .stores import run_state_from_payload, run_state_to_payload


class _GraphState(TypedDict):
    """Stable primitive checkpoint state owned by LangGraph."""

    run_id: str
    run_state: dict[str, Any]


_Route = Literal["execute", "validate", "reason", "__end__"]


class TrainingLoop:
    """Run or resume a frozen plan through injected model-family adapters.

    LangGraph owns orchestration and routing. The existing ML-specific domain
    contracts, adapters, receipts, reasoning policy, and stores remain the
    stable public interface.
    """

    def __init__(
        self,
        *,
        adapters: AdapterRegistry,
        store: RunStore,
        skills: SkillBootstrapper,
        reasoning: ReasoningAdapter | None = None,
        surrogate: SurrogateAdvisor | None = None,
        baseline_skills: tuple[str, ...] = FOUNDATION_SKILLS,
    ) -> None:
        self._adapters = adapters
        self._store = store
        self._skills = skills
        self._reasoning = reasoning
        self._surrogate = surrogate
        self._baseline_skills = baseline_skills
        self._plans: dict[str, TrainingPlan] = {}
        checkpointer_factory = getattr(store, "_langgraph_checkpointer", None)
        self._checkpointer = (
            checkpointer_factory()
            if checkpointer_factory is not None
            else InMemorySaver()
        )
        self._graph = self._compile_graph()

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
        self._plans[run_id] = plan

        config = {
            "configurable": {"thread_id": run_id},
            "recursion_limit": self._recursion_limit(plan),
        }
        checkpoint = self._graph.get_state(config)
        if checkpoint.next:
            if state.phase is Phase.NEEDS_REASONING:
                if self._reasoning is None:
                    return state
                graph_input = Command(resume={"action": "reason"})
            else:
                graph_input = None
        else:
            graph_input = self._graph_state(state)
        self._graph.invoke(graph_input, config=config, durability="sync")
        result = self._store.load(run_id)
        if result is None:
            raise RuntimeError("LangGraph completed without durable run state")
        return result

    def status(self, run_id: str) -> RunState | None:
        return self._store.load(run_id)

    def history(self, run_id: str) -> tuple[RunCheckpoint, ...]:
        """Return durable execution history in chronological order."""

        snapshots = self._graph.get_state_history(self._config(run_id))
        checkpoints = []
        for snapshot in snapshots:
            payload = snapshot.values.get("run_state") if snapshot.values else None
            checkpoint_id = snapshot.config.get("configurable", {}).get(
                "checkpoint_id"
            )
            if (
                payload is None
                or checkpoint_id is None
                or snapshot.created_at is None
            ):
                continue
            checkpoints.append(RunCheckpoint(
                checkpoint_id=checkpoint_id,
                created_at=snapshot.created_at,
                next_nodes=tuple(snapshot.next),
                state=run_state_from_payload(payload),
            ))
        return tuple(reversed(checkpoints))

    def recover(
        self,
        plan: TrainingPlan,
        run_id: str,
        checkpoint_id: str,
    ) -> RunState:
        """Explicitly branch and resume from one inspected durable checkpoint."""

        current = self._store.load(run_id)
        if current is None:
            raise ValueError("run id has no durable training state")
        if current.plan_identity != plan.identity:
            raise ValueError("run id belongs to a different training plan")
        snapshot = next(
            (
                item
                for item in self._graph.get_state_history(self._config(run_id))
                if item.config.get("configurable", {}).get("checkpoint_id")
                == checkpoint_id
            ),
            None,
        )
        if snapshot is None:
            raise ValueError("checkpoint does not belong to this run")
        payload = snapshot.values.get("run_state") if snapshot.values else None
        if payload is None:
            raise ValueError("checkpoint predates recoverable domain state")
        recovered = run_state_from_payload(payload)
        if recovered.plan_identity != plan.identity or recovered.run_id != run_id:
            raise ValueError("checkpoint identity does not match the training plan")

        self._plans[run_id] = plan
        self._store.save(recovered)
        if recovered.phase is Phase.NEEDS_REASONING:
            if self._reasoning is None:
                return recovered
            graph_input = Command(resume={"action": "reason"})
        else:
            graph_input = None
        recovery_config = {
            **snapshot.config,
            "recursion_limit": self._recursion_limit(plan),
        }
        self._graph.invoke(
            graph_input,
            config=recovery_config,
            durability="sync",
        )
        result = self._store.load(run_id)
        if result is None:
            raise RuntimeError("LangGraph recovery lost durable run state")
        return result

    def _compile_graph(self):
        graph = StateGraph(_GraphState)
        retry = RetryPolicy(
            initial_interval=0.1,
            max_interval=1.0,
            max_attempts=3,
            jitter=False,
            retry_on=RetryableInfrastructureError,
        )
        graph.add_node("bootstrap", self._bootstrap, retry_policy=retry)
        graph.add_node("execute", self._execute, retry_policy=retry)
        graph.add_node("validate", self._validate, retry_policy=retry)
        graph.add_node("reason", self._reason, retry_policy=retry)
        graph.add_edge(START, "bootstrap")
        graph.add_conditional_edges("bootstrap", self._route)
        graph.add_conditional_edges("execute", self._route)
        graph.add_conditional_edges("validate", self._route)
        graph.add_conditional_edges("reason", self._route)
        return graph.compile(checkpointer=self._checkpointer)

    def _bootstrap(self, graph: _GraphState) -> _GraphState:
        plan, state = self._context(graph)
        required = tuple(dict.fromkeys(
            self._baseline_skills
            + plan.required_skills
            + tuple(
                skill
                for stage in plan.stages
                for skill in stage.required_skills
            )
        ))
        skill_receipt = self._skills.ensure(required)
        if not skill_receipt.ready:
            state = self._finish(
                state,
                Phase.BLOCKED,
                "required Codex skills are unavailable",
            )
        elif not state.terminal and state.stage_index >= len(plan.stages):
            state = self._finish(state, Phase.COMPLETE, "all stages proceeded")
        return self._graph_state(state)

    def _execute(self, graph: _GraphState) -> _GraphState:
        plan, state = self._context(graph)
        stage = plan.stages[state.stage_index]
        attempt = state.attempts.get(stage.name, 0) + 1
        override = self._override_for(state.revisions, stage.name)
        state = replace(state, phase=Phase.EXECUTING, last_gate=None)
        self._store.save(state)
        try:
            receipt = self._adapters.stage(stage.stage_adapter).execute(
                StageRequest(
                    run_id=state.run_id,
                    plan_identity=plan.identity,
                    stage=stage,
                    attempt=attempt,
                    prior_receipts=state.receipts,
                    config_override=override,
                )
            )
        except RetryableInfrastructureError:
            raise
        except Exception as error:
            state = self._finish(
                state,
                Phase.BLOCKED,
                f"stage {stage.name} failed: {type(error).__name__}: {error}",
            )
            return self._graph_state(state)

        if (
            receipt.stage != stage.name
            or receipt.attempt != attempt
            or receipt.status != "complete"
        ):
            state = self._finish(
                state,
                Phase.BLOCKED,
                f"stage {stage.name} returned an invalid receipt",
            )
            return self._graph_state(state)

        state = replace(
            state,
            phase=Phase.VALIDATING,
            attempts={**state.attempts, stage.name: attempt},
            receipts=state.receipts + (receipt,),
            last_gate=None,
        )
        self._store.save(state)
        return self._graph_state(state)

    def _validate(self, graph: _GraphState) -> _GraphState:
        plan, state = self._context(graph)
        stage = plan.stages[state.stage_index]
        receipt = self._current_receipt(state, stage.name)
        if receipt is None:
            state = self._finish(
                state,
                Phase.BLOCKED,
                f"stage {stage.name} validation lacks a completed receipt",
            )
            return self._graph_state(state)

        gate = state.last_gate
        if gate is None:
            try:
                gate = self._adapters.gate(stage.gate_adapter).evaluate(
                    GateRequest(
                        run_id=state.run_id,
                        plan_identity=plan.identity,
                        stage=stage,
                        receipt=receipt,
                        prior_receipts=state.receipts[:-1],
                    )
                )
            except RetryableInfrastructureError:
                raise
            except Exception as error:
                state = self._finish(
                    state,
                    Phase.BLOCKED,
                    f"gate {stage.gate_adapter} failed: "
                    f"{type(error).__name__}: {error}",
                )
                return self._graph_state(state)
            state = replace(state, last_gate=gate)
            self._store.save(state)

        if gate.decision is Decision.PROCEED:
            next_index = state.stage_index + 1
            if next_index >= len(plan.stages):
                state = self._finish(
                    replace(state, stage_index=next_index, last_gate=None),
                    Phase.COMPLETE,
                    "all stages proceeded",
                )
            else:
                state = replace(
                    state,
                    phase=Phase.EXECUTING,
                    stage_index=next_index,
                    last_gate=None,
                )
                self._store.save(state)
        elif gate.decision is Decision.BLOCKED:
            state = self._finish(state, Phase.BLOCKED, gate.reason)
        elif gate.decision is Decision.STOP:
            state = self._finish(state, Phase.STOPPED, gate.reason)
        else:
            state = replace(
                state,
                phase=Phase.NEEDS_REASONING,
                message=gate.reason,
            )
            self._store.save(state)
        return self._graph_state(state)

    def _reason(self, graph: _GraphState) -> _GraphState:
        plan, state = self._context(graph)
        stage = plan.stages[state.stage_index]
        receipt = self._current_receipt(state, stage.name)
        gate = state.last_gate
        if receipt is None or gate is None or gate.decision is not Decision.REVISE:
            state = self._finish(
                state,
                Phase.BLOCKED,
                "reasoning checkpoint lacks a valid receipt or REVISE gate",
            )
            return self._graph_state(state)

        revisions = sum(item.stage == stage.name for item in state.revisions)
        if revisions >= plan.max_revisions_per_stage:
            state = self._finish(
                state,
                Phase.FAILED_GATE,
                f"stage {stage.name} exhausted its controlled revisions",
            )
            return self._graph_state(state)
        if self._reasoning is None:
            interrupt({
                "run_id": state.run_id,
                "stage": stage.name,
                "reason": gate.reason,
                "revision_number": revisions + 1,
            })
            return self._graph_state(state)

        try:
            experiment_ledger = ExperimentLedger.from_run_state(state)
        except (TypeError, ValueError) as error:
            state = self._finish(
                state,
                Phase.BLOCKED,
                f"experiment ledger is invalid: {error}",
            )
            return self._graph_state(state)

        surrogate_advice = None
        if self._surrogate is not None:
            try:
                surrogate_advice = self._surrogate.advise(SurrogateRequest(
                    run_id=state.run_id,
                    plan=plan,
                    stage=stage,
                    receipt=receipt,
                    gate=gate,
                    revision_number=revisions + 1,
                    prior_receipts=state.receipts,
                    prior_revisions=state.revisions,
                    effective_config_override=self._override_for(
                        state.revisions, stage.name
                    ),
                    experiment_ledger=experiment_ledger,
                ))
                if (
                    surrogate_advice is not None
                    and not isinstance(surrogate_advice, SurrogateAdvice)
                ):
                    raise TypeError(
                        "surrogate advisor returned invalid advice"
                    )
            except RetryableInfrastructureError:
                raise
            except Exception as error:
                state = self._finish(
                    state,
                    Phase.BLOCKED,
                    f"surrogate advisor failed: {type(error).__name__}: {error}",
                )
                return self._graph_state(state)

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
                    surrogate_advice=surrogate_advice,
                    experiment_ledger=experiment_ledger,
                )
            )
        except RetryableInfrastructureError:
            raise
        except Exception as error:
            state = self._finish(
                state,
                Phase.BLOCKED,
                f"reasoning adapter failed: {type(error).__name__}: {error}",
            )
            return self._graph_state(state)

        if reasoned is None:
            state = self._finish(
                state,
                Phase.STOPPED,
                "reasoning adapter declined a further revision",
            )
            return self._graph_state(state)
        if isinstance(reasoned, ReasoningOutcome):
            if reasoned.decision is Decision.STOP:
                state = self._finish(state, Phase.STOPPED, reasoned.rationale)
                return self._graph_state(state)
            if reasoned.decision is Decision.BLOCKED:
                state = self._finish(state, Phase.BLOCKED, reasoned.rationale)
                return self._graph_state(state)
            revision = reasoned.revision
            if revision is None:
                state = self._finish(
                    state,
                    Phase.BLOCKED,
                    "REVISE reasoning outcome omitted its revision",
                )
                return self._graph_state(state)
        elif isinstance(reasoned, Revision):
            revision = reasoned
        else:
            state = self._finish(
                state,
                Phase.BLOCKED,
                "reasoning adapter returned an unsupported outcome",
            )
            return self._graph_state(state)

        if revision.stage != stage.name:
            state = self._finish(
                state,
                Phase.BLOCKED,
                "reasoning adapter attempted to revise a different stage",
            )
            return self._graph_state(state)

        state = replace(
            state,
            phase=Phase.EXECUTING,
            revisions=state.revisions + (revision,),
            last_gate=None,
            message=revision.rationale,
        )
        self._store.save(state)
        return self._graph_state(state)

    def _route(self, graph: _GraphState) -> _Route:
        _, state = self._context(graph)
        if state.terminal:
            return END
        if state.phase is Phase.NEEDS_REASONING:
            return "reason"
        if state.phase is Phase.VALIDATING:
            return "validate"
        return "execute"

    def _context(self, graph: _GraphState) -> tuple[TrainingPlan, RunState]:
        run_id = graph["run_id"]
        try:
            plan = self._plans[run_id]
        except KeyError as error:
            raise RuntimeError(f"training plan is unavailable for run {run_id}") from error
        payload = graph.get("run_state")
        state = (
            run_state_from_payload(payload)
            if payload is not None
            else self._store.load(run_id)
        )
        if state is None:
            raise RuntimeError(f"durable state is unavailable for run {run_id}")
        return plan, state

    @staticmethod
    def _graph_state(state: RunState) -> _GraphState:
        return {
            "run_id": state.run_id,
            "run_state": run_state_to_payload(state),
        }

    @staticmethod
    def _config(run_id: str) -> dict:
        return {"configurable": {"thread_id": run_id}}

    @staticmethod
    def _recursion_limit(plan: TrainingPlan) -> int:
        transitions_per_stage = 3 + (3 * plan.max_revisions_per_stage)
        return max(25, len(plan.stages) * transitions_per_stage + 5)

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

    def _finish(self, state: RunState, phase: Phase, message: str) -> RunState:
        finished = replace(state, phase=phase, message=message)
        self._store.save(finished)
        return finished
