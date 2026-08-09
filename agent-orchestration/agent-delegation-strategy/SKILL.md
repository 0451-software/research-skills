---
name: agent-delegation-strategy
description: "When and how to delegate non-trivial work to specialized persona sub-agents. Guide for the orchestrator-worker pattern — covers delegation triggers, context preparation, persona selection, phase workflow, spawn depth, and result synthesis. Use when deciding whether to handle a task yourself or spawn a sub-agent."
version: 1.2.0
category: strategy
---

# Agent Delegation Strategy

guide for deciding *when* to delegate, *which* persona to use, and *how* to prepare the context for maximum sub-agent effectiveness.

## The Core Principle

> Non-trivial work belongs to a specialized persona sub-agent, not to the agent's primary context.

Non-trivial = anything requiring more than ~5 tool calls, more than one distinct skill domain, or more than one logical phase of work.

This is not about capability — it's about **context isolation**, **independent verification**, and **parallelism**. A sub-agent working in an isolated context won't have its reasoning contaminated by the agent's prior moves. Multiple sub-agents can work in parallel. Results are synthesized by the agent.

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

Before delegating, prepare the following — the more complete, the better the sub-agent output:

| Field | Required | Description |
|-------|----------|-------------|
| **goal** | Yes | One clear sentence: what does success look like? |
| **constraints** | Yes | What must stay unchanged? Boundaries? Include token budget if relevant. |
| **output_format** | Strongly recommended | What to return (report, code PR, list, analysis) |
| **relevant_artifacts** | If applicable | File paths, prior outputs, code snippets, URLs |
| **success_criteria** | Yes | How will you know the delegation succeeded? |
| **persona** | Yes | Which persona skill matches this task? |
| **phase** | If using phase workflow | Which phase (0–6)? |

> **⚠ Critical (learned 2026-04-25):** Every delegation that produces a file must instruct the sub-agent to "write findings to [path], commit, and push before returning." The committed file IS the output — do not accept file content in the summary.

## Persona Selection Guide

| Task Type | Persona | Phase |
|-----------|---------|-------|
| Background research, landscape survey, options analysis | `persona-researcher` | 0–1 |
| Proposing an approach or architecture | `persona-engineer` | 2 |
| Challenging/approving a proposal before building | `persona-inspector` | 2.5 |
| Building/implementing code or config | `persona-engineer` | 3 |
| Verifying/test and confirm work | `persona-inspector` | 4 |
| Red-teaming / stress-testing a plan, code, or architecture | `persona-adversarial-review` | 2.7, 4.5, 6 |
| Final merge review | orchestrator (main agent) | 5 |

**Persona skill references:** Each persona skill (`persona-researcher`, `persona-engineer`, `persona-inspector`, `persona-adversarial-review`) has detailed guidance on toolsets and goal structures. Load the relevant persona skill before delegating.

## Phase-Gated Workflow

For implementation tasks (code, config, infra) — not every phase is always needed:

```
Phase 0:  Researcher   → Scout: monitor landscape, gather context
Phase 1:  Researcher   → Survey: systematic research, options analysis
Phase 2:  Engineer     → Propose: post approach for review
Phase 2.5: Inspector   → Challenge Gate: binding veto (must score 13+/20)
Phase 2.7: Adversarial  → Pre-Implementation Red Team: attack the proposal
         [BLOCKER: Phase 2.7 CRITICAL/HIGH findings must be addressed before Phase 3]
Phase 3:  Engineer     → Implement: build it, ship working code
Phase 4:  Inspector    → Verify: test and confirm
Phase 4.5: Adversarial  → Post-Implementation Red Team: break the verified work
Phase 5:  orchestrator (main agent) → Merge: final review and synthesis
Phase 6:  Adversarial   → On-demand Plan/Architecture Red Team
```

**Critical rules:**
- Phase 2.5 (Inspector veto) is binding — do not skip it
- Phase 2.7 CRITICAL/HIGH findings block Phase 3 until addressed

## Delegation Template

When using `delegate_task`, structure the goal field as:

