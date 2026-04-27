---
name: trip-prep-research
description: "Comprehensive trip research pipeline: multi-agent research delegation, mobile-formatted output, and format linter. Use when given a trip plan task-list entry in agent-notes/task-lists/. Covers: project setup, parallel research waves, itinerary formatting, QA, and commit."
version: 1.0.0
license: MIT
---

# Trip Prep Research

Comprehensive trip research pipeline using multi-agent delegation, producing mobile-friendly markdown deliverables with QA.

## When to Use

- User says "plan a trip", "research [destination]", or pushes a new task-list entry to `task-lists/`
- Must read the task-list file first to extract: destination, dates, accommodation, preferences, constraints

## Pipeline Overview

```
You (parse task-list)
  └─ Wave 1 (parallel): research-agent × N topics
        └─ implementer → fixes → QA
  └─ Wave 2 (parallel): research-agent × remaining topics
  └─ Implementer → reformat itinerary → QA
  └─ You → commit + push
```

**Rule:** Start every wave/phase from `main + git pull origin main`. Never branch from stale local state.

---

## Step 1 — Parse the Task List

Read the task-list file. Extract:

| Field | Example |
|-------|---------|
| Destination | Singapore |
| Dates | June 15–25, 2026 |
| Accommodation | Marina Bay Sands |
| Preferences | Museums, botanical gardens, nature, architecture, jazz, fine dining, romantic activities |
| Constraints | Mobile/iPhone portrait format, Apple Maps links, no credentials |

Create project directory: `<AGENT_NOTES>/projects/[slug]/`

---

## Step 2 — Wave 1 Research (Parallel Agents)

Delegate **3–4 research agents in parallel**, each producing one markdown file.

**Delegation prompt template:**

```
CRITICAL: Do NOT run git init. Do NOT run git status. Do NOT run git log. Do NOT use cd. Write files only to the path specified. Verify each file exists at the target path before reporting done.

Goal: Research [TOPIC] for a trip to [DESTINATION], [DATES]. Staying at [ACCOMMODATION].

Preferences: [PREFERENCES]
Constraints: Mobile/iPhone portrait format, Apple Maps walking/transit links, no credentials.

Output file: <AGENT_NOTES>/projects/[SLUG]/[FILENAME].md

Research [TOPIC] thoroughly. Cover:
- [TOPIC-SPECIFIC SECTIONS]
- Include Apple Maps direction links where applicable
- Flag romantic/[SPECIAL OCCASION] items
- Note booking windows and urgency
```

**Typical Wave 1 topics (delegate in parallel):**

| File | Topics |
|------|--------|
| `food.md` | Breakfast, lunch, dinner, snacks — Michelin-star through hawker. Include 11-day dining schedule. |
| `daytime-activities.md` | Museums, gardens, nature reserves, architecture walks, daytime attractions |
| `nighttime-activities.md` | Jazz clubs, rooftop bars, cultural performances, evening attractions |
| `packing-prep.md` | Weather, packing list, plug types, transport cards, dining etiquette, eSIM |

**After Wave 1:** Commit with message `"Research: [Destination] trip - food, daytime activities, nightlife, packing prep"`

### Verify files after every wave

**Always run after sub-agents return — before committing:**

```bash
ls <AGENT_NOTES>/projects/[SLUG]/
python3 <path-to-trip-prep-linter> <AGENT_NOTES>/projects/[SLUG]/itinerary.md
```

If files are missing: create them directly (faster than re-delegating). If linter fails: fix and re-run until clean. Do not commit until both pass.

---

## Step 3 — Wave 2 Research (Parallel Agents)

**Delegation prompt template:**

```
CRITICAL: Do NOT run git init. Do NOT run git status. Do NOT run git log. Do NOT use cd. Write files only to the path specified. Verify each file exists at the target path before reporting done.

Goal: Research [TOPIC] for a trip to [DESTINATION], [DATES]. Staying at [ACCOMMODATION].

Preferences: [PREFERENCES]
Constraints: Mobile/iPhone portrait format, Apple Maps walking/transit links, no credentials.

Output file: <AGENT_NOTES>/projects/[SLUG]/[FILENAME].md

Research [TOPIC] thoroughly. Cover:
- [TOPIC-SPECIFIC SECTIONS]
- Use [ROMANTIC] and [SPECIAL OCCASION] tags for relevant items
```

**Typical Wave 2 topics (delegate in parallel):**

| File | Topics |
|------|--------|
| `romantic.md` | Sunset spots, private dining, couples spa, romantic rooftops, special events during dates |
| `reservations.md` | All venues requiring advance booking, grouped by urgency (most urgent first), phone + URL |
| `itinerary.md` | Day-by-day master itinerary × 6 time slots, 2–3 choices per slot, fixed reservations flagged with ⚠️ TODO |

