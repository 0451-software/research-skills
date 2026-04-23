#!/usr/bin/env python3
"""
PSMAS DAG to Phases Transformer

Transform a PSMAS (Planning → Scheduling → Monitoring → Adaptation → Shutdown) DAG
into a sequence of executable phases with validated checkpoints.

Features:
- Topological sort for dependency ordering
- TPA formula: theta = 2π * (sigma(i) - 1) / (n - 1) for angular window activation gating
- WPA formula: cumulative latency weighting for phase prioritization
- BFS-based cycle detection
- Angular window activation gating for phase enablement
"""

from __future__ import annotations

import math
import sys
from collections import deque, defaultdict
from dataclasses import dataclass, field
from typing import Optional


# =============================================================================
# Data Structures
# =============================================================================

@dataclass
class Task:
    """Represents a task node in the PSMAS DAG."""
    id: str
    description: str
    duration: float  # minutes
    resources: list[str] = field(default_factory=list)
    entry_criteria: list[str] = field(default_factory=list)
    exit_criteria: list[str] = field(default_factory=list)
    # Computed fields
    depth: int = 0
    sigma: int = 0  # Topological order index (1-based)
    tpa_theta: float = 0.0  # Angular position in execution cycle
    cumulative_latency: float = 0.0  # WPA component


@dataclass
class Phase:
    """Represents an executable phase containing tasks."""
    number: int
    name: str
    tasks: list[Task] = field(default_factory=list)
    parallel_tasks: list[str] = field(default_factory=list)  # Tasks that can run concurrently
    serial_tasks: list[str] = field(default_factory=list)    # Tasks that must be serial
    entry_checkpoint: list[str] = field(default_factory=list)
    exit_checkpoint: list[str] = field(default_factory=list)
    adaptation_triggers: list[dict] = field(default_factory=list)
    rollback_state: dict = field(default_factory=dict)
    # Angular window gating
    window_start: float = 0.0  # theta start
    window_end: float = 0.0    # theta end
    activated: bool = False


@dataclass
class PSMASDAG:
    """Complete PSMAS DAG with tasks and dependencies."""
    tasks: dict[str, Task] = field(default_factory=dict)
    dependencies: list[tuple[str, str]] = field(default_factory=list)  # (from, to)
    adjacency: dict[str, list[str]] = field(default_factory=dict)
    reverse_adj: dict[str, list[str]] = field(default_factory=dict)
    resources: dict[str, int] = field(default_factory=dict)  # resource -> capacity
    deadline: Optional[float] = field(default=None)  # minutes


# =============================================================================
# Core Algorithms
# =============================================================================

class CycleDetectionResult:
    def __init__(self):
        self.has_cycle: bool = False
        self.cycle_nodes: list[str] = []


def bfs_cycle_detection(dag: PSMASDAG) -> CycleDetectionResult:
    """
    BFS-based cycle detection using Kahn's algorithm (topological sort).
    If topological sort fails, a cycle exists.
    """
    result = CycleDetectionResult()
    
    # Calculate in-degree for each node
    in_degree = {task_id: 0 for task_id in dag.tasks}
    for (frm, to) in dag.dependencies:
        in_degree[to] += 1
    
    # BFS queue starting with nodes that have no dependencies
    queue = deque([tid for tid, deg in in_degree.items() if deg == 0])
    visited_count = 0
    
    while queue:
        node = queue.popleft()
        visited_count += 1
        
        for neighbor in dag.adjacency.get(node, []):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    
    if visited_count != len(dag.tasks):
        result.has_cycle = True
        # Find nodes in cycle by identifying nodes not visited in BFS
        not_visited = [tid for tid, deg in in_degree.items() if deg > 0]
        result.cycle_nodes = not_visited
    
    return result


def topological_sort(dag: PSMASDAG) -> list[str]:
    """
    Returns tasks in topological order using Kahn's algorithm.
    Raises ValueError if cycle detected.
    """
    in_degree = {task_id: 0 for task_id in dag.tasks}
    for (frm, to) in dag.dependencies:
        in_degree[to] += 1
    
    queue = deque([tid for tid, deg in in_degree.items() if deg == 0])
    topo_order = []
    
    while queue:
        node = queue.popleft()
        topo_order.append(node)
        
        for neighbor in dag.adjacency.get(node, []):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    
    if len(topo_order) != len(dag.tasks):
        raise ValueError(f"Cycle detected in DAG. Tasks in cycle: {[t for t in dag.tasks if t not in topo_order]}")
    
    return topo_order


