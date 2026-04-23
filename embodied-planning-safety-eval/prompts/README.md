---
These prompts are not called directly. They are loaded by `embodied_agent_planning`
or by invoking the `embodied-planning-safety-eval` skill at runtime.
---

# Prompt Templates — embodied-planning-safety-eval

## Overview
These prompts are invoked by `embodied_agent_planning` after the SI gate passes.
Do not use them directly — they are loaded automatically when the safety skill is referenced.

## Templates

| File | When to Use | Inputs | Outputs |
|------|-------------|--------|---------|
| `pddl-safety-check.md` | Plans with formalizable preconditions (PDDL format) | domain.pddl, problem.pddl, plan | VALID/INVALID + safety flags |
| `pre-execution-safety.md` | Multi-agent coordination, shared resources | plan, agent roles, coordination points | coordination safety verdict |
| `post-incident-review.md` | After any safety-related failure | incident log, plan history, SI scores | structured review findings + recommendations |
