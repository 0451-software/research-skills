---
name: trip-prep-research
description: "Comprehensive trip research pipeline: multi-agent research delegation, mobile-formatted output, and format linter. Use when given a trip plan task-list entry in agent-notes/task-lists/. Covers: project setup, parallel research waves, itinerary formatting, QA, and commit."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [research, travel, multi-agent, delegation, markdown, qa]
    related_skills: [agent-delegation-strategy, two-wave-research-delegation, subagent-driven-development]
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

Create project directory: `~/source/agent-notes/projects/[slug]/`

---

## Step 2 — Wave 1 Research (Parallel Agents)

Delegate **3–4 research agents in parallel**, each producing one markdown file.

**Delegation prompt template:**

```
Goal: Research [TOPIC] for a trip to [DESTINATION], [DATES]. Staying at [ACCOMMODATION].

Preferences: [PREFERENCES]
Constraints: Mobile/iPhone portrait format, Apple Maps walking/transit links, no credentials.

Output file: ~/source/agent-notes/projects/[SLUG]/[FILENAME].md

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

---

## Step 3 — Wave 2 Research (Parallel Agents)

**Delegation prompt template:**

```
Goal: Research [TOPIC] for a trip to [DESTINATION], [DATES]. Staying at [ACCOMMODATION].

Preferences: [PREFERENCES]
Constraints: Mobile/iPhone portrait format, Apple Maps walking/transit links, no credentials.

Output file: ~/source/agent-notes/projects/[SLUG]/[FILENAME].md

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

The itinerary is the most format-sensitive file. Dispatch an implementer with this exact format spec:

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
Read ~/source/agent-notes/projects/[SLUG]/itinerary.md

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

Write the corrected file to ~/source/agent-notes/projects/[SLUG]/itinerary.md
```

---

## Step 5 — QA (Inspector Persona)

Dispatch a `persona-inspector` sub-agent:

```
Final QA of ~/source/agent-notes/projects/[SLUG]/itinerary.md

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

## Step 6 — Run Format Linter

After QA, run the linter to catch any remaining issues before committing:

```bash
python3 ~/.local/bin/trip_prep_linter.py ~/source/agent-notes/projects/[SLUG]/itinerary.md
```

Fix any errors it reports before proceeding to commit.

---

## Step 7 — Commit and Push

```bash
cd ~/source/agent-notes
git add -A
git commit -m "QA + fixes: [Destination] trip - reformat itinerary mobile, fix P0/P1 issues"
git push origin main
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
