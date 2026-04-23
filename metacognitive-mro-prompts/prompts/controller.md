---
name: Metacognitive Controller
description: "Uncertainty articulation and decision control prompt. Use before responding with high confidence or when uncertain which of several approaches to take."
---

## Uncertainty Articulation

Before responding with high confidence, articulate what you know, what you don't know, and the gap between them.

**Task:** {task}

**Output Format:**

```
KNOW: <what you know with high confidence — facts, confirmed outputs, established relationships>

PARTIAL: <what you know partially — approximations, likely-but-unconfirmed beliefs>

DON'T KNOW: <what you have not established — unknowns that could materially affect the answer>

EPISTEMIC_GAP: <the specific gap between KNOW and what's needed to answer confidently>

GAP_ANALYSIS:
  - KNOWABLE: <which DON'T KNOW items are knowable with available tools/information>
  - UNKNOWABLE: <which items would require information you don't have and cannot obtain>
  - CONFIDENCE_RANGES: <probability ranges for each KNOW and PARTIAL item>

DECISION_READY: <yes/no - whether you have sufficient confidence to proceed>

ALTERNATIVES: <if not decision-ready, what additional information or approaches could reduce uncertainty>
```

**Instructions:**
- Distinguish clearly between confirmed knowledge, approximations, and genuine unknowns
- For each DON'T KNOW item, assess whether it is knowable or fundamentally unavailable
- Express confidence as probability ranges where possible
- Only proceed with a decision if confidence is sufficient for the stakes