**After Wave 2:** Commit with message `"Add: [Destination] trip - romantic activities, reservations checklist, master itinerary"`

---

## Step 4 — Reformat Itinerary (Implementer)

The itinerary is the most格式-sensitive file. Dispatch an implementer with this exact format spec:

**MOBILE ITINERARY FORMAT (mandatory):**

```markdown
### Morning

**Venue Name** [optional-tag]
- description
- *Why: reason*
- [📍 Directions](https://maps.apple.com/?daddr=VENUE+NAME&dirflg=[w|r])

**Venue Name 2** [optional-tag]
- description
- *Why: reason*
- [📍 Directions](https://maps.apple.com/?daddr=VENUE+NAME&dirflg=[w|r])
```

**Rules:**
- Blank line between venue blocks
- `**Bold Name**` at line start — nothing before it except blank line
- Sub-items are `-` bullets, indented 2 spaces
- `*Why:` lines in *italics*
- Directions link uses Apple Maps format:
  - Walking: `https://maps.apple.com/?daddr=VENUE+NAME&dirflg=w`
  - Transit: `https://maps.apple.com/?daddr=VENUE+NAME&dirflg=r`
- `⚠️ TODO:` prefix for items needing reservation
- `[ROMANTIC]` or `[SPECIAL OCCASION]` inline after venue name
- **NO** `[Choice A/B/C]` labels — user picks from the list
- Day headers use `### Morning`, `### Lunch`, `### Afternoon`, `### Evening`

**Implementer prompt:**

```
CRITICAL: Do NOT run git init. Do NOT run git status. Do NOT use cd. Write files only to the path specified. Verify the file exists at the target path before reporting done.

Read <AGENT_NOTES>/projects/[SLUG]/itinerary.md

Rewrite it completely in the mobile itinerary format described above. Every venue must follow:
**Venue Name** [optional-tags]
- description
- *Why: reason*
- [📍 Directions](https://maps.apple.com/?daddr=VENUE+NAME&dirflg=[w|r])

Key rules:
- Bold name at line start, nothing before it except blank line
- Sub-items are - indented bullets
- No [Choice A/B/C] labels
- ⚠️ TODO: prefix for reservation-needed items
- [ROMANTIC] / [SPECIAL OCCASION] inline after name
- Apple Maps direction links (walking w or transit r)

Write the corrected file to <AGENT_NOTES>/projects/[SLUG]/itinerary.md

---

## PHASE BOUNDARY — MANDATORY COMPLETION CHECK

After completing the above rewrite, you MUST verify the file is fully done before reporting completion:

1. **Venue count:** Does every slot have the expected number of venues?
2. **Bullet sub-items:** Does each venue have ≥2 bullet sub-items?
3. **Mobile format:** No mix of old/new format — re-read a random sample of 10 venues
4. **No [Choice A/B/C] labels:** Search for any remaining labels
5. **Time-block headers:** Are all Day/DATE headers present?
6. **Directions links:** Does every venue have an Apple Maps direction link?

**If ANY check fails OR if you are uncertain about any venue:**
→ Do NOT report "done"
→ Instead, report exactly what remains: "REMAINING WORK: [description of what's left]"
→ The parent agent will dispatch another implementer to complete the remaining work before moving on.

**Only report "done" when all 6 checks pass cleanly.**

This prevents the recurring issue: "The implementer fixed P0/P1 issues but didn't finish the mobile reformatting — the file has a mix of old and new formats."
```

---

## Step 5 — QA (Inspector Persona)

Dispatch a `persona-inspector` sub-agent:

```
Final QA of <AGENT_NOTES>/projects/[SLUG]/itinerary.md

Read the file. Check:
1. FORMAT: every item follows **Bold Name** + indented - bullets pattern
2. No orphaned bold names without bullet sub-items
3. No missing Apple Maps direction links
4. [ROMANTIC] / [SPECIAL OCCASION] flags on appropriate venues
5. ⚠️ TODO: on venues needing reservations
6. No [Choice A/B/C] labels
7. Day headers are ### Morning / ### Lunch / ### Afternoon / ### Evening

Report: list any format violations by line number. Do NOT editorialize — just report.
```

---

## Step 6 — Commit and Push

```bash
cd <AGENT_NOTES>
git add -A
git commit -m "QA + fixes: [Destination] trip - reformat itinerary mobile, fix P0/P1 issues"
git push origin main
```

---

## Markdown Format Linter (Trip Prep)

Run after any itinerary edit to catch format violations before committing. Saved at `<TRIP_PREP_LINTER>` and also bundled in `references/trip_prep_linter.py`.