```markdown
## Task
<one clear sentence describing what the sub-agent should accomplish>

## Context
<relevant background, constraints, file paths, prior outputs>

## Output Format
<what to return — be specific about sections, format, and depth>

## Success Criteria
<how you'll evaluate whether the delegation succeeded>

## Constraints (when delegating from creator/vendor sources)
No brand/provider-specific content. Cite sources by topic description, not speaker name, 
model name, or company. Brand-specific claims may be noted as caveats but cannot form 
the basis of recommendations.

## Token Budget (optional)
- warning_threshold: 8000
- hard_limit: 15000
- current_estimate: ~N
```

**File output rule:** Always include: "write findings to `[path]`, commit, and push before returning."

---

## Delegation Execution Notes

### Writing and Committing Within Sub-Agents (Critical)

Sub-agents write files and commit them directly — do NOT return file content in your summary.

**Required pattern for every delegation that produces a file output:**
1. Delegate with explicit output file path in the goal
2. Sub-agent writes the file to disk
3. Sub-agent commits the file (e.g., `git add <file> && git commit -m "<descriptive message>"`)
4. Sub-agent returns ONLY: commit SHA + file path + one-paragraph summary

**Verification:** Before returning, confirm the file exists at the target path (e.g., `ls <path>` or platform-equivalent check).

### Pushing After Batch Completion

After a parallel batch completes, push once from the project root:
```bash
git push <remote> <branch>
```
The final push from the orchestrator after the batch ensures all commits reach the remote.

### Per-Task File Targeting in Batch Mode

Each sub-agent in a batch must write to a **different output file**. Never have two sub-agents in the same batch write to the same file.

### Reading Shared Sources in Batch Mode

When all sub-agents read the same source files:
- Use a multi-file batch read for the initial read — handles compression in one call
- Cache reads locally; don't re-read redundantly
- If a sub-agent needs to re-read after writing, use `ctx_read` with `fresh=true`

### Cross-Wave File Dependencies (for multi-wave patterns like adversarial debate)

- Wave 2 cannot start until Wave 1 commits are pushed
- Wave 3 cannot start until Wave 2 commits are pushed
- **Confirm the previous wave's push succeeded before starting the next wave**

---

## Context Efficiency for Sub-Agents

Sub-agents run in isolated contexts, so they don't inherit the orchestrator's read cache. The cheapest way to keep sub-agent work efficient is to pass relevant excerpts (or pointers to specific files/lines) in the delegation context rather than have sub-agents re-read or re-discover the source material.

**General best practices (platform-agnostic):**
1. Read source material once at the orchestrator and pass relevant excerpts via context.
2. Prefer targeted reads (line ranges, function signatures) over full-file reads when only a section is needed.
3. Batch reads into a single call when your platform supports it.
4. If your agent integrates with a context-compression tool (e.g., for symbol outlines, semantic search, or compressed-read modes), use it for large files that would otherwise dominate the sub-agent's context.

If your agent does not have a context-compression tool, the same conventions still apply — reduce what the sub-agent must read.

---

## Result Synthesis

After sub-agent completes:
1. Read the report/results
2. Apply your own judgment — don't accept uncritically
3. For phase-gated work: decide whether to proceed to next phase or loop back
4. For parallel delegation: merge findings, identify conflicts, synthesize into one coherent output

---

## Common Mistakes

### Mistake 1: Delegating without context
**Bad:** `goal: "fix the bug"`  
**Good:** `goal: "Fix the null pointer exception in ~/src/auth.py line 47 that occurs when the user has no session token. Error: [text]. Output: fixed code + root cause explanation."`

### Mistake 2: Not specifying output format
**Bad:** `goal: "research async Python patterns"`  
**Good:** `goal: "research async Python patterns for I/O-bound web scraping" output_format: "3 options with pros/cons, code examples, recommended choice for ~10k URL crawl"`

### Mistake 3: Skipping the Inspector gate
Don't skip Phase 2.5. The Inspector's binding veto catches bad approaches before expensive implementation. Running Phase 3 without Phase 2.5 clearance means you may build the wrong thing.

### Mistake 4: Not acting on Adversarial findings
CRITICAL/HIGH findings are not suggestions — they are early warnings. Address them or explicitly document why you're proceeding anyway.

### Mistake 5: Parallelizing dependent tasks
You can run up to 3 sub-agents in parallel. Only parallelize tasks that are truly independent. Phase 2 → Phase 3 is sequential — don't force it into parallel.

