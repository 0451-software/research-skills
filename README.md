# Research Skills

AI research-grounded techniques and reusable agent orchestration patterns. Install via:

```bash
/plugin marketplace add https://github.com/0451-software/research-skills
```

## Research Techniques (root)

Skills grounded in published AI research and methodologies:

| Skill | Description |
|-------|-------------|
| `uncertainty-quantification-conactu` | CONACTU 4-axis uncertainty quantification for agent outputs |
| `embodied-agent-planning` | Embodied agent planning with integrated safety intention (SI) scoring and orthogonal feasibility+safety checks |
| `research-paper-to-agent-plan` | Convert research PDFs to plans via researcher sub-agents |

## Agent Orchestration (`agent-orchestration/`)

Agent scaffolding patterns — not grounded in published research but useful for multi-agent coordination:

| Skill | Description |
|-------|-------------|
| `agent-delegation-strategy` | When and how to delegate to persona sub-agents |
| `faberlens-hardened-skills` | Apply Faberlens behavioral safety hardening |
| `fantasia-aware-agent` | Fantasia-aware agent routing to prevent premature commitment to underspecified intent |
| `metacognitive-mro-prompts` | MRO self-awareness loops and bias detection |
| `persona-adversarial-review` | Red-team persona for failure mode analysis |
| `persona-engineer` | Implementation persona — ship working code |
| `persona-inspector` | QA/inspection persona — verification gate |
| `persona-researcher` | Research persona — deep dives and synthesis |
| `psmas-dag-to-phases` | PSMAS DAG → executable phases with validation |
| `safety-intention-checker` | Pre-action semantic safety evaluation |
| `self-refinement-loop` | MRO Monitor/Reasoner/Controller refinement loop |

## Adding a new skill

1. Create a directory under the appropriate section (root or `agent-orchestration/`).
2. Add a `SKILL.md` with YAML frontmatter (`name`, `description`) and a markdown body.
3. Register the plugin in `.claude-plugin/marketplace.json` so the marketplace can resolve it.

Pull requests should preserve the research-grounded scope of the repo. Skills that are workflow-specific, host-specific, or only useful to a single agent instance do not belong here.

## License

MIT