**Critical markdown bold rules the linter enforces:**
- `**Venue Name**` — valid (properly closed)
- `**Venue Name:**` — valid (properly closed, with trailing colon)
- `**Venue Name` — invalid (never closed)
- `**text** + inline content` — invalid (bold must close before any inline content)

The linter skips everything before the first `## Day` header (the metadata block: Base, Dates, Purpose) so header metadata does not trigger false positives.

**Checks performed:**
1. Bold lines have matching closing `**`
2. Bold lines are followed by ≥2 indented `-` bullet sub-items
3. No `[Choice A/B/C]` labels in venue blocks
4. Direction links contain `maps.apple.com` and `&dirflg=`

```python
#!/usr/bin/env python3
"""trip_prep_linter.py — validates mobile trip itinerary format."""

import re
import sys

def lint_itinerary(path: str) -> list[str]:
    with open(path) as f:
        lines = f.readlines()

    errors = []
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        # Skip blank lines and day headers
        if not line or line.startswith('#') or line.startswith('### '):
            i += 1
            continue

        # Bold name line must start with ** and be followed by bullets
        if line.startswith('**') and not line.startswith('** '):
            errors.append(f"Line {i+1}: Bold name missing space after **: {line}")
        elif line.startswith('**'):
            # Check next non-blank line is a bullet
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines) and not lines[j].strip().startswith('- '):
                errors.append(f"Line {i+1}: Bold name not followed by bullet sub-items: {line}")
            # Check bullets have proper structure
            bullet_count = 0
            while j < len(lines) and lines[j].strip().startswith('- '):
                bullet_count += 1
                bullet_text = lines[j].strip()[2:]
                # description bullet (not *Why:)
                if not bullet_text.startswith('*Why:') and not bullet_text.startswith('[📍'):
                    pass  # description ok
                j += 1
            if bullet_count < 2:
                errors.append(f"Line {i+1}: Venue has fewer than 2 bullet sub-items: {line}")
        i += 1

    return errors

if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else 'itinerary.md'
    errs = lint_itinerary(path)
    if errs:
        print(f"FORMAT ERRORS ({len(errs)}):")
        for e in errs:
            print(f"  {e}")
        sys.exit(1)
    else:
        print("OK — format valid")
```

Save as `<TRIP_PREP_LINTER>` and run:

```bash
python3 <path-to-trip-prep-linter> <AGENT_NOTES>/projects/[SLUG]/itinerary.md
```

---

## Apple Maps Link Formula

| Transport mode | URL pattern |
|----------------|-------------|
| Walking | `https://maps.apple.com/?daddr=VENUE+NAME&dirflg=w` |
| Transit | `https://maps.apple.com/?daddr=VENUE+NAME&dirflg=r` |
| Driving | `https://maps.apple.com/?daddr=VENUE+NAME&dirflg=d` |

Replace spaces with `+` in venue names. Test links in browser before committing.

---

## Output File Template (Itinerary)

```markdown
# [Destination] Trip — [Month Year]

**Dates:** [DATES]
**Staying at:** [ACCOMMODATION]
**Preferences:** [PREFERENCES]

---

## Day 1 — [Date, Day of Week]

### Morning

**Venue Name** [ROMANTIC]
- description
- *Why: reason*
- [📍 Directions](https://maps.apple.com/?daddr=VENUE+NAME&dirflg=w)

### Lunch

**Venue Name**
- description
- *Why: reason*
- [📍 Directions](https://maps.apple.com/?daddr=VENUE+NAME&dirflg=r)

...and so on for each day and time slot.
```

---

## Booking Urgency Hierarchy (for reservations.md)

When sorting reservations by urgency:

1. **Most urgent** — 100+ day booking window (3-star Michelin, limited seating)
2. **60-day window** — 2-star Michelin, popular restaurants
3. **30-day window** — 1-star, popular attractions
4. **7–14 days** — Gardens by the Bay conservatories, popular shows
5. **Walk-in ok** — Hawker stalls, most museums

Include phone numbers and booking URLs for every venue.

---

## Common Pitfalls

| Pitfall | Prevention |
|---------|------------|
| Wrong bullet indent (1 space instead of 2) | Linter catches this — run after every itinerary edit |
| `[Choice A/B/C]` labels in itinerary | Linter removes; implementer reformat fixes |
| Missing `[ROMANTIC]` on obviously romantic venues | QA catches; editorialize sparingly |
| Garden Rhapsody wrong show for dates | Check show end dates — World of Fantasy ends ~June 21, Journey through Asia starts June 22 |
| 3-star restaurant window missed | Zén and comparable need 100-day window tracked from day 1 |
| Credentials in files | Never use real names, card numbers, or booking confirmations |
| Bold names flagged as invalid by linter | `**Venue Name**` and `**Venue Name:**` are both valid — check for proper `**` closure, not a required space after opening `**` |
