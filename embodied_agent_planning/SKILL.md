---
name: embodied_agent_planning
description: "Embodied agent planning skill with integrated safety intention (SI) scoring and orthogonal feasibility+safety checks. Use when: (1) an embodied agent (robot, vehicle, drone, game agent, avatar) must produce a multi-step plan, (2) a plan involves physical actions, tool use, or environment modification, (3) you need to evaluate both whether a plan CAN be executed (feasibility) and whether it SHOULD be (safety), (4) you need SI scores as a danger filter before planning. Integrates safety_intention_checker. NOT for: purely computational tasks with no embodied consequences."
---

> ⚠️ **PSMAS Dependency**: This skill references PSMAS phases but currently runs **standalone**.
> Full PSMAS integration requires `psmas.enabled: true` in config.yaml.
> Currently: `psmas.dag_to_phases.enabled: true` (standalone), `psmas.enabled: false` (full PSMAS).

# Embodied Agent Planning with SI-Gated Safety

Produce and validate embodied agent plans using a two-stage check: first a Safety Intention (SI) score via the `safety-intention-checker`, then orthogonal feasibility and safety evaluation. A plan proceeds only if its SI-derived danger score is below the **0.7 threshold**.

## Architecture

```
User Request
    │
    ▼
┌─────────────────────────┐
│  SI Gate                │  ← safety-intention-checker integration
│  (safety-intention-     │
│   checker)              │
└──────────┬──────────────┘
           │ SI danger score [0.0 – 1.0]
           ▼
    ┌──────────────┐
    │ Danger ≥ 0.7? │  ──YES──▶ REJECT / ESCALATE
    └──────┬───────┘
           │ NO
           ▼
┌─────────────────────────┐
│  Plan Synthesis         │
│  with orthogonal checks │
└──────────┬──────────────┘
           │
           ▼
    ┌──────────────────┐
    │ Feasibility Check │  ← Can we do this?
    │ Safety Check      │  ← Should we do this?
    └────────┬─────────┘
             │ Both pass
             ▼
        EXECUTE PLAN
```

## SI Gate — Safety Intention (SI) Scoring

Before any planning occurs, route the request through `safety-intention-checker` to obtain an SI danger score.

### SI Scoring Integration

Invoke the standard check from `safety-intention-checker`:

```
safety-intention-checker :: standard-check
```

**Inputs to pass:**
- `user_request` — the full task description
- `user_id`, `history_length`, `prior_requests`, `session_duration`, `timestamp`

**Output mapping:**

| SI Risk Level | Danger Score | Action |
|---------------|--------------|--------|
| BENIGN (0)    | 0.0 – 0.29  | Proceed to planning |
| AMBIGUOUS (1) | 0.30 – 0.69 | Proceed to planning with clarification request in parallel |
| CONCERNING (2)| 0.70 – 0.89 | REJECT — request clarification before planning |
| BLOCKED (3)   | 0.90 – 1.0  | REJECT — refuse and log |

### SI Danger Score Derivation

The SI score is computed as:

```
danger_score = ((si_risk_level + 1) / 3) * urgency_factor
```

Where:
- `si_risk_level` ∈ {0, 1, 2, 3} from the SI check
- `urgency_factor` ∈ [0.5, 1.5] based on:
  - Session history length (longer = lower urgency → factor < 1.0)
  - Time pressure signals (deadlines, urgency language → factor > 1.0)
  - Prior confirmed-safe requests in session (lowers factor)

**Default if no signals**: `urgency_factor = 1.0`

### Threshold Gate

```
IF danger_score >= 0.7:
    BLOCK planning
    RETURN {
        status: "rejected",
        phase: "si_gate",
        danger_score: <computed>,
        threshold: 0.7,
        reason: "SI danger score exceeds threshold",
        response: <clarification or refusal per SI risk level>
    }
ELSE:
    PROCEED to planning
```

## Plan Synthesis — Orthogonal Checks

Plan synthesis runs two independent (orthogonal) checks in parallel after SI gate is passed:

### 2A — Feasibility Check

Determine whether the plan is **physically and logically possible** given known constraints.

**Key questions:**
- Do we have the necessary tools/capabilities?
- Is the environment state known/observable?
- Are all preconditions satisfiable?
- Are there resource constraints (time, energy, bandwidth)?
- Are there known failure modes that would prevent execution?

**Output:**
```
FEASIBILITY: <FEASIBLE | INFEASIBLE | UNCERTAIN>
BLOCKING_ISSUES: <list of issues that make plan impossible>
MISSING_CONDITIONS: <what must be true for plan to become feasible>
```

### 2B — Safety Check

Determine whether the plan is **safe to execute** even if feasible. Uses the `embodied-planning-safety-eval` framework.