def compute_depths(dag: PSMASDAG) -> None:
    """
    Compute depth (longest path from any source) for each task.
    Uses BFS from source nodes.
    """
    # Find source nodes (no incoming edges)
    has_incoming = set(to for (_, to) in dag.dependencies)
    sources = [tid for tid in dag.tasks if tid not in has_incoming]
    
    # BFS to compute depths
    for source in sources:
        dag.tasks[source].depth = 1
    
    queue = deque(sources)
    while queue:
        node = queue.popleft()
        current_depth = dag.tasks[node].depth
        
        for neighbor in dag.adjacency.get(node, []):
            # Depth is max of any path leading to this node
            if dag.tasks[neighbor].depth < current_depth + 1:
                dag.tasks[neighbor].depth = current_depth + 1
            queue.append(neighbor)


def compute_tpa(dag: PSMASDAG, topo_order: list[str]) -> None:
    """
    Compute TPA (Task Phase Angle) for angular window activation gating.
    Formula: theta = 2π * (sigma(i) - 1) / (n - 1)
    where sigma(i) is the 1-based topological order index.
    """
    n = len(topo_order)
    if n < 2:
        # Single node case - put at pi/2
        for i, task_id in enumerate(topo_order):
            dag.tasks[task_id].sigma = i + 1
            dag.tasks[task_id].tpa_theta = math.pi / 2
        return
    
    for i, task_id in enumerate(topo_order):
        sigma = i + 1
        theta = 2 * math.pi * (sigma - 1) / (n - 1)
        dag.tasks[task_id].sigma = sigma
        dag.tasks[task_id].tpa_theta = theta


def compute_wpa(dag: PSMASDAG, topo_order: list[str]) -> None:
    """
    Compute WPA (Weighted Phase Assignment) using cumulative latency weighting.
    Cumulative latency = sum of durations of all predecessor tasks.
    """
    # Compute cumulative latency for each task
    for task_id in topo_order:
        task = dag.tasks[task_id]
        # Sum of durations of all direct predecessors
        pred_latency = sum(
            dag.tasks[pred].duration
            for pred in dag.reverse_adj.get(task_id, [])
        )
        # Total cumulative latency through all predecessors in the path
        max_pred_latency = 0
        for pred in dag.reverse_adj.get(task_id, []):
            if dag.tasks[pred].cumulative_latency > max_pred_latency:
                max_pred_latency = dag.tasks[pred].cumulative_latency
        
        task.cumulative_latency = max_pred_latency + task.duration


def identify_critical_path(dag: PSMASDAG, topo_order: list[str]) -> list[str]:
    """
    Identify the critical path (longest duration chain) through the DAG.
    Returns list of task IDs on the critical path.
    """
    if not topo_order:
        return []
    
    # Compute end-to-start times (earliest completion time)
    ETC = {}  # Earliest time complete
    for task_id in topo_order:
        task = dag.tasks[task_id]
        max_pred_etc = 0
        for pred in dag.reverse_adj.get(task_id, []):
            if pred in ETC and ETC[pred] > max_pred_etc:
                max_pred_etc = ETC[pred]
        ETC[task_id] = max_pred_etc + task.duration
    
    # Backtrack from task with max ETC to find critical path
    if not ETC:
        return []
    
    max_end_task = max(ETC, key=ETC.get)
    critical_path = []
    
    # Build predecessor chain
    stack = [max_end_task]
    visited = set()
    while stack:
        current = stack.pop()
        if current in visited:
            continue
        visited.add(current)
        critical_path.append(current)
        
        # Find predecessor on critical path
        best_pred = None
        best_pred_etc = -1
        for pred in dag.reverse_adj.get(current, []):
            if pred in ETC:
                # Check if this predecessor is on the critical path
                # (i.e., its ETC + duration leads to current's ETC)
                if ETC[pred] + dag.tasks[current].duration == ETC[current]:
                    if ETC[pred] > best_pred_etc:
                        best_pred_etc = ETC[pred]
                        best_pred = pred
        
        if best_pred:
            stack.append(best_pred)
    
    critical_path.reverse()
    return critical_path


