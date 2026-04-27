---
name: fantasia-aware-agent
description: Fantasia-aware agent routing to prevent premature commitment to underspecified user intent. Based on paper 2604.21827 (Jo, De Simone, Gordon, Wilson — MIT, April 2026).
version: 1.0.0
category: routing
tags:
  - intent-resolution
  - ambiguity-detection
  - fantasia
  - agent-routing
  - user-alignment
config:
  fantasia_routing:
    enabled: false
    default_mode: generate
    elicit_threshold: 0.5
    expand_options: 3
---

# Fantasia-Aware Agent Routing

## 1. Overview

### What Is the Fantasia Problem?

The Fantasia problem (Jo, De Simone, Gordon, Wilson, MIT, April 2026 — paper 2604.21827) describes a failure mode in which an AI system **commits prematurely to an underspecified user intent** and then faithfully executes a request that does not actually match what the user needed.

In the Fantasia interaction pattern, the AI behaves correctly by its own metrics — it receives a prompt, interprets it reasonably, and produces a coherent response — yet the interaction as a whole fails because the original prompt was ambiguous and the AI chose one interpretation without confirming it.

### Failure Modes

| Mode | Description |
|------|-------------|
| **Premature Execution** | The AI acts on the first plausible interpretation before the user's intent is sufficiently established. |
| **False Satisfaction** | The interaction feels successful in the moment (AI produces output, user receives something), but the output does not serve the user's actual goal. |
| **Anchoring** | Early AI outputs disproportionately shape the user's downstream thinking, steering them toward the AI's initial interpretation rather than toward what they originally needed. |

### Four AI-Side Interventions

To address Fantasia, the AI must route each incoming request through one of four intervention modes:

1. **Expand** — Surface multiple valid interpretations and let the user choose.
2. **Elicit** — Ask targeted questions to gather missing specificity.
3. **Support Intent Formation** — Help the user articulate an unclear goal through guided dialogue.
4. **Generate** — Proceed with full generation when intent is clear and specificity is sufficient.

---

## 2. The Four Routing Modes

### Expand

**When to use:** The request is vague but multiple valid interpretations exist with roughly equal prior probability. The user may not be aware that alternatives exist.

**Trigger condition:** Ambiguity score > 0.3 AND multiple coherent interpretations detected.

**Implementation prompt fragment:**

```
I can help with this in a few ways:

  A. [First interpretation — brief description]
  B. [Second interpretation — brief description]
  C. [Third interpretation — brief description]

Which approach interests you, or would you like me to clarify something first?
```

**Routing logic:**
```
if ambiguity_score > 0.3 and len(valid_interpretations) >= 2:
    return "expand"
```

---

### Elicit

**When to use:** The request lacks specificity — missing parameters, undefined constraints, or scope that is too broad. The ambiguity score exceeds the `elicit_threshold`.

**Trigger condition:** Ambiguity score > `fantasia_routing.elicit_threshold` (default 0.5).

**Implementation prompt fragment:**

```
To give you the best answer, I need a bit more detail:

[specific question targeting the highest-weight ambiguity]

For example: [concrete example to illustrate what kind of answer is helpful]
```

**Routing logic:**
```
if ambiguity_score > fantasia_routing.elicit_threshold:
    return "elicit"
```

**Important:** Do not re-elicit information already provided in the conversation history. Track what has been elicited; move to Generate or Support once ambiguity falls below threshold.

---

### Support Intent Formation

**When to use:** The user appears to be exploring, iterating, or struggling to articulate a goal. Their request may be a rough first pass rather than a considered specification.

**Trigger condition:** The user has sent multiple related prompts with evolving scope, or their prompt contains exploratory language ("I guess maybe", "something like", "I'm not sure").

**Implementation prompt fragment:**

```
It sounds like you're trying to [restate understanding of the user's goal].

Before I proceed, can you tell me more about:
  - [aspect the user seems unclear about]
  - [constraint the user has not mentioned]

This will help me give you something actually useful rather than guessing.
```

**Routing logic:**
```
if is_exploratory_language(prompt) or intent_evolution_detected():
    return "support"
```

---

### Generate

**When to use:** Intent is clear and specificity is sufficient. The ambiguity score is below threshold and no key dimensions are undefined. This is the **default mode**.

**Trigger condition:** Ambiguity score ≤ `fantasia_routing.elicit_threshold` AND all critical parameters specified.

**Implementation prompt fragment:**

```
[Proceed directly with generation. No Fantasia routing intervention needed.]
```

**Routing logic:**
```
if ambiguity_score <= fantasia_routing.elicit_threshold and critical_params_defined:
    return "generate"
```

**Do NOT use Generate when:**
- Ambiguity score is high
- The request contains open-ended scope without bounds
- Critical parameters are missing or undefined
- The user has indicated they are still forming their intent

---

## 3. Ambiguity Scoring

### What Makes a Request Ambiguous?

A request is underspecified when it exhibits one or more of the following:

| Indicator | Example |
|-----------|---------|
| **Missing subject** | "Can you fix it?" (what is "it"?) |
| **Undefined constraints** | "Make it faster" (faster than what? by how much?) |
| **Open-ended scope** | "Help me with my code" (how much code? which file? what problem?) |
| **Vague goal** | "Make it look better" (better by what metric?) |
| **Underspecified scale** | "Write a summary" (summary of what length? for what audience?) |

### Simple Heuristic Scoring

Compute ambiguity score as a normalized value in [0, 1]:

```
def compute_ambiguity_score(prompt, context=None):
    score = 0.0
    weight = 0.0

    # Missing subject: "fix it", "do that", pronoun without antecedent
    if has_missing_subject(prompt):
        score += 0.4
    weight += 1

    # Undefined constraints: comparative without baseline
    if has_undefined_constraints(prompt):
        score += 0.3
    weight += 1

    # Open-ended scope: "help me with X" without bounds
    if has_open_ended_scope(prompt):
        score += 0.5
    weight += 1

    # Vague goal: subjective adjective without objective criterion
    if has_vague_goal(prompt):
        score += 0.3
    weight += 1

    # Underspecified scale
    if has_underspecified_scale(prompt):
        score += 0.2
    weight += 1

    # Positive evidence of specificity reduces score
    if has_concrete_examples(prompt):
        score -= 0.15
    if has_defined_parameters(prompt):
        score -= 0.2

    return max(0.0, min(1.0, score / max(weight, 1)))
```

### Threshold

```
elicit_threshold = 0.5  # configurable via fantasia_routing.elicit_threshold
```

- Score > 0.5: Elicit or Expand recommended
- Score 0.3–0.5: Consider Expand if multiple interpretations exist
- Score < 0.3: Typically safe to Generate

### Intent Evolution Over Session

**Do not treat each prompt independently.** Ambiguity scoring must be informed by session-level context:

- Track the evolving user goal across turns
- A request that seems ambiguous in isolation may be well-specified given conversation history
- Maintain a `specificity_level` estimate that can only increase (not decrease) unless the user introduces a genuinely new topic

---

## 4. User Intent Tracking

### Memory Schema

Store the following state per session (e.g., in the memory skill):

```json
{
  "user_goal": "string — high-level description of what the user is trying to accomplish",
  "specificity_level": "float — 0.0 to 1.0, increases as intent becomes clearer",
  "clarification_history": [
    {
      "elicited_dimension": "what aspect was asked about",
      "user_response": "concise summary of answer",
      "turn": "integer — conversation turn number"
    }
  ],
  "defined_parameters": ["list of parameters the user has specified"],
  "undefined_critical_params": ["parameters still missing"],
  "active_interpretations": [
    {
      "interpretation": "string — description of one possible reading",
      "prior_probability": "float — estimated likelihood 0–1"
    }
  ],
  "last_mode": "expand|elicit|support|generate"
}
```

### Clarification History Rules

1. **Never re-ask the same clarification.** Before eliciting, check `clarification_history` to see if the dimension was already addressed.
2. **If a critical parameter was never answered**, you may re-elicit with different framing after two or more turns.
3. **Track what was actually answered**, not just what was asked. A user saying "I don't know" is itself informative and should be recorded.

### Long-Context Intent Evolution

The most recent prompt is not the full story. Consider:

- Is the user refining a previous request (intent evolved)?
- Is the user pivoting to a new goal (reset specificity tracking)?
- Has the conversation moved through multiple Expand/Elicit cycles without resolution?

If the user pivots, reset `specificity_level` and `clarification_history`. If they are iterating, preserve history and continue building specificity.

---

## 5. Configuration

```yaml
fantasia_routing:
  enabled: false  # default off — opt-in per agent or per conversation
  default_mode: generate  # what to do when intent is clear
  elicit_threshold: 0.5   # ambiguity score threshold for Elicit/Expand
  expand_options: 3        # max number of alternatives to present in Expand mode
```

### Enabling Fantasia Routing

Set `fantasia_routing.enabled: true` in the agent's configuration, or enable per-conversation via a system prompt directive:

```
You are operating in Fantasia-aware mode. Before acting on any request,
assess whether the user's intent is sufficiently specified. Use Expand,
// Elicit, or Support Intent Formation when ambiguity is detected.
```

---

## 6. Interaction with Other Skills

### Works With: Memory Skill

The memory skill provides persistent storage for the intent tracking schema described in Section 4. On each turn:

1. **Read** current intent state from memory
2. **Update** specificity level and clarification history
3. **Write** updated state back to memory

Without memory integration, Fantasia routing cannot track intent evolution across turns and will treat each prompt independently — undermining the core purpose of the system.

### Works With: Persona-Adversarial-Reviewer

The adversarial-reviewer skill can be used to check AI outputs for Fantasia attack patterns (see Section 7). Feed the AI's proposed response into the reviewer before sending it to the user. If the reviewer flags a Fantasia attack, reroute to Elicit or Support instead of Generate.

### Does NOT Apply To

Fantasia routing is **not needed** for:

- Well-specified technical requests with explicit requirements ("Write a Python function that takes X and returns Y using algorithm Z")
- Code generation with clear, complete specifications
- Requests that explicitly state "just do X" where X is unambiguous
- Domain expert requests where the user is already aware of alternatives and has chosen

In these cases, the ambiguity score will be near zero and Generate mode will activate automatically.

---

## 7. Fantasia Attack Patterns (for Adversarial Review)

These patterns describe ways an AI can accidentally exploit or mishandle underspecified user intent. The adversarial reviewer should flag any response that exhibits one or more of these patterns.

### Premature Commitment

The AI locks onto the first plausible interpretation of an underspecified request and treats it as established fact without confirmation.

**Example:** User says "make the chart look better" → AI immediately redesigns the chart in one specific style without asking which aspects need improvement.

**Detection:** Check if ambiguity score > threshold AND the response commits to a specific interpretation without first confirming.

### Anchoring

Early AI outputs disproportionately shape the user's downstream thinking. After receiving an initial response, the user's subsequent requests become anchored to that response rather than to their original intent.

**Example:** User asks for "a summary of the document." AI provides a 200-word summary. User's next request is "make it shorter" — now anchored to the 200-word interpretation rather than reconsidering what length would actually be appropriate.

**Detection:** If a follow-up request references or modifies a previous AI output, check whether the original request was underspecified. Flag if the user appears to be negotiating with the AI's framing rather than pursuing their own goal.

### False Satisfaction

The interaction feels productive — the AI produces output, the user receives something — but the output does not actually serve the user's underlying goal. The user may leave the conversation satisfied in the moment but later realize the output was wrong or unhelpful.

**Example:** User asks "how do I set up the server?" AI gives a standard Nginx setup guide. The user follows it but it conflicts with their existing infrastructure. Both parties were satisfied during the conversation; the problem only surfaces later.

**Detection:** Check whether the AI's response addresses a well-characterized goal or a guessed interpretation. False satisfaction is likely when the response would need to change significantly based on one missing piece of context.

### Present Bias Exploitation

The AI optimizes for what the user seems to want right now, without considering whether the user's stated request reflects their long-term interests. This is especially dangerous when the user is in an exploratory or uncertain state.

**Example:** User says "just give me the quick version." AI provides a stripped-down answer that the user requested, but which omits critical caveats the user would have wanted had they been thinking more carefully.

**Detection:** Flag responses that fulfill a hedged or uncertain request without noting the tradeoffs being made. The AI should at minimum acknowledge what is being omitted.

---

## 8. Verification

### Test Cases

#### Test 1: Ambiguous Request — Should NOT Generate

**Input:**
```
"help me set up my computer"
```

**Expected behavior:**
- Ambiguity score > 0.5 → Elicit or Expand
- AI should ask: "What kind of computer? What operating system? What do you need it to do?"
- NOT: immediately start giving hardware setup instructions

**Failure mode:** AI starts listing computer specs or OS installation steps without first determining the user's actual goal.

---

#### Test 2: Well-Specified Request — Should Generate

**Input:**
```
"write a Python function that takes a list of integers and returns the median value"
```

**Expected behavior:**
- Ambiguity score < 0.2 → Generate immediately
- No Elicit or Expand needed
- AI produces a correct, well-commented Python function

**Failure mode:** AI asks clarifying questions about the median calculation (already unambiguous) or offers multiple implementation approaches unprompted.

---

#### Test 3: No Repeated Clarifications

**Conversation:**
```
User: "help me with my code"
AI: (Elicit) "Which file or project are you referring to?"
User: "the Python script in my project"
AI: (Elicit) "Which Python script specifically?"
```

**Expected behavior at turn 3:**
- The AI should NOT ask again which language (already established as Python)
- Should ask for the missing dimension: which specific script or file

**Failure mode:** AI re-asks the same question about language/script after user already answered, indicating failure to track clarification history.

---

#### Test 4: Exploratory User — Support Intent Formation

**Input:**
```
"hmm I'm not really sure, I guess maybe something like an app that tracks expenses"
```

**Expected behavior:**
- Detected as exploratory language ("not really sure", "I guess", "maybe")
- Route to Support Intent Formation
- AI responds with something like: "It sounds like you want to build an expense tracking app. Before we dive in, can you tell me: is this for personal use, or for a team? What platform? Any must-have features?"

**Failure mode:** AI treats this as a fully specified request and immediately starts building a production-grade expense tracker.

---

## Appendix: Routing Decision Tree

```
START
  │
  ▼
Is fantasia_routing.enabled? ──No──► Generate (default)
  │
  Yes
  ▼
Compute ambiguity_score(prompt, context)
  │
  ├─ score > 0.5 ───────────────────► Elicit
  │
  ├─ score > 0.3 AND multi_interp? ─► Expand
  │
  ├─ is_exploratory(prompt)? ───────► Support Intent Formation
  │
  └─ score <= 0.3 AND params_defined ► Generate
```

---

*Based on "Fantasia: Premature Commitment and the Ambiguity Problem in LLM-Agent Interactions" — Jo, De Simone, Gordon, Wilson (MIT, April 2026). Paper 2604.21827.*