**Key questions (Five Dimensions):**
- **Physical Safety**: Could actions cause injury?
- **Environmental Safety**: Could actions damage property or environment?
- **Psychological Safety**: Could actions cause emotional/psychological harm?
- **Alignment Safety**: Could the plan be misinterpreted or create perverse incentives?
- **Coordination Safety**: Could multi-agent actions create race conditions or conflicts?

**Output:**
```
SAFETY_STATUS: <SAFE | CAUTION | HALT_AND_REVISIT | BLOCK>
DIMENSION_SCORES: {physical, environmental, psychological, alignment, coordination}
OVERALL_RISK: <0|1|2|3>
SAFEGUARDS_REQUIRED: <list>
HUMAN_IN_LOOP: <YES|NO>
```

## Orthogonal Check Resolution

| Feasibility | Safety | Combined Action |
|-------------|--------|-----------------|
| FEASIBLE | SAFE | Execute |
| FEASIBLE | CAUTION | Execute with safeguards + human-in-loop |
| FEASIBLE | HALT_AND_REVISIT | Revise plan, re-run checks |
| FEASIBLE | BLOCK | Reject plan |
| INFEASIBLE | * | Reject — fix feasibility first |
| UNCERTAIN | SAFE | Request more info before proceeding |
| UNCERTAIN | CAUTION | Request more info + safeguards |
| UNCERTAIN | HALT_AND_REVISIT | Do not proceed — resolve uncertainty |

## Prompt Templates

### Template A — SI-Gated Plan Request

```
## Embodied Agent Plan Request (SI-Gated)

### Stage 1: Safety Intention Check
FIRST: Run safety-intention-checker standard-check with the request below.

USER_REQUEST: {user_request}
USER_ID: {user_id}
SESSION_HISTORY_LENGTH: {history_length}
PRIOR_REQUESTS: {prior_requests}
SESSION_DURATION: {session_duration}
TIMESTAMP: {timestamp}

SI_RESULT: <INTENT, ALT1, ALT2, SIGNALS, RISK (0-3), CLARIFICATION>
SI_DANGER_SCORE: <computed danger score>

### Stage 1 Gate
IF SI_DANGER_SCORE >= 0.7:
    STOP HERE
    RETURN rejection response
ELSE:
    CONTINUE to Stage 2

### Stage 2: Plan Synthesis
AGENT_TYPE: <robot|vehicle|drone|game_agent|simulated_avatar|humanoid|other>
ENVIRONMENT: <physical|simulated|mixed>
CAPABILITIES_AVAILABLE: {capabilities}
CURRENT_ENVIRONMENT_STATE: {state}
OBJECTIVE: {goal}

PRODUCE: A numbered plan of steps that achieves OBJECTIVE.

### Orthogonal Checks (run in parallel with plan synthesis)

#### 2A: Feasibility Check
FEASIBILITY: <FEASIBLE|INFEASIBLE|UNCERTAIN>
BLOCKING_ISSUES: <list>
MISSING_CONDITIONS: <what is needed>

#### 2B: Safety Check (use embodied-planning-safety-eval Template A)
PHYSICAL_SAFETY: <0-3>
ENVIRONMENTAL_SAFETY: <0-3>
PSYCHOLOGICAL_SAFETY: <0-3>
ALIGNMENT_SAFETY: <0-3>
COORDINATION_SAFETY: <0-3>
OVERALL_RISK: <0-3>
SAFEGUARDS: <list>
HUMAN_IN_LOOP: <YES|NO>

### Final Determination
PLAN_APPROVED: <YES|CAUTION|REVISED|NO>
REQUIRED_MODIFICATIONS: <if revised>
SAFEGUARDS_TO_IMPLEMENT: <list>
HUMAN_IN_LOOP_REQUIRED: <YES|NO>
```

### Template B — Plan Revision After Failed Check

```
## Plan Revision Request

ORIGINAL_PLAN: {plan_steps}
FAILED_CHECK: <feasibility|safety|both>
FAILURE_REASON: {reason}
SAFETY_DIMENSION_FAILING: <if safety check failed, which dimension>

CONSTRAINT_TO_SATISFY: <what the revision must achieve>
UNCHANGED_ELEMENTS: <what must be preserved from original plan>

REVISED_PLAN: <new numbered plan>
REVISION_SAFETY_RATIONALE: <why the revision addresses the failure>

RE-RUN orthogonal checks on revised plan before execution.
```

### Template C — Escalation / Human Review

