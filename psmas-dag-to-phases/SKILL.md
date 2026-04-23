---
name: psmas-dag-to-phases
description: "Transform a PSMAS (Planning, Scheduling, Monitoring, Adaptation, Shutdown) DAG of tasks into executable phases with checkpoint validation. Use when: (1) a complex multi-step plan needs to be decomposed into runnable phases, (2) task dependencies must be verified for cycles and ordering constraints, (3) each phase needs explicit entry/exit criteria for checkpoint-based validation, (4) adaptation triggers need to be mapped to specific DAG nodes for mid-execution plan repair. NOT for: simple linear task lists (use a basic step planner), real-time reactive systems, or tasks with no defined dependency structure."
---

# PSMAS DAG to Phases

Transform a PSMAS (Planning → Scheduling → Monitoring → Adaptation → Shutdown) DAG into a sequence of executable phases with validated checkpoints. Converts a graph of tasks with dependencies into a runnable phased execution plan.

## PSMAS Model Overview

| Phase | Full Name | Purpose |
|-------|-----------|---------|
| P | Planning | Define goals, decompose into tasks, establish dependencies |
| S | Scheduling | Assign ordering, timing, and resource constraints to tasks |
| M | Monitoring | Track execution state against the plan; detect deviations |
| A | Adaptation | Trigger plan repair when deviations exceed thresholds |
| S | Shutdown | Graceful termination; cleanup; final state validation |

## When to Use

- A task graph (DAG) has been defined and needs to be converted into a sequential or parallel executable plan
- A multi-step plan has failure points that need explicit checkpoint validation before proceeding
- Mid-execution adaptation is required — need to identify which DAG nodes are affected by a specific failure
- Handing off a plan to a sub-agent or external system that requires phased execution
- Validating that a plan has no circular dependencies or impossible ordering constraints
- Resource-constrained scheduling: tasks need to be grouped into phases that respect resource limits

## Process

### Phase 1 — DAG Ingestion

Accept a DAG definition with:
- Nodes: task ID, description, estimated duration, resource requirements, entry criteria, exit criteria
- Edges: dependency relationships (A must complete before B starts)

```
Input format:
TASKS:
  - id: T1
    description: <string>
    duration: <minutes>
    resources: <list>
    entry_criteria: <list of conditions>
    exit_criteria: <list of conditions>
  - id: T2 ...

DEPENDENCIES:
  - from: T1
    to: T2
  ...
```

### Phase 2 — Validation

Run the following checks:

1. **Cycle detection**: Use topological sort. If sort fails, report the cycle.
2. **Reachability**: All nodes must be reachable from at least one source node.
3. **Orphan check**: No nodes should exist without a path to or from any other node (unless intentional isolation).
4. **Resource conflicts**: Tasks in the same phase cannot exceed available resource capacity.
5. **Timing constraints**: If a deadline is specified, verify the critical path fits within it.

### Phase 3 — Phase Assignment

Group tasks into phases using these rules:

1. **Width-first grouping**: Tasks with no dependencies on each other can share a phase (parallel execution potential).
2. **Depth layering**: Tasks at the same depth level in the dependency tree belong in the same phase.
3. **Resource bundling**: If resource capacity is limited, split width layers into sub-phases.
4. **Critical path preservation**: The critical path (longest duration chain) drives minimum total duration.

Output: ordered list of phases, each containing a list of tasks that can execute in parallel, plus tasks that must be serial within the phase.

### Phase 4 — Checkpoint Definition

For each phase, define:

- **Entry checkpoint**: Conditions that must be true before the phase starts
- **Exit checkpoint**: Conditions that must be true when the phase completes
- **Adaptation triggers**: If exit checkpoint fails, which DAG nodes are affected and what repair options exist
- **Rollback plan**: For each phase, what state must be preserved to enable rollback if the phase fails

### Phase 5 — Adaptation Mapping

Map each adaptation trigger to specific DAG nodes:

- Failure of task T → which dependent tasks are blocked?
- Resource exhaustion → which tasks in current and future phases are affected?
- Timing overrun → which tasks on the critical path are affected?
- External event → which tasks have exposure to the event source?

## Prompt Templates

### Template A — DAG to Phases Conversion

```
## PSMAS DAG to Phases Conversion

Given the following task DAG, produce an executable phased plan.

TASKS:
{task_list}

DEPENDENCIES:
{dependency_list}

RESOURCE_CONSTRAINTS:
{resource_constraints}

DEADLINE (if any): {deadline}

## Output Format

### Phase Assignment
PHASE_N: [list of task IDs]

### Phase Detail
For each phase:
PHASE_N: <phase name>
TASKS: <task IDs in execution order within phase>
PARALLELISM: <which tasks can run concurrently>
ENTRY_CHECKPOINT: <conditions required before phase starts>
EXIT_CHECKPOINT: <conditions required for phase completion>
ADAPTATION_TRIGGERS:
  - trigger: <failure condition>
    affected_tasks: <downstream tasks blocked>
    repair_action: <recommended fix>
ROLLBACK_STATE: <state to preserve for rollback>
```

