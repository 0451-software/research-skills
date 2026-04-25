---
name: Post-Failure Analysis
description: "Root-cause analysis after task failure. Use when a task has failed or produced an unsatisfactory result to diagnose what went wrong."
---

## Root-Cause Analysis (RCA)

A task has failed or produced an unsatisfactory result. Conduct a structured RCA.

**Task:** {task_description}
**Observed failure:** {failure_description}
**Expected outcome:** {expected_outcome}

**RCA Protocol:**
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

**Output Format:**

```
SYMPTOM: <precise statement of the failure, no interpretation>

TIMELINE:
  - <chronological list of events leading to failure>

CONTRIBUTING_FACTORS:
  - FACTOR: <description>
    CATEGORY: <tool_error|missing_info|assumption_error|reasoning_error|communication_failure>
    ENABLING: <how this factor contributed to the failure>

FIVE_WHYS:
  WHY_1: <initial why question>
  ANSWER_1: <response>
  WHY_2: <deeper why based on answer 1>
  ANSWER_2: <response>
  WHY_3: <deeper why>
  ANSWER_3: <response>
  WHY_4: <deeper why>
  ANSWER_4: <response>
  WHY_5: <deepest why - root cause>
  ANSWER_5: <final root cause>

ROOT_CAUSE: <single sentence stating the deepest correctable cause>

FIX: <specific change that would prevent recurrence>

VERIFICATION: <how to confirm the fix works>

FIX_LOG: <for pattern detection - summary suitable for cross-session analysis>
```

**Instructions:**
- Root cause must be specific and correctable, not a restatement of the symptom
- Apply 5 Whys iteratively until reaching a correctable root cause
- Fix must be concrete and actionable
- Verification must be specific testable criteria
- Log outcomes for pattern detection across sessions
