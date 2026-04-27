---
name: arxiv-research-to-agent-notes
description: Process arXiv PDFs into Hermes agent-notes — pymupdf4llm conversion, spawn 1 researcher per paper, max 3 concurrent, commit plans immediately.
related_skills:
  - research-paper-to-agent-plan  # deprecated, merged into this skill
  - marker-pdf-conversion         # platform-specific PDF extraction guidance
---

# ArXiv Research → Agent Notes Pipeline

## When to Use
Process arXiv PDFs into Hermes agent-notes with researcher sub-agents writing implementation plans.

## Steps

### 1. Archive PDFs
Download PDFs to `<AGENT_NOTES>/arxiv-pdfs/`.
```bash
mkdir -p <AGENT_NOTES>/arxiv-pdfs
# Download each PDF with curl/wget
```

### 2. Extract Content
- **Primary**: `web_extract` on arXiv abstract page (more reliable than marker)
  - URL pattern: `https://arxiv.org/abs/XXXXX.XXXXX` → extract abstract
  - Then download the HTML for additional metadata
- **Fallback**: `marker.single` on PDF for full text extraction
  - Resource-heavy; run sequentially, not in parallel
  - Activate venv first: `source ~/.venv/marker/bin/activate`
  - Run with: `marker.single /path/to/pdf --output_dir /path/to/output --output_format markdown`

## Spawn Researchers: delegate_task with tasks=[] (one paper per task, max 3 concurrent)

Use `delegate_task` with the `tasks` array — one task entry per paper. Each sub-agent gets ONE paper. Max 3 concurrent.

⚠️ Common mistake: put all papers in a single `goal` string and let one agent handle them all. Correct pattern:

```python
delegate_task(
    tasks=[
        {"goal": "Read paper A. Write plan to <AGENT_NOTES>/projects/slug-a/PLAN.md"},
        {"goal": "Read paper B. Write plan to <AGENT_NOTES>/projects/slug-b/PLAN.md"},
        {"goal": "Read paper C. Write plan to <AGENT_NOTES>/projects/slug-c/PLAN.md"},
    ],
    max_iterations=50
)
```

Each task gets its own sub-agent with isolated context. Max 3 per batch.

### Project Folder Naming
Use `<topic-slug>-YYYY-MM/` format for project folders, e.g., `skill-improvement-2026-04/`.

### Researcher Output Structure
Each researcher sub-agent writes:
- `PLAN.md` to the project folder — structure: **Research Summary, Skills, Memory, Hermes Config/SOUL Changes, Next Steps**
- `notes/<paper-id>.md` with paper notes

After all researchers finish:
```bash
cd <AGENT_NOTES>
git add projects/<new-folders>
git commit -m "Research: <topic> papers"
git push
```

## Known Issues
- Marker parallel runs fail; run sequentially on Linux/CUDA only
- Marker venv activation needed before use on Linux
- Marker FAILS on M4 Macs — use pymupdf4llm instead (see marker-pdf-conversion skill)
- web_extract on abstract pages is faster and more reliable than full PDF extraction

