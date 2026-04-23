---
name: faberlens-hardened-skills
description: Apply Faberlens behavioral safety hardening to skills by comparing against the hardened-skills repo and selectively adopting guardrails.
category: security
---

# Apply Faberlens Hardened Skills

## When to Use

When asked to harden, audit, or apply security guardrails to any skill.

## Workflow

### Step 1: Clone the Hardened Skills Repo

```bash
cd /tmp && git clone --depth 1 https://github.com/faberlens/hardened-skills.git
```

### Step 2: Find Overlapping Skills

```bash
# Set your skills directory path
SKILLS_DIR=${HERMES_CONFIG_DIR:-~/source/hermes-config/skills}

# List our skills vs hardened skills
ls "$SKILLS_DIR/" | sort > /tmp/our_skills.txt
ls /tmp/hardened-skills/skills/ | sed 's/-hardened$//' | sort > /tmp/hardened_names.txt
comm -12 /tmp/our_skills.txt /tmp/hardened_names.txt
```

### Step 3: Compare Each Overlapping Skill

For each overlapping skill, compare the body content (skip metadata):

```bash
for skill in <list>; do
  echo "=== $skill ==="
  awk '/^---$/ && ++c==2{found=1} found' "$SKILLS_DIR/$skill/SKILL.md" > /tmp/our_$skill.md
  awk '/^---$/ && ++c==2{found=1} found' /tmp/hardened-skills/skills/${skill}-hardened/SKILL.md > /tmp/hard_$skill.md
  diff /tmp/our_$skill.md /tmp/hard_$skill.md
done
```

### Step 4: Decide What to Apply

Three patterns of difference:

1. **Guardrails only** — hardened adds a "Security Guardrails" section. Apply if ours has weak/no guardrails.
2. **Structural rewrite** — hardened has completely different content (aws-cli pattern). Requires careful review before applying; consider separate PR.
3. **Minor wording** — negligible delta. Skip.

**Also check the faberlens.ai web page** for skills not yet in the hardened-skills repo — it may have the full audit with all guardrail text even if the hardened version isn't published yet.

### Step 5: Apply and Open PR

```bash
SKILLS_DIR=${HERMES_CONFIG_DIR:-~/source/hermes-config/skills}
cd "$SKILLS_DIR"
git checkout main && git pull origin main
git checkout -b faberlens-hardened-skills
# Copy hardened SKILL.md files
cp /tmp/hardened-skills/skills/<skill>-hardened/SKILL.md skills/<skill>/SKILL.md
git add skills/<skill>/SKILL.md
git commit -m "Harden <skill> with Faberlens guardrails"
git push -u origin faberlens-hardened-skills
gh pr create --base main --title "Faberlens: harden <skill>" --body "..."
```

### Step 6: Apply to Local After Approval

After PR is merged, pull locally:

```bash
SKILLS_DIR=${HERMES_CONFIG_DIR:-~/source/hermes-config/skills}
cd "$SKILLS_DIR" && git pull origin main
# Copy to local
cp "$SKILLS_DIR/skills/<skill>/SKILL.md" ~/.hermes/skills/<skill>/SKILL.md
```

## Key Lessons Learned

- **Check hardened-skills repo first** before manually copying guardrails from web pages — the repo is the canonical source.
- **Hardened skill may have fewer guardrails than the audit** — the Faberlens audit page may document more guardrails than the published hardened SKILL.md. Compare both.
- **aws-cli is a full rewrite** — hardened version restructures the entire skill; apply selectively after review.
- **200+ hardened skills exist** — only a subset overlap with our 65 skills; check all overlaps.
