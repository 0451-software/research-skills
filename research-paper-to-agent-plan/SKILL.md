---
name: research-paper-to-agent-plan
description: Convert research PDFs to markdown, spawn researcher sub-agents, produce implementation plans.
version: 1.0.0
license: MIT
---

# Research Paper → Agent Plan Pipeline

## When to Use

Convert research PDFs to markdown, then spawn researcher agents to read them and produce implementation plans.

## Step 1 — Convert PDFs to Markdown

### M4 Mac / text-based PDFs

Use `pymupdf4llm` (marker fails on M4 Macs):

```bash
pip install pymupdf4llm -q

python3 -c "
import pymupdf4llm, pymupdf, sys, os
pdf_path = sys.argv[1]
out_path = sys.argv[2]
doc = pymupdf.open(pdf_path)
md = pymupdf4llm.to_markdown(doc)
os.makedirs(os.path.dirname(out_path), exist_ok=True)
with open(out_path, 'w') as f: f.write(md)
print(f'Wrote {len(md)} chars to {out_path}')
" \"\$PDF\" \"\$OUTPUT.md\"
```

Batch convert:

```bash
for f in ./research-pdfs/*.pdf; do
  python3 -c "
import pymupdf4llm, pymupdf, sys
doc = pymupdf.open('$f')
md = pymupdf4llm.to_markdown(doc)
with open('\${f%.pdf}.md', 'w') as out: out.write(md)
"
done
```

### Scanned PDFs or papers with LaTeX equations

Use [Marker](https://github.com/VikParuchuri/marker) on a Linux/CUDA machine:

```bash
uvx --from marker-pdf[all] marker_single /path/to/paper.pdf \
  --output_dir ./output \
  --output_format markdown \
  --disable_image_extraction
```

Marker produces superior LaTeX rendering and handles scanned documents.

## Step 2 — Spawn Researcher Agents

Spawn using a **researcher persona**. Each agent reads one paper markdown and writes an implementation plan.

**Max 3 concurrent.** Batch spawn, wait, repeat.

```python
delegate_task(
    tasks=[
        {
            "goal": (
                "Read the paper at ./papers/2402.03300.md. "
                "Write a detailed implementation plan to ./plans/2402.03300/PLAN.md. "
                "Structure: Research Summary, Key Techniques, "
                "Skills to Create or Update, Memory Notes, Next Steps."
            )
        },
    ],
    max_iterations=50
)
```

Plan folder naming: `<topic-slug>-YYYY-MM/`

## Step 3 — Commit

```bash
git add plans/
git commit -m "Research: <topic> papers — $(date +%Y-%m-%d)"
git push
```

## Directory Structure

```
.
├── research-pdfs/       # Source PDFs
│   └── paper.pdf
├── papers/              # Converted markdown
│   └── paper.md
└── plans/              # Researcher output
    └── <topic-slug>/
        └── PLAN.md
```

## Notes

- pymupdf4llm is the default on M4 Macs — marker OOMs
- Run PDF conversions sequentially, not in parallel
- If using the arXiv API, download PDFs with: `curl -sL "https://arxiv.org/pdf/{id}.pdf" -o "{id}.pdf"`
