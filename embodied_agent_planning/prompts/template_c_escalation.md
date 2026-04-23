# Human Escalation Brief

You are preparing an escalation brief for human review. A plan has triggered mandatory escalation due to safety concerns that require human judgment.

---

## What Triggered Escalation

Escalation is required when one or more of the following conditions are met:

```
ESCALATION_TRIGGER: <SI_RISK_LEVEL_3 | IRREVERSIBLE_ACTION | NORMATIVE_DANGER | MULTIPLE_SAFETY_DIMENSIONS>
SI_DANGER_SCORE: {score}
SI_RISK_LEVEL: {risk_level}
FEASIBILITY_STATUS: {status}
SAFETY_STATUS: {status}
OVERALL_RISK: {risk}
```

### Escalation Triggers Explained

| Trigger | Meaning |
|---------|---------|
| SI_RISK_LEVEL_3 | The Safety Intention check returned BLOCKED (3) — the request has been refused at the SI gate |
| IRREVERSIBLE_ACTION | The plan contains at least one step with irreversible consequences that cannot be undone |
| NORMATIVE_DANGER | The plan involves normative uncertainty — actions that could be harmful regardless of intent |
| MULTIPLE_SAFETY_DIMENSIONS | Three or more safety dimensions are rated at risk level 2 or above |

---

## Information to Present

Prepare a structured brief with the following sections:

### 1. Plan Summary

```
ORIGINAL_OBJECTIVE: <what the user was trying to accomplish>
AGENT_TYPE: <robot|vehicle|drone|game_agent|simulated_avatar|humanoid|other>
ENVIRONMENT: <physical|simulated|mixed>

PLAN_STEPS:
1. <step 1>
2. <step 2>
...
N. <step N>
```

### 2. SI Findings

```
SI_DANGER_SCORE: {score} (threshold: 0.7)
SI_RISK_LEVEL: <BENIGN|AMBIGUOUS|CONCERNING|BLOCKED>
APPARENT_INTENT: <what the request appeared to be asking for>
ALTERNATIVE_INTERPRETATIONS: <what else it could mean>
CONTEXT_SIGNALS: <urgency, history, phrasing that informed the assessment>
CLARIFICATION_PROVIDED: <if any, what clarification was attempted>
```

### 3. Feasibility Concerns

```
FEASIBILITY_STATUS: <FEASIBLE|INFEASIBLE|UNCERTAIN>
BLOCKING_ISSUES: <if infeasible, what makes execution impossible>
MISSING_CONDITIONS: <what would need to be true for this to be feasible>
```

### 4. Safety Evaluation Findings

```
OVERALL_RISK: <0-3>
SAFETY_STATUS: <SAFE|CAUTION|HALT_AND_REVISIT|BLOCK>

DIMENSION_SCORES:
- Physical Safety: <0-3>
- Environmental Safety: <0-3>
- Psychological Safety: <0-3>
- Alignment Safety: <0-3>
- Coordination Safety: <0-3>

DIMENSION_DETAIL:
<for each dimension with risk >= 1, explain the concern>
```

### 5. Irreversibility Assessment (if applicable)

```
IRREVERSIBLE_STEPS: <which steps have irreversible consequences>
IRREVERSIBILITY_TYPE: <physical|informational|environmental|social>
RECOVERY_METHOD: <how the state could be restored if needed>
RECOVERY_COST: <what is lost even with full recovery>
```

### 6. Available Alternatives

```
ALTERNATIVE_APPROACHES:
- <Option 1>: <description> — <why it was or wasn't considered>
- <Option 2>: <description> — <why it was or wasn't considered>
- <Option 3>: <description> — <why it was or wasn't considered>

RECOMMENDED_ALTERNATIVE: <if any, which option is safest while still achieving the goal>
```

### 7. Proposed Safeguards

```
SAFEGUARDS_UNDER_CONSIDERATION:
- <safeguard 1>: <what it controls> | <implementation approach>
- <safeguard 2>: <what it controls> | <implementation approach>

HUMAN_IN_LOOP_REQUIRED: <YES|NO>
OVERRIDE_AUTHORITY: <who can abort or modify the plan mid-execution>
```

---

## Human Decision Required

```
SPECIFIC_QUESTION_FOR_HUMAN: <precisely what the human must decide>
OPTIONS_AVAILABLE:
1. <Approve the plan as-is>
2. <Approve with specific modifications or safeguards>
3. <Deny the request — do not execute>
4. <Request additional information before deciding>

DO_NOT_EXECUTE_UNTIL: <human authority grants explicit approval>
```

---

## Anticipated Human Reviewer Questions

Prepare answers for these likely questions:

1. **"Why can't the system make this decision autonomously?"**
   - Because the SI gate or safety evaluation exceeded the automatic-approval threshold (danger_score ≥ 0.7 or safety risk ≥ 2)

2. **"What is the worst-case outcome if this plan executes?"**
   - <describe the most severe plausible consequence>

3. **"What would need to be different for this to be auto-approved?"**
   - <specific conditions that would lower the risk score below threshold>

4. **"Is there a safer way to accomplish the same goal?"**
   - <reference the alternative approaches section>

5. **"What happens if we deny this request?"**
   - <describe the consequence of not executing the plan>

6. **"Who is accountable for the decision?"**
   - Human reviewer: for approving a flagged request
   - System: for correctly identifying the risk and escalating

---

## Brief Format Summary

This brief is formatted for a non-technical human reviewer. Avoid jargon. Explain acronyms on first use. Prioritize clarity on:
- What the user wanted to do
- Why the system flagged it
- What could go wrong
- What options the reviewer has

Do not include: internal system architecture details, Phase terminology, or PSMAS references.
