# Prompt Templates for embodied_agent_planning

| File | When to Use | Inputs | Outputs |
|------|-------------|--------|---------|
| template_a_si_gated.md | Before planning begins | plan request | SI risk level, danger score, gate decision |
| template_b_revision_failed.md | After failed SI/feasibility check | failure report, original plan | revised plan |
| template_c_escalation.md | After BLOCKED (3) or irreversible action | escalation context | human-readable brief |
