---
name: Metacognitive Reasoner
description: "Plan revision and reasoning refinement prompt. Use when an original plan has failed or is no longer viable and needs structured revision without discarding prior work."
---

## Plan Revision

Original plan failed or is no longer viable. Revise without discarding all prior work.

**Original plan:** {original_plan}
**Failure point:** {where_it_failed}
**What worked:** {what_worked_before_failure}

Revise the plan addressing:
1. What assumption was wrong? How do you know?
2. What information was missing?
3. Is there a simpler path that avoids the failure mode?
4. Should you backtrack to an earlier checkpoint and try a different branch?

**Output Format:**

```
REVISED_PLAN: <numbered step list>

CHECKPOINT: <where to resume from in the revised plan>

ASSUMPTION_REVISION: <which assumption was wrong and what evidence contradicts it>

MISSING_INFO: <what information was unavailable or not requested>

SIMPLER_PATH: <yes/no and explanation if a more direct route exists>

BACKTRACK_DECISION: <yes/no and which checkpoint if applicable>

CONFIDENCE: <HIGH|MEDIUM|LOW in revised plan>
```

**Instructions:**
- Be specific about what failed and why
- Preserve working elements from the original plan where possible
- Identify concrete next steps, not abstract goals
- Set a clear checkpoint for resuming execution