def check_reachability(dag: PSMASDAG) -> tuple[bool, list[str]]:
    """
    Check that all nodes are reachable from at least one source node.
    Returns (is_reachable, unreachable_nodes).
    """
    has_incoming = set(to for (_, to) in dag.dependencies)
    sources = [tid for tid in dag.tasks if tid not in has_incoming]
    
    if not sources:
        # No sources - all nodes should be checked differently
        # In a proper DAG, there must be at least one source
        reachable = set()
    else:
        reachable = set(sources)
        queue = deque(sources)
        
        while queue:
            node = queue.popleft()
            for neighbor in dag.adjacency.get(node, []):
                if neighbor not in reachable:
                    reachable.add(neighbor)
                    queue.append(neighbor)
    
    unreachable = [tid for tid in dag.tasks if tid not in reachable]
    return len(unreachable) == 0, unreachable


def check_orphans(dag: PSMASDAG) -> list[str]:
    """
    Find orphan nodes (no dependencies to/from other nodes).
    """
    orphans = []
    for task_id in dag.tasks:
        has_outgoing = len(dag.adjacency.get(task_id, [])) > 0
        has_incoming = len(dag.reverse_adj.get(task_id, [])) > 0
        if not has_outgoing and not has_incoming:
            orphans.append(task_id)
    return orphans


def check_resource_conflicts(phase: Phase, resources: dict[str, int]) -> list[str]:
    """
    Check if tasks in a phase exceed resource capacity.
    Returns list of conflicting resources.
    """
    usage = defaultdict(int)
    for task in phase.tasks:
        for resource in task.resources:
            usage[resource] += 1
    
    conflicts = []
    for resource, capacity in resources.items():
        if usage[resource] > capacity:
            conflicts.append(f"{resource}: need {usage[resource]}, have {capacity}")
    
    return conflicts


def angular_window_activation(current_theta: float, phase: Phase) -> bool:
    """
    Angular window activation gating.
    A phase is activated when current_theta enters its window [window_start, window_end].
    Uses wraparound handling for angles.
    """
    start = phase.window_start
    end = phase.window_end
    
    # Normalize angles to [0, 2π)
    current_theta = current_theta % (2 * math.pi)
    start = start % (2 * math.pi)
    end = end % (2 * math.pi)
    
    if start <= end:
        # Normal case: window doesn't wrap around 2π
        return start <= current_theta <= end
    else:
        # Wraparound case: window crosses 2π boundary
        return current_theta >= start or current_theta <= end


def assign_phase_windows(phases: list[Phase], total_duration: float) -> None:
    """
    Assign angular windows to phases based on TPA values of contained tasks.
    Window is [min_theta - margin, max_theta + margin] for each phase.
    """
    for phase in phases:
        if not phase.tasks:
            continue
        
        min_theta = min(t.tpa_theta for t in phase.tasks)
        max_theta = max(t.tpa_theta for t in phase.tasks)
        
        # Add margin based on total duration
        margin = (max_theta - min_theta) * 0.1 if max_theta > min_theta else 0.1
        phase.window_start = min_theta - margin
        phase.window_end = max_theta + margin


# =============================================================================
# Phase Assignment
# =============================================================================

def assign_phases(dag: PSMASDAG) -> list[Phase]:
    """
    Assign tasks to phases using width-first grouping with depth layering.
    
    Rules:
    1. Width-first: tasks with no dependencies on each other can share a phase
    2. Depth layering: tasks at same depth belong in same phase
    3. Resource bundling: split width layers if resource capacity exceeded
    4. Critical path preservation: ensure critical path tasks are properly ordered
    """
    # Group tasks by depth
    depth_groups = defaultdict(list)
    for task_id, task in dag.tasks.items():
        depth_groups[task.depth].append(task_id)
    
    # Sort depths
    sorted_depths = sorted(depth_groups.keys())
    
    phases = []
    phase_num = 1
    
    for depth in sorted_depths:
        tasks_at_depth = depth_groups[depth]
        
        # Within same depth, identify which tasks can run in parallel
        # (no dependencies between them) vs serial (have dependencies)
        parallel, serial = group_by_dependency(tasks_at_depth, dag)
        
        # Create phase for this depth layer
        phase_name = f"Phase_{phase_num}"
        phase = Phase(
            number=phase_num,
            name=phase_name,
            parallel_tasks=parallel,
            serial_tasks=serial
        )
        
        for task_id in parallel + serial:
            phase.tasks.append(dag.tasks[task_id])
        
        # Generate checkpoints
        phase.entry_checkpoint = generate_entry_checkpoint(phase, dag, phases)
        phase.exit_checkpoint = generate_exit_checkpoint(phase)
        phase.adaptation_triggers = generate_adaptation_triggers(phase, dag)
        phase.rollback_state = generate_rollback_state(phase)
        
        phases.append(phase)
        phase_num += 1
    
    # Assign angular windows
    total_duration = sum(t.duration for t in dag.tasks.values())
    assign_phase_windows(phases, total_duration)
    
    return phases