### Mistake 6: Ambiguous domain names in research delegations
"research-skills" could mean skills *about* research OR skills *derived from* AI research. A sub-agent picks one — usually the wrong one.

**Fix:** Clarify with the user first, or give explicit examples of what you want AND what to exclude.

### Mistake 7: Not pre-flighting external services
Sending a sub-agent to call `image_generate`, `video_transcribe`, or any external API without testing first wastes tokens on garbage output.

**Fix:** Make one test call yourself first. If it fails, handle it yourself or inform the user before delegating.

### Mistake 8: Sub-agents returning file content in summary
**Bad:** Sub-agent puts analysis text in the `summary` field, forcing the agent to extract and write the file manually.  
**Fix:** Every delegation goal with file output must say: "write findings to [path], commit, and return only the commit SHA and file path."

---

## Escalation to Human

Delegate to a human when:
- A CRITICAL severity finding has no clear fix path
- The task requires credentials/secrets the sub-agent cannot have
- A Phase 2.5 veto is contested and stakes are high
- Task scope exceeds what any sub-agent can reasonably accomplish in one delegation

---

## Spawn Depth and Orchestrator Role

### Default Behavior (Flat, Depth 1)

`max_spawn_depth=1` (default) — all sub-agents are **leaf** nodes. the agent is depth 0; children land at depth 1 and cannot spawn further workers.

| Config | Behavior |
|--------|----------|
| `max_spawn_depth: 1` (default) | Flat — children are leaf nodes, cannot delegate |
| `max_spawn_depth: 2` | One level of orchestration — orchestrator children can spawn leaves |
| `max_spawn_depth: 3` | Two levels of orchestration — rarely needed |

**Why default flat?** Nested delegation multiplies context size, latency, and failure surface. Most tasks fit in one the agent → sub-agent hop.

### When to Use the Orchestrator Role

**the agent is always the orchestrator.** Personas are leaf nodes. Use `role="orchestrator"` only when:
- `max_spawn_depth >= 2` in config
- A sub-agent genuinely needs to coordinate multiple parallel sub-tasks
- The coordination complexity justifies the extra hop

Most delegation does not need this. Flat the agent → persona is the standard pattern.

When sub-agents run concurrently, they may read or write overlapping files. To avoid mangled edits:

- Avoid parallel sub-agents editing the same file — serialize through one sub-agent
- Set concurrency to 1 for tightly coupled file operations
- Re-read files before editing after a sub-agent completes if your wave touched them earlier

**Best practices for platforms that track file state across sub-agents:**
1. Avoid parallel sub-agents editing the same file — serialize through one sub-agent
2. Set concurrency to 1 for coupled file operations
3. Re-read files before editing after a sub-agent completes if you touched them earlier
4. If your platform provides a process-wide file-state registry, prefer it; otherwise, track reads/writes manually in the orchestrator's notes

---

## Pitfalls

### Sub-Transport Failures

If your platform offers optional sub-agent transports (e.g., an external CLI runner, an ACP bridge, a different model provider), they may fail to start if the required binary isn't installed. The failure is often silent and surfaces as a timeout or `max_iterations` error.

**Symptoms:** Sub-agent returns a "could not start <transport>" or "install <binary> or set <config>" error after retries.

**Fix:** Retry the same `delegate_task` call without the optional transport parameters — use the platform's default transport instead. Optional transports are just that — optional; the default transport works for all sub-agent workloads.

**Prevention:** Default to your platform's default transport. Only opt into an alternative transport when the task specifically requires its features.

### Parallel Sub-Agents Editing the Same File

If multiple parallel sub-agents write to the same file, edits can be lost or mangled.

**Symptoms:** One sub-agent's changes disappear; git shows only one set of modifications.

**Fix:** Serialize file writes through a single sub-agent, or use `max_concurrent_children=1` for coupled operations.

---

## See Also

- `adversarial-research-debate` — Wave 1–4 debate pattern for extracting knowledge from competing theses
- `persona-researcher` — Phase 0–1 research workflow
- `persona-engineer` — Phase 2–3 implementation workflow
- `persona-inspector` — Phase 2.5/4 challenge gate workflow
- `persona-adversarial-review` — Phase 2.7/4.5/6 red team workflow
- `psmas-dag-to-phases` — DAG-to-executable-phase conversion for complex task graphs
