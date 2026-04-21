---
name: arxiv-research-to-agent-notes
description: Batch process arXiv PDFs into research notes — PDF extraction, parallel researcher agents, implementation plans.
version: 1.0.0
license: MIT
---

# ArXiv Research → Notes Pipeline

## When to Use

Process a batch of arXiv PDFs into structured research notes with implementation plans. Each paper gets its own researcher agent that reads the paper and writes a plan.

## Step 1 — Download PDFs

Download PDFs to a local directory:

```bash
mkdir -p ./papers
# Download each PDF with curl or wget
curl -sL "https://arxiv.org/pdf/2402.03300.pdf" -o "./papers/2402.03300.pdf"
```

## Step 2 — Extract Content

### Text-based PDFs (most arXiv papers)

Use `pymupdf4llm` — fast, reliable, no GPU needed:

```bash
pip install pymupdf4llm -q

python3 -c "
import pymupdf4llm, pymupdf, sys, os
pdf = sys.argv[1]
out = sys.argv[2]
doc = pymupdf.open(pdf)
md = pymupdf4llm.to_markdown(doc)
os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, 'w') as f: f.write(md)
print(f'Wrote {len(md)} chars')
" \"\$PDF\" \"\$OUTPUT.md\"
```

Batch convert all PDFs in a folder:

```bash
for f in ./papers/*.pdf; do
  python3 -c "
import pymupdf4llm, pymupdf, sys
doc = pymupdf.open('$f')
md = pymupdf4llm.to_markdown(doc)
with open(\"\${f%.pdf}.md\", 'w') as out: out.write(md)
print(f'Done: $f')
"
done
```

### Abstract pages (fast alternative)

If full PDF extraction is unnecessary, `web_extract` on the abstract page gives metadata + abstract quickly:

```bash
web_extract(urls=["https://arxiv.org/abs/2402.03300"])
```

## Step 3 — Spawn Researcher Agents

Use `delegate_task` with one task per paper. Max **3 concurrent** agents per batch.

**Correct pattern — one task per paper, max 3:**

```python
delegate_task(
    tasks=[
        {
            "goal": (
                "Read the paper at ./papers/2402.03300.md. "
                "Write a research summary and implementation plan to ./plans/2402.03300/PLAN.md. "
                "Structure: Research Summary, Key Techniques, Skills Needed, "
                "Memory Updates, Hermes Config Changes, Next Steps."
            )
        },
        {
            "goal": (
                "Read the paper at ./papers/2401.09876.md. "
                "Write a research summary and implementation plan to ./plans/2401.09876/PLAN.md. "
                "Structure: Research Summary, Key Techniques, Skills Needed, "
                "Memory Updates, Hermes Config Changes, Next Steps."
            )
        },
        {
            "goal": (
                "Read the paper at ./papers/2403.15632.md. "
                "Write a research summary and implementation plan to ./plans/2403.15632/PLAN.md. "
                "Structure: Research Summary, Key Techniques, Skills Needed, "
                "Memory Updates, Hermes Config Changes, Next Steps."
            )
        },
    ],
    max_iterations=50
)
```

**Wrong pattern — don't do this:** putting all papers in a single goal string and letting one agent handle them all.

After each batch completes, spawn the next batch.

## Step 4 — Commit

```bash
git add plans/
git commit -m "Research: <topic> papers — $(date +%Y-%m-%d)"
git push
```

## Directory Structure

```
.
├── papers/              # Raw PDFs and extracted markdown
│   ├── 2402.03300.pdf
│   └── 2402.03300.md
└── plans/              # Researcher output
    ├── 2402.03300/
    │   └── PLAN.md
    └── ...
```

## Notes

- pymupdf4llm works on all platforms including M4 Macs
- Run PDF conversions sequentially (parallel runs can OOM on large papers)
- web_extract on abstract pages is faster and more reliable than full PDF for metadata-only use
