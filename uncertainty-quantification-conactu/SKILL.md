---
name: uncertainty-quantification-conactu
description: "Structured uncertainty quantification (UQ) for agent outputs. Use when assessing calibrated confidence, communicating epistemic limitations, or building multi-agent pipelines where downstream decisions depend on upstream reliability."
version: 1.0.0
license: MIT
---

# Uncertainty Quantification — CONACTU

**CONACTU**: **Con**fidence **A**ssessment **C**alibrated to **T**otal **U**nderstanding

A structured framework for quantifying and communicating uncertainty in agent reasoning. Use when building agentic pipelines where downstream decisions depend on the reliability of intermediate outputs.

## When to Use

- Agent is about to make a decision with significant consequences and needs to assess confidence
- An answer is being generated in a domain with known knowledge gaps
- The user asks "how sure are you?" — provide a structured answer, not a hedge
- Deciding whether to proceed with tool use, API calls, or multi-step reasoning when prior steps had ambiguous outputs
- Flagging to a downstream agent or system that an upstream output has limited reliability
- Post-execution review: "Was the confidence level justified by the evidence?"
- Calibration training: comparing predicted confidence to actual outcome accuracy over time

## CONACTU Framework

### Four Uncertainty Axes

Every knowledge claim should be evaluated on four axes:

| Axis | Label | Description |
|------|-------|-------------|
| Evidence | E1–E5 | Quality and quantity of supporting evidence |
| Model Fidelity | M1–M3 | How well the internal model matches ground truth |
| Completeness | C1–C4 | Fraction of relevant knowledge space covered |
| Stability | S1–S3 | Likelihood that the answer would change with new information |

### Confidence Level Table

| Level | Label | Meaning | Action |
|-------|-------|---------|--------|
| 5 | HIGH | Strong evidence, high model fidelity, complete coverage, stable | Proceed |
| 4 | CONFIDENT | Good evidence, minor knowledge gaps, low change probability | Proceed with awareness |
| 3 | SPECULATIVE | Limited evidence, significant gaps, moderate instability | Proceed with explicit caveats |
| 2 | UNCERTAIN | Weak evidence, major gaps, high change probability | Seek more information or defer |
| 1 | UNGROUNDED | No evidence or fundamentally incompatible signals | Do not act on this claim |

## Prompt Templates

### Template A — Output Confidence Assessment

```
## CONACTU Confidence Assessment

Evaluate your confidence in the following output before presenting it.

OUTPUT: <the claim or answer you are about to produce>

For each axis, assign a score:

EVIDENCE (E1-E5):
- E5: Direct confirmation from reliable source, multiple independent corroborations
- E4: Strong evidence, single source, well-established domain
- E3: Moderate evidence, partial source access, some extrapolation
- E2: Weak evidence, indirect inference, speculative domain
- E1: No evidence, pure extrapolation, unknown domain

MODEL FIDELITY (M1-M3):
- M3: Model matches domain precisely, no known misalignments
- M2: Model mostly matches, minor known misalignments or edge cases
- M1: Model poorly matches reality, fundamental mismappings

COMPLETENESS (C1-C4):
- C4: Full coverage, all relevant factors accounted for
- C3: Most relevant factors covered, minor omissions
- C2: Partial coverage, significant gaps in relevant knowledge
- C1: Minimal coverage, large portions of relevant space unexplored

STABILITY (S1-S3):
- S3: Would not change with new information (well-established fact)
- S2: Might change with significant new information or edge cases
- S1: Highly likely to change with any new information

CONFIDENCE_VECTOR: E<1-5> M<1-3> C<1-4> S<1-3>
CONFIDENCE_LEVEL: <1-5> (<label>)

For levels below 4:
- CRITICAL_GAPS: <specific missing knowledge items>
- RECOMMENDED_ACTION: <proceed, defer, ask, or refuse>
- USER_FACING_CAVEAT: <plain-language statement of limitation>

OUTPUT_TO_USER: <final phrasing incorporating caveat if confidence < 4>
```

### Template B — Pre-Tool-Use Uncertainty Check

```
## Pre-Tool-Use Uncertainty Check

Before executing {tool_name} with arguments {tool_args}, assess whether
the current knowledge state justifies the action.

TOOL: {tool_name}
ARGS: {tool_args}
INTENDED_OUTCOME: {what_success_looks_like}
FAILURE_COST: {what happens if this goes wrong}

UNCERTAINTY_ASSESSMENT:
- What do you know for certain about the current state?
- What are you assuming without direct evidence?
- What is the most likely failure mode given your uncertainty?
- Is the failure cost acceptable relative to the expected value of success?

If confidence < 3 on the INTENDED_OUTCOME:
- Can you obtain the missing information with available tools before acting?
- What is the minimum information needed to raise confidence to 3?

DECISION: PROCEED | GATHER_INFO | DEFER | REFUSE
RATIONALE: <brief justification>
```

