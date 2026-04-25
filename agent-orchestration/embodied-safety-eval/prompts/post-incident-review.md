## Post-Incident Embodied Safety Review

A safety incident occurred during plan execution. Conduct a structured review.

---

### Incident Summary

**INCIDENT_DESCRIPTION:** `<what happened>`

**PLAN_AT_TIME_OF_INCIDENT:**
```
<plan steps>
```

**ENVIRONMENT_STATE_AT_INCIDENT:** `<what the environment looked like at the time>`

**AGENT_SENSING_AT_INCIDENT:** `<what the agent perceived immediately before the incident>`

---

## Contributing Factor Analysis

### 1. Sensing Failure
Did the agent perceive the environment correctly?

**SENSING_STATUS:** `<ADEQUATE|INADEQUATE|FAILED>`
**SENSING_FAILURE_MODE:** `<description of what was misperceived or not detected>`

### 2. Model Failure
Did the agent's internal model of the environment match reality?

**MODEL_STATUS:** `<ACCURATE|INACCURATE|FAILED>`
**MODEL_FAILURE_MODE:** `<description of incorrect assumptions or predictions>`

### 3. Planning Failure
Was the plan appropriate for the perceived environment?

**PLANNING_STATUS:** `<ADEQUATE|INADEQUATE|FAILED>`
**PLANNING_FAILURE_MODE:** `<description of plan inappropriate for situation>`

### 4. Execution Failure
Did the plan match the intended actions?

**EXECUTION_STATUS:** `<FAITHFUL|DEVIATED|FAILED>`
**EXECUTION_FAILURE_MODE:** `<description of discrepancy between plan and action>`

### 5. Human Factors
Did human oversight or instructions contribute?

**HUMAN_FACTORS:** `<CONTRIBUTING|NOT_CONTRIBUTING|UNKNOWN>`
**HUMAN_FACTOR_DESCRIPTION:** `<how human actions or inactions contributed>`

### 6. Environmental Factors
Did unexpected environmental conditions contribute?

**ENVIRONMENTAL_FACTORS:** `<CONTRIBUTING|NOT_CONTRIBUTING|UNKNOWN>`
**ENVIRONMENTAL_FACTOR_DESCRIPTION:** `<unexpected conditions that contributed>`

---

## Root Cause Analysis

**ROOT_CAUSE:** `<most fundamental cause among above categories>`
**ROOT_CAUSE_CONFIDENCE:** `<HIGH|MEDIUM|LOW>`

---

## Safety Improvements Required

| Category | Improvement Required | Priority |
|----------|---------------------|----------|
| **Sensing** | `<specific improvement to perception>` | `<HIGH|MEDIUM|LOW>` |
| **Model** | `<specific improvement to world model>` | `<HIGH|MEDIUM|LOW>` |
| **Planning** | `<specific improvement to planning or plan safety evaluation>` | `<HIGH|MEDIUM|LOW>` |
| **Execution** | `<specific improvement to execution fidelity>` | `<HIGH|MEDIUM|LOW>` |
| **Protocol** | `<specific improvement to human oversight or interaction protocols>` | `<HIGH|MEDIUM|LOW>` |

---

## Plan Approval Status

**PLAN_APPROVAL_STATUS:** `<RE-APPROVED|REQUIRES_REVISION|SUSPENDED>`

**REAPPROVAL_CONDITIONS:** `<what must be satisfied for re-approval>`

---

## Lessons Learned

**GENERALIZABLE_LESSONS:**
1. `<lesson 1>`
2. `<lesson 2>`
3. `<lesson 3>`

**UPDATED_SAFETY_CHECKLIST:**
- [ ] `<safety check item added based on incident>`
- [ ] `<safety check item added based on incident>`
- [ ] `<safety check item added based on incident>`

---

## Related Incidents

Reference any similar past incidents for cross-analysis:

| Incident ID | Similarity | Key Difference |
|-------------|------------|----------------|
| `<ID>` | `<how similar>` | `<key difference>` |

---

## PDDL Safety Constraint Update (for `run_eval.py`)

Based on this incident, update safety constraints to prevent recurrence:

```pddl
;; New safety constraint derived from incident
(:constraint prevent_<incident_type>
 :parameters (?a - agent ?s - state)
 :condition (and
    (not (hazardous ?s))
    (monitoring_active ?a))
 :effect (safe_action ?a))
```
