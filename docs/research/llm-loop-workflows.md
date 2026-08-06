# Open-source LLM and agent loop workflows

Research snapshot: 2026-08-05. Sources are official project repositories or official project documentation linked from those repositories.

## Bottom line

No surveyed project should be adopted as the ML Training Loop wholesale. The useful design is a composition:

1. **LangGraph-style durable state machine** for checkpointed transitions and explicit pause/resume.
2. **Inspect AI-style evaluation contract** for immutable task/solver/scorer separation, per-run limits, structured logs, and retrying infrastructure failures without changing the scientific verdict.
3. **DSPy-style bounded candidate optimization** for LLM prompts/programs, with the optimizer behind a revision-policy seam rather than inside the workflow engine.
4. **OpenHands/SWE-agent-style event and trajectory evidence** for auditable action/observation history, reproducible configuration, provider/tool seams, and explicit confirmation policy.

The shared engine should therefore own authenticated envelopes, durable state and receipts, idempotent replay/recovery, budgets, approvals, contract checks, and provider invocation. Consumer adapters should own the meaning of a candidate revision, skills/reasoning policy, training/evaluation commands, and domain-specific acceptance gates.

## Two different kinds of loop

These projects divide into two categories that should not be conflated:

- **Agent task loops** repeatedly reason, choose a tool/agent, observe, and stop or replan. Their strongest lessons concern durable execution, event history, approvals, provider/tool plugins, and turn/cost limits.
- **ML/LLM experiment loops** generate or select candidates, evaluate them on declared data and metrics, compare results, and freeze/promote a winner. Their strongest lessons concern immutable evaluation contracts, bounded search, failure classification, and separation of selection from final evaluation.

ML Training Loop needs both, but the experiment state machine must remain authoritative. An LLM reasoning loop should only propose a typed revision or decision; it must not silently mutate the research contract or directly decide scientific validity.

## Comparison