def group_by_dependency(task_ids: list[str], dag: PSMASDAG) -> tuple[list[str], list[str]]:
    """
    Split tasks into parallel (no inter-dependencies) and serial (have dependencies).
    """
    # Build dependency graph within this group
    in_group_deps = defaultdict(list)
    out_group_deps = defaultdict(list)
    
    for task_id in task_ids:
        for dep_from in dag.reverse_adj.get(task_id, []):
            if dep_from in task_ids:
                in_group_deps[task_id].append(dep_from)
        for dep_to in dag.adjacency.get(task_id, []):
            if dep_to in task_ids:
                out_group_deps[task_id].append(dep_to)
    
    # Tasks with no dependencies on other tasks in the group can be parallel
    parallel = []
    serial = []
    
    for task_id in task_ids:
        # Check if this task depends on others in the group
        if in_group_deps[task_id]:
            serial.append(task_id)
        else:
            parallel.append(task_id)
    
    return parallel, serial


def generate_entry_checkpoint(phase: Phase, dag: PSMASDAG, prior_phases: list[Phase]) -> list[str]:
    """Generate entry checkpoint conditions for a phase."""
    checkpoints = []
    
    if not prior_phases:
        # First phase - check source task entry criteria
        for task in phase.tasks:
            checkpoints.extend(task.entry_criteria)
    else:
        # After prior phases - check exit criteria of previous phase
        prev_phase = prior_phases[-1]
        checkpoints.extend(prev_phase.exit_checkpoint)
    
    return list(set(checkpoints))  # Deduplicate


def generate_exit_checkpoint(phase: Phase) -> list[str]:
    """Generate exit checkpoint conditions for a phase."""
    checkpoints = []
    for task in phase.tasks:
        checkpoints.extend(task.exit_criteria)
    return list(set(checkpoints))


def generate_adaptation_triggers(phase: Phase, dag: PSMASDAG) -> list[dict]:
    """Generate adaptation triggers for phase failures."""
    triggers = []
    
    for task in phase.tasks:
        # Task failure trigger
        trigger = {
            "trigger": f"Task {task.id} failed",
            "affected_tasks": dag.adjacency.get(task.id, []),
            "repair_action": f"Retry {task.id} or skip and continue"
        }
        triggers.append(trigger)
        
        # Resource exhaustion for this task
        if task.resources:
            trigger = {
                "trigger": f"Resource exhaustion for {task.id}",
                "affected_tasks": dag.adjacency.get(task.id, []),
                "repair_action": f"Defer {task.id}, reallocate resources"
            }
            triggers.append(trigger)
    
    # Timing overrun trigger
    total_duration = sum(t.duration for t in phase.tasks)
    trigger = {
        "trigger": f"Phase exceeds allocated time ({total_duration} min)",
        "affected_tasks": [t.id for t in phase.tasks],
        "repair_action": "Skip non-critical tasks or extend deadline"
    }
    triggers.append(trigger)
    
    return triggers


def generate_rollback_state(phase: Phase) -> dict:
    """Generate rollback state requirements for a phase."""
    return {
        "tasks": [t.id for t in phase.tasks],
        "checkpoint": f"state_after_{phase.name}",
        "required": True
    }


# =============================================================================
# Validation
# =============================================================================