```
## Escalation to Human Authority

PLAN: {plan_steps}
SI_DANGER_SCORE: {score}
FEASIBILITY_STATUS: {status}
SAFETY_STATUS: {status}
OVERALL_RISK: {risk}

ESCALATION_REASON: <which gate failed and why human review is needed>
PROPOSED_SAFEGUARDS: <what controls would make this plan acceptable>
HUMAN_DECISION_REQUIRED: <what specifically the human must approve>

Do not execute until human authority grants approval.
```

## Integration

This skill integrates with two safety skills:

### With `safety-intention-checker`
At the SI gate, the planner invokes `safety-intention-checker` by inserting `template_a_si_gated.md` content into the planning prompt. The SI assessment returns a risk level (0–3) and danger score. The danger score gates whether planning proceeds.

### With `embodied-planning-safety-eval`
After SI gate passes, `embodied-planning-safety-eval` is used for deeper safety evaluation:
- **Template A** (`pddl-safety-check.md`): For plans with formalizable preconditions
- **Pre-execution safety** (`pre-execution-safety.md`): For multi-agent coordination scenarios
- **Post-incident review** (`post-incident-review.md`): After any safety-related failure

These are invoked by inserting the relevant prompt template content into the agent's reasoning loop — not via tool calls.

### Standalone Mode
If `safety-intention-checker` or `embodied-planning-safety-eval` are not available, use the prompts in `~/.hermes/skills/embodied_agent_planning/prompts/` as standalone fallbacks.

## SI Score Calibration

| SI Risk Level | Urgency Factor | Danger Score | Gate Outcome |
|---|---|---|---|
| BENIGN (0) | 0.5 | 0.17 | ✅ PASS |
| BENIGN (0) | 1.0 | 0.33 | ✅ PASS |
| BENIGN (0) | 1.5 | 0.50 | ✅ PASS |
| AMBIGUOUS (1) | 0.5 | 0.50 | ✅ PASS |
| AMBIGUOUS (1) | 1.0 | 0.67 | ✅ PASS |
| AMBIGUOUS (1) | 1.5 | 1.00 | 🚨 BLOCKED |
| CONCERNING (2) | 0.5 | 0.83 | 🚨 BLOCKED |
| CONCERNING (2) | 1.0 | 1.00 | 🚨 BLOCKED |
| CONCERNING (2) | 1.5 | 1.00 | 🚨 BLOCKED |
| BLOCKED (3) | any | 1.00 | 🚨 BLOCKED |

**Recalibration trigger**: If >20% of AMBIGUOUS plans subsequently require rejection, raise the AMBIGUOUS upper bound from 0.69 to a lower value.

## Pitfalls

1. **Bypassing the SI gate**: Never proceed to planning if SI danger score ≥ 0.7. The gate exists to prevent investing planning effort in requests that should not proceed.

2. **Treating feasibility and safety as the same check**: A plan can be feasible but unsafe (e.g., it works but causes damage) or safe but infeasible (correct approach but impossible with available tools). Both checks are necessary and independent.

3. **Ignoring SI uncertainty**: The SI check may return AMBIGUOUS with a low danger score, allowing planning to proceed. This is acceptable only if clarification is pursued in parallel — do not treat it as a clean bill of health.

4. **Setting threshold too low (false negatives)**: A threshold of 0.7 means ~70% of concerning requests are blocked. If dangerous plans are slipping through, lower the threshold to 0.6.

5. **Setting threshold too high (false positives)**: If legitimate requests are frequently rejected, examine whether the SI scoring is calibrated correctly before raising the threshold.

6. **Planning without re-checking after modification**: If a plan fails either orthogonal check and is revised, re-run BOTH checks on the new plan. A revision that fixes feasibility may introduce safety issues, and vice versa.

7. **Failing to log SI scores**: Every SI check should be logged with the full context (request, user, session, score, action taken). These logs enable calibration of the threshold and scoring model over time.

## Verification

1. **SI gate correctness**: For requests spanning all four SI risk levels, verify the correct action is taken at the gate. Known BENIGN requests should always pass; known BLOCKED requests should always fail.

2. **Orthogonal check independence**: Create scenarios where a plan is:
   - Feasible but unsafe → should fail at safety check
   - Safe but infeasible → should fail at feasibility check
   Confirm the correct failure reason is reported.

3. **Threshold sensitivity**: Test plans with SI danger scores near 0.7 (0.65, 0.69, 0.71, 0.75) to confirm the threshold is applied consistently without drift.

4. **End-to-end trace**: For a sample of 10 requests (mix of risk levels), trace through both phases and verify:
   - SI gate is applied before planning
   - Plan synthesis checks are applied after plan generation
   - Final determination matches expected outcome

5. **Revision loop verification**: Take plans that fail plan synthesis checks, apply revisions per Template B, and confirm they re-pass both checks when the revision is genuinely corrective.