| Project | Kind | Reusable mechanics | Important gap / caution | Relevance |
|---|---|---|---|---|
| [LangGraph](https://github.com/langchain-ai/langgraph) | Agent/workflow runtime | Typed graph state, checkpointers, durable execution, resumable `interrupt`/`Command`, conditional routing, retry and timeout policy, subgraphs, provider-independent nodes. The [`interrupt` implementation and durability modes](https://github.com/langchain-ai/langgraph/blob/main/libs/langgraph/langgraph/types.py) make the resume contract explicit. | Resume can re-execute a node from its beginning, so side effects must be idempotent or separately receipted. A checkpoint is not by itself an authenticated experiment receipt, and LangGraph supplies no scientific revision/validation semantics. | **Best source for the orchestration seam**, not the research policy. Model each transition as a deterministic command over durable state; commit external effects through idempotency keys and receipts before advancing state. |
| [Inspect AI](https://github.com/UKGovernmentBEIS/inspect_ai) | LLM evaluation/experiment harness | Clean `Task` / dataset / solver / scorer decomposition; model/provider abstraction; sandboxed tools; limits; structured eval logs; retries and resumable evaluation workflows. Its companion [Inspect Evals SWE-bench implementation](https://github.com/UKGovernmentBEIS/inspect_evals/tree/main/src/inspect_evals/swe_bench) explicitly distinguishes infrastructure errors (eligible for retry) from an incorrect model result. | It evaluates model behavior; it is not a durable multi-stage training campaign engine and does not provide declared-revision governance or frozen-contract enforcement. | **Best source for the evaluation seam and failure taxonomy.** Preserve `contract + executor + scorer`, and distinguish retryable operational failure from a valid failed experiment. |
| [DSPy](https://github.com/stanfordnlp/dspy) | LLM program optimization | Declarative program modules and typed signatures; optimizers take a program, metric, and training inputs; bounded candidates/trials/demos; trace collection; candidate proposal and metric-based selection. The official [optimizer overview](https://github.com/stanfordnlp/dspy/blob/main/docs/docs/learn/optimization/optimizers.md) documents MIPROv2's trace, proposal, and discrete-search stages and explicit optimization budgets. | Optimizer state is not a durable workflow log; typical optimizers tune on a development set and can overfit it. It does not enforce sealed holdouts, authenticated lineage, or replay-safe external effects. | **Best source for a pluggable revision-policy interface.** Treat DSPy-like optimizers as bounded proposal engines whose candidate and evidence are serialized; do not let them own data splits, promotion, or final validation. |
| [OpenHands](https://github.com/OpenHands/OpenHands) and its [SDK docs repo](https://github.com/OpenHands/docs) | Software-agent task loop | Modular agent/reasoning loop, event model, persisted conversations, pause/resume, security/action confirmation, provider/tool/skill/plugin seams, stuck detection. The docs index links the primary guides for [persistence, pause/resume, plugins, security, skills, and reasoning](https://github.com/OpenHands/docs/blob/main/llms.txt). | Conversation persistence is not the same as authenticated scientific lineage. Its events are optimized for software-agent interaction, and provider reasoning traces should not become the stable domain contract. | Strong model for **append-only evidence, capability packaging, and separating confirmation policy from execution**. Borrow interfaces and event vocabulary, not its software-specific agent loop. |
| [SWE-agent](https://github.com/SWE-agent/SWE-agent) | Software-agent task/evaluation loop | Reproducible YAML configuration, per-instance trajectories, logs, replay model, hooks, environment abstraction, and cost limits. Its [trajectory documentation](https://github.com/SWE-agent/SWE-agent/blob/main/docs/usage/trajectories.md) states that each instance emits a trajectory plus the exact config needed to repeat it; the [model layer](https://github.com/SWE-agent/SWE-agent/blob/main/sweagent/agent/models.py) implements per-instance cost limiting and replay behavior. | Trajectory replay replays an agent interaction, not arbitrary training side effects. Scientific validity and immutable data/split identity remain outside the system. | Good concrete precedent for **request/response transcripts, exact repeat config, bounded provider spend, and replay adapters**. |
| [AutoGen / Magentic-One](https://github.com/microsoft/autogen) | Multi-agent task loop | Layered Core / AgentChat / Extensions architecture; event-driven local/distributed runtime; model client and tool extensions; termination conditions; Magentic-One task/progress ledgers, replanning after stalls, `max_turns`, and `max_stalls` in the [orchestrator implementation](https://github.com/microsoft/autogen/blob/main/python/packages/autogen-agentchat/src/autogen_agentchat/teams/_group_chat/_magentic_one/_magentic_one_group_chat.py). | AutoGen is now in maintenance mode and points new users to Microsoft Agent Framework. Magentic-One's ledger is LLM-authored planning state, not a tamper-evident receipt or scientific evidence record. Multi-agent conversation adds complexity without solving experiment governance. | Borrow the **stall/replan/termination pattern** and layered extension boundary; do not base the shared engine on a conversational multi-agent ledger. |
| [Microsoft Agent Framework](https://github.com/microsoft/agent-framework) | Current agent/workflow runtime | Successor to AutoGen with graph workflows, sequential/concurrent/handoff/group patterns, middleware, checkpointing, human-in-the-loop, provider independence, and Python/.NET APIs. | Newer and still evolving; checkpoint storage and workflow/thread semantics have had visible limitations. It remains agent orchestration rather than experiment governance. | Worth tracking as a current reference for **middleware and provider seams**, but not a reason to replace the smaller repository-local state machine now. |
| [Pydantic AI](https://github.com/pydantic/pydantic-ai) | Typed agent/eval runtime | Typed dependencies and outputs, model/provider abstraction, usage limits, evals, graphs, durable execution, deferred tools and human approval, composable capabilities. Its project overview explicitly treats tools, hooks, instructions, and model settings as reusable capabilities. | Broad and fast-moving. Durable execution still requires application-specific persistence/side-effect discipline; its generic usage limit is not an experiment budget or revision allowlist. | A strong secondary reference for **typed provider capability interfaces and validation at seams**. Prefer small Protocols/data contracts over importing the framework. |
| [Microsoft Conductor](https://github.com/microsoft/conductor) | Declarative agent workflow | YAML workflow graph, validation/dry-run, human gates, loop patterns, provider selection between Copilot and Claude, per-node token/cost visibility, registry/versioned workflows. | Young and oriented to interactive multi-agent work; declarative workflow files can become an unsafe command surface if allowed to rewrite scientific execution arbitrarily. | Useful direct analogue for **Codex/Claude provider adapters and declarative human gates**, provided recipes compile only to allowlisted commands and frozen fields cannot change. |

## Recommended seams for ML Training Loop

### 1. Durable engine, independent of reasoning provider

Use a small state-transition kernel with stable states such as `READY`, `RUNNING`, `NEEDS_REASONING`, `NEEDS_APPROVAL`, `VALIDATING`, and terminal outcomes. A transition consumes the current authenticated state plus a typed command and emits:

- a new state version;
- an append-only event/receipt;
- zero or more idempotent effect requests;
- a declared budget delta.

Adopt LangGraph's explicit pause/resume idea, but strengthen it: every effect gets a deterministic idempotency key, and recovery checks its durable receipt before executing again. Never depend on replaying arbitrary node code safely.

### 2. Authenticated envelope and frozen contract

Keep scientific context outside provider-native conversation state. The provider receives a versioned envelope containing hashes/identities for the contract, data, splits, code, checkpoint, allowed revisions, skills, evidence, remaining budget, and expected output schema. The returned decision must bind to that envelope identity.

OpenHands/SWE-agent events are useful evidence models, but ML Training Loop additionally needs authentication, causal lineage, and an allowlisted diff. Conversation or reasoning traces are supporting evidence, not authority.

### 3. Revision-policy plugin

Define a consumer-owned interface conceptually like:

```text
propose(context, allowed_revisions, remaining_budget) -> RevisionDecision
validate_revision(decision, frozen_contract) -> ValidatedRevision
compile(validated_revision) -> ExistingCommandPlan
```

FFM may select one declared SSL revision; FFM Strategies may propose a bounded experiment; supervised/RL consumers may expose different typed revision families. DSPy-like optimization can sit behind `propose`, but the shared engine validates and records the exact diff before execution.

### 4. Evaluation adapter, separate from orchestration

Follow Inspect's separation:

```text
frozen evaluation contract -> stage executor -> structured evidence -> deterministic validator
```

Classify outcomes at least as `VALID_PASS`, `VALID_FAIL`, `RETRYABLE_INFRA_ERROR`, `CONTRACT_VIOLATION`, and `BUDGET_EXHAUSTED`. Only the infrastructure class may repeat without consuming a scientific revision, and even that retry must be bounded and receipted.

### 5. Multi-dimensional budgets

Do not use only `max_turns`. Track independent ceilings for provider calls/tokens/cost, proposed revisions, stage attempts, infrastructure retries, wall time, and compute. AutoGen's `max_turns`/`max_stalls`, SWE-agent's per-instance cost limit, DSPy's candidate budget, and Inspect's eval limits are complementary, not substitutes.

### 6. Provider adapters should be narrow

The Codex and Claude adapters should translate the same authenticated request into provider calls and normalize the result into one schema. Skills, scientific rules, revision validation, receipts, and budget accounting remain outside adapters. Provider-specific reasoning content may be retained as an opaque artifact, but no downstream state transition should parse hidden chain-of-thought.

## What to implement now versus defer

Implement or retain now:

- typed, versioned state/events/receipts;
- idempotent effect requests and recovery;
- explicit reasoning and approval pauses;
- independent budget counters;
- frozen-contract hash plus allowlisted revision diff;
- narrow provider and consumer-policy protocols;
- deterministic outcome/failure classification.

Defer until two consumers prove identical behavior:

- a universal scientific-context schema beyond a small authenticated core;
- a universal skill sequence;
- generalized candidate generation/optimization;
- multi-agent orchestration;
- replacing the repository-local engine with LangGraph, Agent Framework, or another framework.

The best near-term move is therefore **design-level borrowing, not framework migration**. Run the FFM and FFM Strategies adapters through real terminal paths, then extract only mechanics whose inputs, outputs, retry behavior, and invariants are demonstrably identical.