@dataclass
class ValidationResult:
    cycle_check: bool = False
    reachability_check: bool = False
    orphan_check: bool = False
    resource_check: bool = False
    timing_check: bool = False
    phase_ordering_check: bool = False
    
    cycle_nodes: list[str] = field(default_factory=list)
    unreachable_nodes: list[str] = field(default_factory=list)
    orphan_nodes: list[str] = field(default_factory=list)
    resource_conflicts: list[str] = field(default_factory=list)
    phase_ordering_violations: list[tuple[str, str]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def validate_dag(dag: PSMASDAG, phases: list[Phase]) -> ValidationResult:
    """
    Run all validation checks on the DAG and phase assignment.
    """
    result = ValidationResult()
    
    # 1. Cycle detection
    cycle_result = bfs_cycle_detection(dag)
    result.cycle_check = not cycle_result.has_cycle
    result.cycle_nodes = cycle_result.cycle_nodes
    if cycle_result.has_cycle:
        result.errors.append(f"Cycle detected in DAG: {cycle_result.cycle_nodes}")
    
    # 2. Reachability check
    is_reachable, unreachable = check_reachability(dag)
    result.reachability_check = is_reachable
    result.unreachable_nodes = unreachable
    if not is_reachable:
        result.errors.append(f"Unreachable nodes: {unreachable}")
    
    # 3. Orphan check
    orphans = check_orphans(dag)
    result.orphan_check = len(orphans) == 0
    result.orphan_nodes = orphans
    if orphans:
        result.warnings.append(f"Orphan nodes (no dependencies): {orphans}")
    
    # 4. Resource conflicts
    result.resource_check = True
    for phase in phases:
        conflicts = check_resource_conflicts(phase, dag.resources)
        if conflicts:
            result.resource_check = False
            result.resource_conflicts.extend(conflicts)
    
    # 5. Timing constraint (deadline)
    if dag.deadline:
        total_duration = sum(t.duration for t in dag.tasks.values())
        critical_path = identify_critical_path(dag, list(dag.tasks.keys()))
        critical_duration = sum(dag.tasks[tid].duration for tid in critical_path)
        
        if critical_duration > dag.deadline:
            result.timing_check = False
            result.errors.append(
                f"Critical path ({critical_duration} min) exceeds deadline ({dag.deadline} min)"
            )
        else:
            result.timing_check = True
    else:
        result.timing_check = True
    
    # 6. Phase ordering verification
    violations = verify_phase_ordering(dag, phases)
    result.phase_ordering_violations = violations
    result.phase_ordering_check = len(violations) == 0
    if violations:
        result.errors.append(f"Phase ordering violations: {violations}")
    
    return result


def verify_phase_ordering(dag: PSMASDAG, phases: list[Phase]) -> list[tuple[str, str]]:
    """
    Verify that for every edge (A→B), phase(A) ≤ phase(B).
    """
    # Build task -> phase mapping
    task_to_phase = {}
    for phase in phases:
        for task in phase.tasks:
            task_to_phase[task.id] = phase.number
    
    violations = []
    for (frm, to) in dag.dependencies:
        phase_a = task_to_phase.get(frm)
        phase_b = task_to_phase.get(to)
        
        if phase_a is not None and phase_b is not None:
            if phase_a > phase_b:
                violations.append((frm, to))
    
    return violations


# =============================================================================
# Main Class
# =============================================================================

class PSMASToPhases:
    """
    Main transformer class for converting PSMAS DAG to executable phases.
    """
    
    def __init__(self):
        self.dag: Optional[PSMASDAG] = None
        self.phases: list[Phase] = []
        self.validation_result: Optional[ValidationResult] = None
    
    def load_from_dict(self, data: dict) -> None:
        """Load DAG from dictionary format."""
        dag = PSMASDAG()
        
        # Load tasks
        for task_data in data.get("tasks", []):
            task = Task(
                id=task_data["id"],
                description=task_data.get("description", ""),
                duration=task_data.get("duration", 0),
                resources=task_data.get("resources", []),
                entry_criteria=task_data.get("entry_criteria", []),
                exit_criteria=task_data.get("exit_criteria", [])
            )
            dag.tasks[task.id] = task
        
        # Load dependencies
        dag.dependencies = [
            (dep["from"], dep["to"])
            for dep in data.get("dependencies", [])
        ]
        
        # Build adjacency lists
        for task_id in dag.tasks:
            dag.adjacency[task_id] = []
            dag.reverse_adj[task_id] = []
        
        for (frm, to) in dag.dependencies:
            if frm in dag.adjacency and to in dag.reverse_adj:
                dag.adjacency[frm].append(to)
                dag.reverse_adj[to].append(frm)
        
        # Load resource constraints
        dag.resources = data.get("resources", {})
        
        # Load deadline
        dag.deadline = data.get("deadline")
        
        self.dag = dag
    
    def transform(self) -> list[Phase]:
        """
        Transform DAG to phases.
        Raises ValueError if validation fails.
        """
        if not self.dag:
            raise ValueError("DAG not loaded. Call load_from_dict first.")
        
        # Compute topological order
        topo_order = topological_sort(self.dag)
        
        # Compute depths
        compute_depths(self.dag)
        
        # Compute TPA and WPA
        compute_tpa(self.dag, topo_order)
        compute_wpa(self.dag, topo_order)
        
        # Assign phases
        self.phases = assign_phases(self.dag)
        
        # Validate
        self.validation_result = validate_dag(self.dag, self.phases)
        
        if self.validation_result.errors:
            raise ValueError(f"Validation failed: {self.validation_result.errors}")
        
        return self.phases
    
    def get_critical_path(self) -> list[str]:
        """Get the critical path through the DAG."""
        if not self.dag:
            return []
        return identify_critical_path(self.dag, list(self.dag.tasks.keys()))
    
    def get_report(self) -> str:
        """Generate a detailed report of the transformation."""
        if not self.dag or not self.phases:
            return "No data loaded. Call load_from_dict and transform first."
        
        lines = []
        lines.append("=" * 70)
        lines.append("PSMAS DAG TO PHASES REPORT")
        lines.append("=" * 70)
        
        # Critical path
        critical_path = self.get_critical_path()
        lines.append(f"\nCRITICAL PATH: {' -> '.join(critical_path)}")
        total_duration = sum(self.dag.tasks[tid].duration for tid in critical_path)
        lines.append(f"Critical Path Duration: {total_duration:.1f} minutes")
        
        # Validation summary
        if self.validation_result:
            lines.append("\n" + "-" * 70)
            lines.append("VALIDATION RESULTS")
            lines.append("-" * 70)
            checks = [
                ("Cycle Detection", self.validation_result.cycle_check),
                ("Reachability", self.validation_result.reachability_check),
                ("Orphan Check", self.validation_result.orphan_check),
                ("Resource Conflicts", self.validation_result.resource_check),
                ("Timing Constraints", self.validation_result.timing_check),
                ("Phase Ordering", self.validation_result.phase_ordering_check),
            ]
            for name, passed in checks:
                status = "✓ PASS" if passed else "✗ FAIL"
                lines.append(f"  {name}: {status}")
            
            if self.validation_result.errors:
                lines.append("\n  ERRORS:")
                for err in self.validation_result.errors:
                    lines.append(f"    - {err}")
            
            if self.validation_result.warnings:
                lines.append("\n  WARNINGS:")
                for warn in self.validation_result.warnings:
                    lines.append(f"    - {warn}")
        
        # Phases
        lines.append("\n" + "-" * 70)
        lines.append("PHASE ASSIGNMENTS")
        lines.append("-" * 70)
        
        for phase in self.phases:
            lines.append(f"\n{phase.name}: {phase.name.replace('_', ' ').title()}")
            lines.append(f"  Tasks: {[t.id for t in phase.tasks]}")
            lines.append(f"  Parallel: {phase.parallel_tasks}")
            lines.append(f"  Serial: {phase.serial_tasks}")
            lines.append(f"  Angular Window: [{phase.window_start:.3f}, {phase.window_end:.3f}] rad")
            lines.append(f"  Entry Checkpoint: {phase.entry_checkpoint}")
            lines.append(f"  Exit Checkpoint: {phase.exit_checkpoint}")
            
            if phase.adaptation_triggers:
                lines.append("  Adaptation Triggers:")
                for trig in phase.adaptation_triggers:
                    lines.append(f"    - {trig['trigger']}")
                    lines.append(f"      Affected: {trig['affected_tasks']}")
                    lines.append(f"      Repair: {trig['repair_action']}")
        
        lines.append("\n" + "=" * 70)
        
        return "\n".join(lines)


# =============================================================================
# Example Usage
# =============================================================================

def create_example_dag() -> dict:
    """Create an example PSMAS DAG for demonstration."""
    return {
        "tasks": [
            {
                "id": "P1",
                "description": "Define project goals and scope",
                "duration": 30,
                "resources": ["analyst"],
                "entry_criteria": ["requirements_document"],
                "exit_criteria": ["goals_approved"]
            },
            {
                "id": "P2",
                "description": "Decompose goals into tasks",
                "duration": 45,
                "resources": ["analyst"],
                "entry_criteria": ["goals_approved"],
                "exit_criteria": ["task_list_complete"]
            },
            {
                "id": "S1",
                "description": "Create initial schedule",
                "duration": 60,
                "resources": ["planner"],
                "entry_criteria": ["task_list_complete"],
                "exit_criteria": ["schedule_draft"]
            },
            {
                "id": "S2",
                "description": "Assign resources to tasks",
                "duration": 30,
                "resources": ["planner"],
                "entry_criteria": ["schedule_draft"],
                "exit_criteria": ["resources_assigned"]
            },
            {
                "id": "M1",
                "description": "Setup monitoring dashboard",
                "duration": 45,
                "resources": ["monitor"],
                "entry_criteria": ["resources_assigned"],
                "exit_criteria": ["monitoring_active"]
            },
            {
                "id": "M2",
                "description": "Define deviation thresholds",
                "duration": 20,
                "resources": ["analyst"],
                "entry_criteria": ["monitoring_active"],
                "exit_criteria": ["thresholds_configured"]
            },
            {
                "id": "A1",
                "description": "Define adaptation strategies",
                "duration": 40,
                "resources": ["analyst", "planner"],
                "entry_criteria": ["thresholds_configured"],
                "exit_criteria": ["adaptation_plans_ready"]
            },
            {
                "id": "S3",
                "description": "Finalize and approve schedule",
                "duration": 30,
                "resources": ["planner"],
                "entry_criteria": ["adaptation_plans_ready"],
                "exit_criteria": ["schedule_approved"]
            },
            {
                "id": "SH1",
                "description": "Execute shutdown procedure",
                "duration": 25,
                "resources": ["operator"],
                "entry_criteria": ["schedule_approved"],
                "exit_criteria": ["system_shutdown"]
            }
        ],
        "dependencies": [
            {"from": "P1", "to": "P2"},
            {"from": "P2", "to": "S1"},
            {"from": "S1", "to": "S2"},
            {"from": "S2", "to": "M1"},
            {"from": "M1", "to": "M2"},
            {"from": "M2", "to": "A1"},
            {"from": "A1", "to": "S3"},
            {"from": "S3", "to": "SH1"}
        ],
        "resources": {
            "analyst": 2,
            "planner": 1,
            "monitor": 1,
            "operator": 1
        },
        "deadline": 400
    }


if __name__ == "__main__":
    print("PSMAS DAG to Phases - Example Execution")
    print("=" * 50)
    
    # Create transformer
    transformer = PSMASToPhases()
    
    # Load example DAG
    example_data = create_example_dag()
    transformer.load_from_dict(example_data)
    
    print("\nInput DAG:")
    print(f"  Tasks: {list(transformer.dag.tasks.keys())}")
    print(f"  Dependencies: {transformer.dag.dependencies}")
    print(f"  Resources: {transformer.dag.resources}")
    print(f"  Deadline: {transformer.dag.deadline} minutes")
    
    # Transform
    try:
        phases = transformer.transform()
        
        # Print report
        print(transformer.get_report())
        
        # Demonstrate angular window activation
        print("\n" + "=" * 50)
        print("ANGULAR WINDOW ACTIVATION DEMO")
        print("=" * 50)
        
        # Simulate theta progression
        current_theta = 0.0
        step = math.pi / 8
        total_phases = len(phases)
        
        for i in range(total_phases + 2):
            print(f"\nTime step {i}: θ = {current_theta:.3f} rad ({current_theta * 180 / math.pi:.1f}°)")
            for phase in phases:
                active = angular_window_activation(current_theta, phase)
                status = "ACTIVATED" if active else "waiting"
                print(f"  {phase.name}: {status}")
            current_theta += step
        
        # Show TPA and WPA values
        print("\n" + "=" * 50)
        print("TASK METRICS (TPA & WPA)")
        print("=" * 50)
        
        for task_id, task in transformer.dag.tasks.items():
            print(f"\n  {task_id}:")
            print(f"    Sigma (topo order): {task.sigma}")
            print(f"    TPA Theta: {task.tpa_theta:.4f} rad ({task.tpa_theta * 180 / math.pi:.2f}°)")
            print(f"    Cumulative Latency (WPA): {task.cumulative_latency:.1f} min")
            print(f"    Depth: {task.depth}")
        
    except ValueError as e:
        print(f"\nError: {e}")
        sys.exit(1)
