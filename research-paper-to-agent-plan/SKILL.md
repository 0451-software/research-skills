---
name: research-paper-to-agent-plan
description: Convert research PDFs to markdown, then delegate to researcher sub-agents to produce implementation plans. Use when papers need to be ingested and translated into actionable plans for an agent team.
version: 1.0.0
license: MIT
---

# Research Paper → Agent Plan Pipeline

## When to Use

Convert research PDFs to markdown, then spawn researcher sub-agents (one per paper) to read them and produce implementation plans. Used to bootstrap a body of in-progress plans from a research corpus.

## Step 1 — Convert PDFs to Markdown

### Text-based, digitally-generated PDFs

On most systems, `pymupdf4llm` is the fastest and most reliable choice for cleanly extracted PDFs:

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
" "$PDF" "$OUTPUT.md"
```

Batch convert:

```bash
for f in ./research-pdfs/*.pdf; do
  python3 -c "
import pymupdf4llm, pymupdf, sys
doc = pymupdf.open('$f')
md = pymupdf4llm.to_markdown(doc)
with open('${f%.pdf}.md', 'w') as out: out.write(md)
"
done
```

### Scanned PDFs or papers with heavy LaTeX equations

Use [Marker](https://github.com/VikParuchuri/marker) when better OCR or LaTeX fidelity is required. Marker needs a CUDA-capable Linux machine to run at full speed:

```bash
uvx --from marker-pdf[all] marker_single /path/to/paper.pdf \
  --output_dir ./output \
  --output_format markdown \
  --disable_image_extraction
```

Marker produces superior LaTeX rendering and handles scanned documents where `pymupdf4llm` would return empty text.

### File-size guidance

- **Under 50 MB total** (small corpus): `pymupdf4llm` is fine. Sequential is safe.
- **Hundreds of PDFs or large files**: convert sequentially, not in parallel — `pymupdf4llm` and `marker` are memory-hungry and concurrent runs can OOM.

## Step 2 — Spawn Researcher Sub-Agents

Delegate using a **researcher persona**. Each sub-agent reads one paper markdown and writes an implementation plan.

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

Conventions:
- **Max concurrency** — batch up to 3 sub-agents at a time. Plan files are tiny, but reading + planning is the bottleneck.
- **Plan folder naming** — `<topic-slug>-YYYY-MM/`
- **Output format** — markdown outline with the agreed sections, written to a path inside `plans/`.

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

- If using the arXiv API, download PDFs with: `curl -sL "https://arxiv.org/pdf/{id}.pdf" -o "{id}.pdf"`
- Run PDF conversions sequentially, not in parallel, to avoid memory pressure.
- For very large corpora, consider chunking the conversion into overnight batches.
