---
name: research-paper-to-agent-plan
description: DEPRECATED — use arxiv-research-to-agent-notes instead. Convert research PDFs to markdown (pymupdf4llm, not marker on M4), spawn researcher sub-agents, commit plans to agent-notes
---

> ⚠️ **DEPRECATED**: This skill is deprecated. All functionality has been merged into `arxiv-research-to-agent-notes`. Please use that skill instead.

# Research Paper to Agent Plan Pipeline (Deprecated)

## Use When
Converting research PDFs to markdown, then spawning sub-agents to read them and produce implementation plans for skills/memory/Hermes config.

## Step 1 — Convert PDFs (M4 Mac workaround)

**marker-pdf is broken on M4 Macs** — OOM killed, filetype errors. Use `pymupdf4llm` instead.

```bash
# Convert a single PDF to markdown
python3 -c "
import pymupdf4llm
import pymupdf
import sys, os

pdf_path = sys.argv[1]
out_path = sys.argv[2]
doc = pymupdf.open(pdf_path)
md = pymupdf4llm.to_markdown(doc)
os.makedirs(os.path.dirname(out_path), exist_ok=True)
with open(out_path, 'w') as f:
    f.write(md)
print(f'Wrote {len(md)} chars to {out_path}')
" "$PDF" "$OUTPUT.md"
```


## Step 2 — Spawn Researchers (3 concurrent max)

Spawn using the **researcher persona** (`persona-researcher`). Each agent:
- Reads 1 paper (1 markdown file)
- Writes 1 `PLAN.md` to `<AGENT_NOTES>/projects/<project-folder>/PLAN.md`
- Also writes a `notes/<paper-id>.md` with paper notes
- Structure: Research Summary, Skills, Memory, Hermes Config/SOUL Changes, Next Steps

```bash
# Batch spawn 3 at a time (one per paper)
# Wait for batch to complete, then spawn next batch
```

Project folder naming: `<topic-slug>-YYYY-MM/`

## Step 3 — Commit

```bash
cd <AGENT_NOTES>
git add projects/<folder-1> projects/<folder-2> projects/<folder-3>
git commit -m "research: <topic> papers - $(date +%Y-%m-%d)"
git push
```