### Template C — Multi-Step Pipeline Confidence Propagation

```
## Pipeline Confidence Audit

Review the following multi-step pipeline and propagate uncertainty from inputs to outputs.

PIPELINE STEPS:
{step_1}: input → {step_1_output} [CONFIDENCE: {c1}]
{step_2}: {step_1_output} → {step_2_output} [CONFIDENCE: {c2}]
{step_3}: {step_2_output} → {step_3_output} [CONFIDENCE: {c3}]
...

COMBINATION_RULE: Confidence in a composed output is the minimum confidence
across all steps, unless intermediate steps provide amplification through
independent evidence.

PIPELINE_CONFIDENCE: <minimum across steps, or explain if amplification applies>

WEAKEST_LINK: <which step has the lowest confidence and why>
UPSTREAM_RECOVERY: <what information would raise the weakest link's confidence>
DOWNSTREAM_IMPACT: <how does the weakest link's uncertainty affect the final output>
IS_OUTPUT_USABLE: <YES if final confidence >= 3, NO otherwise>
```

### Template D — Post-Outcome Calibration Review

```
## Post-Outcome Calibration Review

Compare predicted confidence to actual outcome to improve future calibration.

PREDICTED_CONFIDENCE: {level} ({vector})
ACTUAL_OUTCOME: {correct|partially_correct|incorrect}
DEVIATION: {direction and magnitude of miscalibration}

Analysis:
1. Was the confidence level appropriate given the evidence available at prediction time?
2. Was the evidence quality assessment accurate?
3. Were there knowledge gaps that were not identified?
4. Was the model fidelity assessment correct?
5. Was the stability assessment correct?

CALIBRATION_ERROR: <overconfident | appropriately_confident | underconfident>
CORRECTIVE_NOTE: <what to watch for in similar future cases>
```

## Usage Patterns

### High-Stakes Decision Protocol
1. Run Template A on the proposed output before any user-facing communication
2. If confidence < 4, run Template B to check whether additional information gathering is warranted
3. Present output with calibrated caveat (do not suppress, but do not over-qualify either)
4. Log the confidence assessment for later calibration review

### Multi-Agent Pipeline Integration
- Each agent in a pipeline should attach a CONACTU confidence vector to its output
- Downstream agents read the confidence vector and apply Template C to assess composite confidence
- If composite confidence drops below threshold, pipeline halts and routes to a clarification path

### User-Facing Communication Rules
- Confidence level 5–4: No caveat needed; the answer is reliable
- Confidence level 3: "I'm fairly confident, but [specific caveat]"
- Confidence level 2: "I'm uncertain; [specific gap]. My best estimate is [X], but this may change."
- Confidence level 1: Do not present as an answer; state that you lack sufficient knowledge

## Pitfalls

1. **Treating uncertainty as weakness**: Expressing uncertainty accurately is a feature, not a flaw. Over-confident wrong answers are more harmful than calibrated uncertainty.

2. **Conflating uncertainty with ignorance**: A level 3 can still be a good basis for action; level 3 means "speculative with significant caveats," not "don't use this."

3. **Failing to propagate**: In multi-step pipelines, a single uncertain step poisons downstream outputs. Always propagate confidence vectors explicitly.

4. **Generic hedging**: "I might be wrong" is not a CONACTU response. State the specific gap, the specific axis, and the implied risk.

5. **Static calibration**: Confidence levels should evolve as evidence evolves. Do not lock in an initial confidence estimate and then ignore new information.

6. **Over-qualifying low-stakes answers**: If the task is "what's the weather in Tokyo?", a level 3 is fine. Do not apply high-stakes rigor to low-consequence queries.

## Verification

1. **Calibration accuracy**: Track predicted confidence vs. actual outcome over at least 20 cases per confidence level. Ideal calibration: 90% of predictions at confidence 4 should be correct or partially correct.

2. **Cross-axis consistency**: For a given output, verify that the four axes are internally consistent (e.g., E5 without M3 is suspicious — if evidence is strong, why is model fidelity low?).

3. **Propagation test**: Create a synthetic 3-step pipeline with known confidence levels at each step. Verify that the propagated confidence matches the minimum rule.

4. **User comprehension check**: After presenting a confidence-3 output with a caveat, verify the user understood the limitation by asking a targeted follow-up question.

5. **Escalation audit**: Periodically review cases where confidence < 3 and the agent proceeded anyway. Determine whether the decision to proceed was justified in retrospect.
