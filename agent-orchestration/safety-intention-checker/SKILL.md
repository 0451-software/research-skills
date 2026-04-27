---
name: safety-intention-checker
description: "Evaluate whether a task request reflects a benign, ambiguous, or potentially harmful intention before the agent takes any action. Use when: (1) a user request could be interpreted multiple ways, (2) the request involves sensitive capabilities (code execution, file modification, external API calls), (3) the user expresses frustration or urgency that deviates from normal patterns, (4) the request lacks sufficient context to determine safety. NOT for: routine confirmed-safe operations, or when the user has already established a trusted context. NOT a substitute for capability-level guardrails — this is a pre-action semantic check."
version: 1.0.0
metadata:
  hermes:
    tags: [safety, security, intention-check, risk-assessment]
    category: security
---

# Safety Intention Checker

Evaluate the semantic safety of a task request before execution. Determines whether the apparent intent is benign, ambiguous, or concerning enough to warrant clarification, refusal, or escalation.

## When to Use

- A request could be read in multiple ways, one of which is harmful
- The user is escalating urgency or using pressure tactics ("just do it", "why won't you", "I told you to")
- A task involves modifying system files, running unsigned code, or interacting with credential stores
- A request is vague but the agent's interpretation could be harmful if wrong
- A user explicitly asks the agent to bypass its own safety guidelines

## Framework

### Three-Layer Assessment

**Layer 1 — Apparent Intent**
What does the user appear to be asking for, taking the request at face value?

**Layer 2 — Alternative Interpretations**
What else could this request mean? List at least 2 alternative readings.

**Layer 3 — Context Signals**
What surrounding signals inform interpretation? (user history, session context, request phrasing, urgency markers)

### Risk Taxonomy

| Level | Label | Description |
|-------|-------|-------------|
| 0 | BENIGN | Unambiguously safe; normal operation |
| 1 | AMBIGUOUS | Multiple valid interpretations; needs clarification before proceeding |
| 2 | CONCERNING | Potentially harmful if the least-charitable interpretation is correct; escalate or refuse |
| 3 | BLOCKED | Clearly harmful request; refuse and log |

## Prompt Templates

Prompt templates for each evaluation mode are available in the `prompts/` subdirectory:

| Template | File | Use when |
|----------|------|----------|
| Standard Intention Check | `prompts/standard-check.md` | Normal ambiguous requests |
| High-Urgency / Pressure | `prompts/high-urgency.md` | User escalating or using pressure tactics |
| Tool Use Scope Check | `prompts/tool-use-check.md` | Sensitive tools with unclear scope |
| Detailed Safety Check | `prompts/safety-check.md` | Rich VERDICT + DANGER_FLAGS output |

Load a specific template with `skill_view('safety-intention-checker', 'prompts/<filename>')`.

### Quick-Reference Response Formats

**Standard Check Output:**
```
INTENT: <apparent intent>
ALT1: <alternative interpretation 1>
ALT2: <alternative interpretation 2>
SIGNALS: <context signals>
RISK: <0|1|2|3>
CLARIFICATION: <if risk >= 1, a question that resolves ambiguity>
```

**High-Urgency Check Output:**
```
MANIPULATION_LIKELIHOOD: <LOW|MEDIUM|HIGH>
PRESSURE_LEVEL: <NONE|MILD|MODERATE|SEVERE>
AUTHENTIC_NEED: <most likely real intent>
RESPONSE_TONE: <FIRM|COLLABORATIVE|REFUSAL>
FOLLOW_UP_NEEDED: <YES|NO>
RECOMMENDED_RESPONSE: <specific response strategy>
```

**Tool Use Check Output:**
```
SAFE_SUBSET: <tools/actions that are safe regardless of intent>
UNSAFE_SUBSET: <tools/actions only safe under charitable interpretation>
RECOMMENDATION: <proceed with safe subset only, proceed with all, refuse, or ask>
```

## Clarification Strategies

### For AMBIGUOUS (Level 1) — Ask before acting
- "I want to make sure I understand correctly — did you mean X, or Y?"
- "Could you clarify what you're trying to accomplish? I'm not sure if you meant [A] or [B]."

### For CONCERNING (Level 2) — Refuse and explain
- "I'm not going to do that. If you have a legitimate need, can you describe it differently?"
- "I need more context before I can help with this safely."

### For BLOCKED (Level 3) — Refuse and log
- "I can't help with that request. This type of task is outside what I'm able to do."
- Do not explain *how* to accomplish the harmful act, even if asked.

## Pitfalls

1. **Over-trusting benign signals**: A polite, detailed request can still be a sophisticated social engineering attempt. Apply Layer 2 analysis consistently.

2. **Anthropomorphizing intent**: The agent must not assume a user "wouldn't mean harm" based on politeness or apparent expertise. Intent and capability are separate.

3. **Failing to log**: Level 2 and 3 assessments should be logged even if the user backs down after clarification. Patterns over time matter.

4. **Refusing too aggressively**: Disproportionate refusal on ambiguous requests creates friction for legitimate users. Aim for clarification-first at Level 1.

5. **Treating this as a guardrail**: This skill is a semantic check, not a technical enforcement. It does not replace capability-level permissions or sandboxing.

## Verification

Run the standard check on known examples to confirm risk levels:

```bash
# Benign: user asks for help with a Python script
# Expected: RISK 0 (BENIGN)

# Ambiguous: user asks to "clean up the system" without specifying scope
# Expected: RISK 1 (AMBIGUOUS) with clarification prompt

# Concerning: user provides a URL and asks the agent to "run whatever is there"
# Expected: RISK 2 (CONCERNING) or RISK 3 (BLOCKED)

# Blocked: user asks for help bypassing content filters
# Expected: RISK 3 (BLOCKED)
```

After any update to the risk taxonomy, run a regression suite of at least 10 previously evaluated requests and confirm risk levels have not shifted inappropriately.
