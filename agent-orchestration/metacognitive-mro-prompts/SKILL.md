---
name: metacognitive-mro-prompts
description: "Metacognitive monitoring and regulation prompts for Hermes agents. Use when an agent needs to self-evaluate reasoning quality, catch cognitive biases, revise plans mid-execution, or recover from dead-ends. NOT a skill for end-user consumption — it is a prompt library for agent self-regulation."
---

# Metacognitive MRO Prompts

Prompts for **M**onitoring, **R**egulation, and **O**ptimization of agent cognitive processes. Inject structured self-reflection into reasoning loops without breaking task flow.

## When to Use

- Checkpoint: verify reasoning before proceeding
- Sub-agent returns unexpected/contradictory output
- Dead-end: need to backtrack
- Task taking too many iterations
- Uncertain which approach to take
- Bias detection: pattern in responses suggests systematic error
- Recovery: diagnose what went wrong

## Prompt Library

### 1. Pre-Execution: Plan Quality Check

```
## Meta-Cognitive Pre-Execution Check

Before executing your plan, run through each item:

1. **Completeness**: Have you identified all sub-tasks? List them explicitly.
2. **Dependency ordering**: Are sub-tasks in a valid topological order? Flag any circular dependencies.
3. **Failure modes**: For each sub-task, what is the most likely failure mode?
4. **Reversibility**: If a sub-task produces wrong output, can you detect it before it poisons downstream tasks?
5. **Evidence requirements**: What evidence would confirm each sub-task succeeded? What would falsify it?

PLAN_QUALITY_SCORE: <1-5, where 5 = fully specified and failure-resilient>
FLAGS: <list any concerns that need addressing before proceeding>
```

### 2. Mid-Execution: Convergence Check

```
## Mid-Execution Convergence Check

Task: {task_description}
Current step: {current_step} of {total_steps}
Time elapsed: {elapsed_time}

Evaluate:
1. **Progress**: Are you closer to the goal than when you started? What evidence do you have?
2. **Velocity**: Is the rate of progress consistent with the remaining work? If not, why?
3. **Signal quality**: Is the information you're getting back reliable? Could you be receiving stale or misleading data?
4. **Scope creep**: Has the task expanded beyond its original scope? Re-state the original scope.
5. **Dead-end risk**: Is there a concrete next step, or are you iterating without clear direction?

CONVERGENCE_STATUS: <CONVERGING | STALLING | DIVERGING>
ADJUSTMENT: <if STALLING or DIVERGING, what specific change to make>
```

### 3. Post-Execution: Root-Cause Analysis

```
## Root-Cause Analysis (RCA)

A task has failed or produced an unsatisfactory result. Conduct a structured RCA.

Task: {task_description}
Observed failure: {failure_description}
Expected outcome: {expected_outcome}

RCA Protocol:
1. **Symptom description**: State the failure precisely, without interpretation.
2. **Timeline**: List the sequence of events leading to the failure.
3. **Contributing factors**: Identify factors that enabled or amplified the failure.
   - Tool errors or ambiguity?
   - Missing information available but not requested?
   - Incorrect assumption about system state?
   - Reasoning error (wrong inference, missed case)?
   - Communication failure (user provided unclear input)?
4. **Root cause (5 Whys)**: Apply 5 Whys iteratively to isolate the deepest correctable cause.
5. **Fix**: What is the specific change that would prevent recurrence?
6. **Verification**: How would you confirm the fix works?

ROOT_CAUSE: <single sentence stating the deepest correctable cause>
FIX_SUMMARY: <one-sentence fix description>
```

### 4. Bias Detection Prompts

