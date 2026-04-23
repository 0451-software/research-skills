---
name: agent-delegation-strategy
description: "When and how to delegate non-trivial work to specialized persona sub-agents. Barry's guide for the orchestrator-worker pattern — covers delegation triggers, context preparation, persona selection, and result synthesis. Use when deciding whether to handle a task yourself or spawn a sub-agent."
version: 1.0.0
category: strategy
---

# Agent Delegation Strategy

Barry's guide for deciding *when* to delegate, *which* persona to use, and *how* to prepare the context for maximum sub-agent effectiveness.

## The Core Principle

> Non-trivial work belongs to a specialized persona sub-agent, not to Barry's primary context.

Non-trivial = anything requiring more than ~5 tool calls, more than one distinct skill domain, or more than one logical phase of work.

This is not about capability — it's about **context isolation**, **independent verification**, and **parallelism**. A sub-agent working in an isolated context won't have its reasoning contaminated by Barry's prior moves. Multiple sub-agents can work in parallel. Results are synthesized by Barry.

## Delegation Decision Tree

```
Is the task non-trivial? (multi-step, multi-phase, or requires specialized knowledge)
├── NO  → Handle it yourself directly
└── YES → Continue

Does the task fit a persona's phase workflow?
├── YES → Use the phase-gated persona workflow
└── NO  → Delegate with general context + explicit output format

Is the task embarrassingly parallel? (multiple independent sub-tasks)
├── YES → Use delegate_task with tasks=[] (up to 3 parallel sub-agents)
└── NO  → Sequential delegation with result synthesis
```

## Context Preparation Checklist

Before delegating, prepare the following — the more complete, the better the sub-agent output.

| Field | Required? | Description |
|-------|-----------|-------------|
| **goal** | Yes | One clear sentence: what does success look like? |
| **constraints** | Yes | What must stay unchanged? What boundaries exist? |
| **output_format** | Strongly recommended | What should the sub-agent return? (report, code PR, list, analysis) |
| **relevant_artifacts** | If applicable | File paths, prior outputs, relevant code snippets, URLs |
| **success_criteria** | Yes | How will you know the delegation succeeded? |
| **persona** | Yes | Which persona skill matches this task? |
| **phase** | If using phase workflow | Which phase (0-6) does this correspond to? |

## Persona Selection Guide

| Task Type | Persona | Phase |
|-----------|---------|-------|
| Background research, landscape survey, options analysis | `persona-researcher` | 0-1 |
| Proposing an approach or architecture | `persona-engineer` | 2 |
| Challenging/approving a proposal before building | `persona-inspector` | 2.5 |
| Building/implementing code or config | `persona-engineer` | 3 |
| Verifying/test and confirm work | `persona-inspector` | 4 |
| Red-teaming / stress-testing a plan, code, or architecture | `persona-adversarial-reviewer` | 2.7, 4.5, 6 |
| Final merge review | Barry (main) | 5 |

## Phase-Gated Workflow (Full)

This is the canonical workflow for complex tasks. Not every task needs all phases — use what's appropriate.

```
Phase 0:  Researcher   → Scout: monitor landscape, gather context
Phase 1:  Researcher   → Survey: systematic research, options analysis
Phase 2:  Engineer     → Propose: post approach in group
Phase 2.5: Inspector   → Challenge Gate: binding veto (must score 13+/20)
Phase 2.7: Adversarial  → Pre-Implementation Red Team: attack the proposal
         [BLOCKER: Phase 2.7 findings must be addressed before Phase 3]
Phase 3:  Engineer     → Implement: build it, ship working code
Phase 4:  Inspector    → Verify: test and confirm
Phase 4.5: Adversarial  → Post-Implementation Red Team: break the verified work
Phase 5:  Barry (main) → Merge: final review and synthesis
Phase 6:  Adversarial   → On-demand Plan/Architecture Red Team
```

**Critical rule:** Phase 2.5 (Inspector veto) is binding. Phase 2.7 (Adversarial red team) findings with CRITICAL/HIGH severity must be addressed before Phase 3 begins.

## Delegation Template

When using `delegate_task`, structure the goal field as:

```
## Task
<one clear sentence describing what the sub-agent should accomplish>

## Context
<relevant background, constraints, file paths, prior outputs>

## Output Format
<what to return — be specific about sections, format, and depth>

## Success Criteria
<how you'll evaluate whether the task succeeded>
```

## Result Synthesis

After sub-agent completes:
1. Read the report/results
2. Apply your own judgment — don't accept uncritically
3. For phase-gated work: decide whether to proceed to next phase or loop back
4. For parallel delegation: merge findings, identify conflicts, synthesize into one coherent output
5. Log notable delegation patterns (what works, what doesn't) for future reference

## Common Mistakes

### Mistake 1: Delegating without context
**Bad:** `goal: "fix the bug"`
**Good:** `goal: "Fix the null pointer exception in ~/src/auth.py line 47 that occurs when the user has no session token. The error is: [error text]. Output: fixed code + explanation of root cause."`

### Mistake 2: Not specifying output format
**Bad:** `goal: "research async Python patterns"`
**Good:** `goal: "research async Python patterns for I/O-bound web scraping" output_format: "3 options with pros/cons, code examples, and recommended choice for ~10k URL crawl"`

### Mistake 3: Skipping the Inspector gate
**Don't skip Phase 2.5.** The Inspector's binding veto exists to catch bad approaches before expensive implementation work. Running Phase 3 without Phase 2.5 clearance means you may build the wrong thing.

### Mistake 4: Not acting on Adversarial findings
The Adversarial Reviewer finds real failure modes. CRITICAL/HIGH findings are not suggestions — they are early warnings. Address them or explicitly document why you're proceeding anyway.

### Mistake 5: Parallelizing dependent tasks
You can run up to 3 sub-agents in parallel via `delegate_task(tasks=[...])`. Only parallelize tasks that are truly independent. If Phase 2 must complete before Phase 3, that's sequential — don't force it into parallel.

## Escalation to Human

Delegate to a human when:
- A CRITICAL severity finding has no clear fix path
- The task requires access to credentials/secrets the sub-agent cannot have
- A Phase 2.5 veto is contested and the stakes are high
- The task scope exceeds what any sub-agent can reasonably accomplish in one delegation

## See Also

- `persona-researcher` — Phase 0-1 research workflow
- `persona-engineer` — Phase 2-3 implementation workflow
- `persona-inspector` — Phase 2.5/4 challenge gate workflow
- `persona-adversarial-reviewer` — Phase 2.7/4.5/6 red team workflow
- `psmas-dag-to-phases` — DAG-to-executable-phase conversion for complex task graphs
