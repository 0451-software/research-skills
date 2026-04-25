---
name: Metacognitive Monitor
description: "Cognitive bias detection and self-audit prompt. Use proactively at intervals or when an agent notices patterns in its own responses that might indicate systematic errors."
---

## Cognitive Bias Scan

Review your recent reasoning for these common agent biases:

**BIAS CHECKLIST:**
- [ ] **Confirmation bias**: Have you been overweighting evidence that supports your initial hypothesis and underweighting contradicting evidence?
- [ ] **Anchoring**: Did you fixate on an early piece of information and fail to update adequately?
- [ ] **Sunk cost**: Are you continuing down a path because of prior investment rather than current merit?
- [ ] **Availability heuristic**: Are you judging outcomes by how easily examples come to mind rather than actual frequency or probability?
- [ ] **Hindsight bias**: Are you overconfident in retrospect, claiming the outcome was predictable?
- [ ] **Framing effects**: Would you give different advice if the same information were presented with different phrasing?

**Output Format:**

```
BIAS_DETECTED: <true/false>

BIASES_FOUND:
  - BIAS: <name>
    EVIDENCE: <specific instance in your reasoning>
    REMEDIATION: <how to correct this bias in future reasoning>

REASONING_CHANGES: <list of specific changes to make based on detected biases>

BIAS_LOG: <for pattern detection across sessions - summary of findings>
```

**Instructions:**
- Be specific and cite actual reasoning instances
- Remediation must be concrete, actionable changes
- Log outcomes for cross-session pattern detection
- This prompt should change behavior — if no changes result, the scan was wasted
