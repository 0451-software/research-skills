---
name: Pre-Execution Check
description: "Plan quality verification before execution. Use when an agent reaches a checkpoint and needs to verify its reasoning before proceeding."
---

## Meta-Cognitive Pre-Execution Check

Before executing your plan, run through each item:

1. **Completeness**: Have you identified all sub-tasks? List them explicitly.
2. **Dependency ordering**: Are sub-tasks in a valid topological order? Flag any circular dependencies.
3. **Failure modes**: For each sub-task, what is the most likely failure mode?
4. **Reversibility**: If a sub-task produces wrong output, can you detect it before it poisons downstream tasks?
5. **Evidence requirements**: What evidence would confirm each sub-task succeeded? What would falsify it?

**Output Format:**

```
SUB_TASKS:
  - <numbered list of all identified sub-tasks>

DEPENDENCY_GRAPH: <valid/invalid with explanation>

CIRCULAR_DEPENDENCIES: <none/list any found>

FAILURE_MODES:
  - SUBTASK: <name>
    LIKELY_FAILURE: <description>
    DETECTION_STRATEGY: <how to detect when this occurs>

REVERSIBILITY_ASSESSMENT:
  - SUBTASK: <name>
    REVERSIBLE: <yes/no>
    CHECKPOINT: <where detection occurs before downstream impact>

EVIDENCE_REQUIREMENTS:
  - SUBTASK: <name>
    SUCCESS_EVIDENCE: <what confirms success>
    FAILURE_EVIDENCE: <what falsifies or indicates wrong output>

PLAN_QUALITY_SCORE: <1-5, where 5 = fully specified and failure-resilient>

FLAGS: <list any concerns that need addressing before proceeding>

PROCEED_DECISION: <yes/no - proceed only if score >= 4 and no unaddressed flags>
```

**Instructions:**
- A score below 4 indicates insufficient planning — revise before proceeding
- All flags must be addressed or explicitly accepted before execution
- Evidence requirements create checkpoints for verification during execution