```
## Cognitive Bias Scan

Review your recent reasoning for these common agent biases:

BIAS CHECKLIST:
- [ ] **Confirmation bias**: Have you been overweighting evidence that supports your initial hypothesis and underweighting contradicting evidence?
- [ ] **Anchoring**: Did you fixate on an early piece of information and fail to update adequately?
- [ ] **Sunk cost**: Are you continuing down a path because of prior investment rather than current merit?
- [ ] **Availability heuristic**: Are you judging outcomes by how easily examples come to mind rather than actual frequency or probability?
- [ ] **Hindsight bias**: Are you overconfident in retrospect, claiming the outcome was predictable?
- [ ] **Framing effects**: Would you give different advice if the same information were presented with different phrasing?

For each detected bias:
BIAS: <name>
EVIDENCE: <specific instance in your reasoning>
REMEDIATION: <how to correct this bias in future reasoning>
```

### 5. Plan Revision Prompt

```
## Plan Revision

Original plan failed or is no longer viable. Revise without discarding all prior work.

Original plan: {original_plan}
Failure point: {where_it_failed}
What worked: {what_worked_before_failure}

Revise the plan addressing:
1. What assumption was wrong? How do you know?
2. What information was missing?
3. Is there a simpler path that avoids the failure mode?
4. Should you backtrack to an earlier checkpoint and try a different branch?

REVISED_PLAN: <numbered step list>
CHECKPOINT: <where to resume from in the revised plan>
CONFIDENCE: <HIGH|MEDIUM|LOW in revised plan>
```

### 6. Uncertainty Articulation Prompt

```
## Uncertainty Articulation

Before responding with high confidence, articulate what you know, what you don't know, and the gap between them.

Task: {task}

KNOW: <what you know with high confidence — facts, confirmed outputs, established relationships>
PARTIAL: <what you know partially — approximations, likely-but-unconfirmed beliefs>
DON'T KNOW: <what you have not established — unknowns that could materially affect the answer>
EPISTEMIC_GAP: <the specific gap between KNOW and what's needed to answer confidently>

For the DON'T KNOW items:
- Which are knowable with available tools/information?
- Which would require information you don't have and cannot obtain?
- What is your current confidence in each, expressed as a probability range?
```

## Usage Patterns

### Inline Injection (Recommended)
Insert prompts at natural breakpoints, not as separate turns. Example:

```
[After step 3 of 7]
<inject mid-execution convergence check>
[Based on result, continue to step 4 or revise]
```

### Sub-agent Delegation
Spawn focused sub-agent with RCA prompt when primary task fails. Set context to only failed task details — no full conversation history.

### Delegation Triggers (D1–D4)
Auto-apply on non-trivial tasks:

- **D1 (Complexity):** 3+ phases or 5+ tool calls → delegate subsequent phases to persona-agent
- **D2 (Expertise):** Research, adversarial review, verification → use `persona-researcher` / `persona-adversarial-reviewer` / `persona-inspector`
- **D3 (Parallelization):** Independent workstreams → batch delegate up to 3 sub-agents concurrently
- **D4 (Escalation):** Failure mode, high uncertainty, or blocked → delegate with full context

See `agent-delegation-strategy` for decision tree and context prep checklist.

### Scheduled Self-Audit
Every ~20 turns, inject cognitive bias scan proactively. Systemic detection catches drift before failure.

## Pitfalls

1. **Over-use fragments focus**: Reserve for genuine decision points or failures only.
2. **Decoration doesn't work**: Prompt output must change behavior. If you detect bias but proceed same way, prompt was wasted.
3. **Reflection ≠ execution**: Metacognitive prompts are for planning/evaluation, not primary output. Self-analysis must not become the deliverable.
4. **Log outcomes**: Log RCA results for pattern detection. Recurring root causes reveal systemic issues.
5. **Fill placeholders**: Bare prompt injection without `{placeholder}` fields filled produces generic output.

## Verification

1. **Convergence validation**: After use, compare CONVERGENCE_STATUS and ADJUSTMENT to actual task outcome.
2. **RCA quality**: Check whether root cause was specific/correctable, not just symptom restatement.
3. **Bias accuracy**: Run bias checklist on sample tasks. For flagged biases, verify reasoning actually changed.
4. **Regression tests**: Maintain 5 known-failure scenarios. After updates, re-run RCA and verify root causes still correct.