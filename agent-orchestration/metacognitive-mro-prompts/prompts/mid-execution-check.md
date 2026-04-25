---
name: Mid-Execution Check
description: "Convergence verification during task execution. Use when a task is taking more iterations than expected or when the agent is uncertain about progress."
---

## Mid-Execution Convergence Check

**Task:** {task_description}
**Current step:** {current_step} of {total_steps}
**Time elapsed:** {elapsed_time}

Evaluate:

1. **Progress**: Are you closer to the goal than when you started? What evidence do you have?
2. **Velocity**: Is the rate of progress consistent with the remaining work? If not, why?
3. **Signal quality**: Is the information you're getting back reliable? Could you be receiving stale or misleading data?
4. **Scope creep**: Has the task expanded beyond its original scope? Re-state the original scope.
5. **Dead-end risk**: Is there a concrete next step, or are you iterating without clear direction?

**Output Format:**

```
PROGRESS_ASSESSMENT:
  CLOSER_TO_GOAL: <yes/no/partially>
  EVIDENCE: <specific evidence of progress or lack thereof>

VELOCITY:
  RATE: <fast/stable/slow>
  CONSISTENT_WITH_REMAINING: <yes/no>
  IF_NO_EXPLANATION: <why velocity doesn't match remaining work>

SIGNAL_QUALITY:
  RELIABLE: <yes/no/uncertain>
  STALE_OR_MISLEADING_RISK: <none/low/medium/high>
  MITIGATION: <if risk exists, how to address>

SCOPE_STATUS:
  ORIGINAL_SCOPE: <re-stated original scope>
  EXPANDED: <yes/no>
  IF_YES_NATURE: <what expanded beyond original>

DEAD_END_RISK:
  RISK_LEVEL: <none/low/medium/high>
  NEXT_STEP_CONCRETE: <yes/no>
  IF_NO_PATH: <what concrete next step to take>

CONVERGENCE_STATUS: <CONVERGING | STALLING | DIVERGING>

ADJUSTMENT: <if STALLING or DIVERGING, what specific change to make>

REVISED_PLAN_IF_NEEDED: <updated plan or sub-task list if status is STALLING or DIVERGING>
```

**Instructions:**
- CONVERGENCE_STATUS must be one of the three exact values
- STALLING means progress has stopped but task is still viable
- DIVERGING means the task is moving away from the goal
- If STALLING or DIVERGING, ADJUSTMENT must specify concrete behavioral changes
