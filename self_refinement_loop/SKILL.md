---
name: self_refinement_loop
description: "Self-refinement loop skill using MRO (Monitor/Reasoner/Controller) three-role factorization. Use when iteratively improving a response, catching errors before they propagate, or recovering from dead-ends. Integrates with metacognitive-mro-prompts templates for structured self-regulation."
---

# Self-Refinement Loop (MRO)

A closed-loop self-improvement system with three distinct roles that rotate through each refinement cycle:

- **Monitor**: Observes the current output, detects issues, and evaluates progress against criteria
- **Reasoner**: Diagnoses root causes of detected issues, proposes revisions, and generates alternatives
- **Controller**: Validates proposed changes, decides which revision to apply, and commits the refined output

## When to Use

- Iteratively improving a response, code, plan, or other deliverable
- Catching errors or quality issues before they propagate to downstream steps
- When a first-draft response requires multi-pass refinement
- Recovering from a dead-end or failed approach
- Any task where quality gates or multiple revision passes are beneficial

## Architecture

Each refinement cycle consists of three phases:

```
┌─────────────────────────────────────────────────────────────┐
│  CYCLE N                                                    │
│                                                             │
│  1. MONITOR → evaluates current_output, detects issues      │
│       ↓                                                     │
│  2. REASONER → diagnoses root causes, proposes revisions    │
│       ↓                                                     │
│  3. CONTROLLER → validates changes, commits refined_output  │
│       ↓                                                     │
│  [loop until EXIT_CRITERIA met or max_iterations reached]   │
└─────────────────────────────────────────────────────────────┘
```

## Prompt Files

| File | Role | Description |
|------|------|-------------|
| `prompts/monitor.md` | Monitor | Issue detection and quality evaluation |
| `prompts/reasoner.md` | Reasoner | Root-cause diagnosis and revision generation |
| `prompts/controller.md` | Controller | Validation and commitment of refined output |
| `prompts/loop_manager.md` | Loop Manager | Exit criteria evaluation and cycle orchestration |

## Integration with metacognitive-mro-prompts

This skill is designed to compose with the metacognitive-mro-prompts templates:

- **Pre-execution**: Use `metacognitive-mro-prompts/prompts/pre-execution-check.md` before the first refinement cycle to validate the plan
- **Mid-loop**: Use `metacognitive-mro-prompts/prompts/mid-execution-check.md` if the loop stalls or diverges
- **Post-loop**: Use `metacognitive-mro-prompts/prompts/post-failure-analysis.md` if the loop fails to converge
- **Bias detection**: Use the bias detection prompts documented in
`metacognitive-mro-prompts/SKILL.md` (Section 4, lines 88–106) —
these are inline prompts, not separate files. The Monitor role in this
loop should cross-reference those bias patterns when diagnosing
Reasoner output.

## Usage

### Basic Loop

```
[Initialize current_output with first draft]
[max_iterations = 3]

for cycle in 1..max_iterations:
    issues = Monitor(current_output, criteria)
    if no_critical_issues(issues):
        break
    revisions = Reasoner(current_output, issues)
    current_output = Controller(current_output, revisions)
```

### Inline Injection

For simpler use cases, inject the three-role factorization inline:

```
[First draft complete]
→ MONITOR: Evaluate against criteria, list issues
→ REASONER: For each issue, diagnose cause and propose fix
→ CONTROLLER: Validate and commit changes
[Refined output]
```

## Exit Criteria

The loop terminates when any of these conditions are met:

1. **Quality threshold**: Monitor reports no critical issues (severity >= threshold resolved)
2. **Convergence**: Controller reports output is stable (proposed change rejected as no-op)
3. **Max iterations**: Iteration limit reached — return best effort
4. **Dead-end**: Reasoner reports no viable revision path

## Pitfalls

1. **Infinite loops**: Always set max_iterations and evaluate exit criteria rigorously
2. **Quality degradation**: Controller must validate that revisions actually improve output
3. **Over-refinement**: Some issues are stylistic or minor — don't chase perfection on every detail
4. **Lost original intent**: Reasoner should preserve core elements that are working
5. **Disconnection from criteria**: Monitor must evaluate against external criteria, not moving goalposts

## Verification

1. **Convergence test**: Run on a known multi-issue input — verify loop terminates at quality threshold, not max iterations
2. **Quality regression test**: Start with a low-quality input, verify each cycle improves rather than degrades
3. **Stability test**: On a high-quality input, verify loop exits immediately with no changes
4. **Integration test**: Verify metacognitive-mro-prompts compose correctly at loop boundaries