### Template B — Mid-Execution Phase Validation

```
## Phase Checkpoint Validation

CURRENT_PHASE: {phase_number} ({phase_name})
TASKS_IN_PHASE: {task_list}
PLANNED_EXIT_CHECKPOINT: {exit_checkpoint_conditions}

## Actual State
Task completion status: {task_statuses}
Resource usage: {actual_resource_usage}
Elapsed time: {elapsed_time}
Deviation from plan: {deviation_description}

## Validation
1. Are all tasks in the phase complete?
2. Do exit checkpoint conditions hold?
3. Is deviation within tolerance?
4. Are any downstream phases already affected?

VALIDATION_RESULT: PASS | FAIL | CONDITIONAL_PASS
ADAPTATION_REQUIRED: YES | NO
ADAPTATION_TYPE: <replan | skip | defer | rollback | escalate>
```

### Template C — DAG Repair After Failure

```
## DAG Repair — Post-Failure

FAILED_NODE: {task_id}
FAILURE_MODE: {how it failed}
DEPENDENTS_AFFECTED: {list of tasks blocked by this failure}
CURRENT_PHASE: {phase_number}

## Repair Options
Rank the following options and select the best:

OPTION_A — Skip and continue:
  Skip failed node, mark dependents as handled (if possible), continue pipeline.
  Tradeoff: may produce incomplete output; downstream quality risk.

OPTION_B — Retry:
  Retry failed node with same or modified parameters.
  Tradeoff: may fail again if root cause is systemic; time cost.

OPTION_C — Substitute:
  Use an alternative task or approach that achieves the same goal.
  Tradeoff: requires re-planning; may change output semantics.

OPTION_D — Defer:
  Pause the pipeline at this point, escalate to human review.
  Tradeoff: breaks automation; ensures human oversight.

OPTION_E — Rollback:
  Roll back to the last valid checkpoint and re-execute from there.
  Tradeoff: time cost; may fail at same point if root cause is in prior phase.

SELECTED_OPTION: <A|B|C|D|E>
RATIONALE: <why this is the best choice given failure mode and constraints>
REVISED_PIPELINE: <updated phase/task list if different from original>
```

## Pitfalls

1. **Incomplete DAG input**: If not all dependencies are specified, the phase assignment will contain hidden sequential bottlenecks. Always verify dependency completeness before phase generation.

2. **Ignoring resource constraints during phase assignment**: A phase that is logically sound may still be infeasible if it demands more resources than available. Always factor in resource capacity.

3. **Checkpoint over-specification**: Entry/exit criteria that are too strict will cause false negatives (phase passes but is actually invalid). Define criteria that are necessary and sufficient, not exhaustive.

4. **Treating adaptation as an afterthought**: The adaptation map should be defined *before* execution begins, not during failure. Pre-defined adaptation plans are faster and less error-prone than improvised ones.

5. **Rolling back to wrong checkpoint**: Without explicit rollback state preserved at each phase, rollback may be impossible or may restore an inconsistent state.

6. **Critical path blindness**: If the critical path is not identified, resource allocation and scheduling decisions may inadvertently lengthen total execution time.

## Advanced Features

### Temporal Phase Activation (TPA)
TPA assigns angular positions to phases based on their estimated execution time, enabling
temporal scheduling across parallel-capable phases:
```
theta = 2π × (rank(i) - 1) / (n - 1)
```
Where rank(i) is the phase's position in the critical path ordering and n is total phases.
Phases within the same angular window (ε = 0.52) can execute in parallel.

### Weighted Phase Assignment (WPA)
WPA assigns final phase positions using cumulative latency weighting — phases with longer
critical path dependencies get priority placement:
- Phases on the critical path: placed first within their angular window
- Phases with higher cumulative downstream latency: given preferential angular positioning
- ω_ratio = 0.85: within-window priority weighting

These features are automatically applied when `dag_to_phases.py` runs. You do not need to
invoke them separately.

## Verification

1. **Cycle check**: Apply topological sort to the DAG. Confirm it succeeds. Then inject a synthetic dependency that creates a cycle and verify the cycle is detected.

2. **Phase ordering correctness**: Verify that for every edge (A→B), phase(A) ≤ phase(B). Write a script that checks this invariant across all edges.

3. **Checkpoint coverage**: For each phase, verify that entry checkpoint is achievable given the exit checkpoint of the prior phase. If not, flag the gap.

4. **Adaptation map completeness**: For each task node, verify there is at least one defined adaptation trigger. If a task has no failure mode defined, it cannot be recovered.

5. **End-to-end dry run**: Simulate execution with a small DAG (5–7 nodes) through all phases including one adaptation trigger. Verify the repair path executes correctly.
