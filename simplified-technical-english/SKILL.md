---
name: simplified-technical-english
description: "Rewrite English text in ASD-STE100 Simplified Technical English style — one meaning per word, active voice, simple tense, short sentences, one instruction per sentence. Use when the user asks to simplify, clarify, rewrite in STE, apply STE100, remove ambiguity, or asks for a before/after rewrite. Also use when producing agent-facing text — tool descriptions, error messages, inter-agent instructions — where misparsing has a real cost."
version: 1.0.0
author:
license: MIT
category: writing
tags: [writing, clarity, technical-writing, controlled-language, asd-ste100]
---

# Simplified Technical English (ASD-STE100)

## What This Skill Does

You rewrite English text so a downstream agent — or a non-native English reader, or a translation pipeline — cannot misread it. The rewrite follows ASD-STE100 Issue 9 (Jan 2025), the controlled-language standard the aerospace and defense industry built so maintenance technicians cannot misread an instruction.

STE exists because a misread instruction on an aircraft can kill people, and the readers often have no author to call. An agent parsing another agent's output is in the same position: no back-channel to ask "did you mean X or Y?"

## When to Use

Use this skill when any of the following is true:

- The user says **simplify**, **clarify**, **rewrite in STE**, **apply STE100**, **remove ambiguity**, **unambiguous**, **make this parseable**, **plain English**.
- The output will be read by another agent, a tool, a parser, or a translation pipeline — not a human who can ask a follow-up.
- You are writing an error message, tool description, system prompt, or inter-agent instruction and want to remove ambiguity before another model sees it.
- The user pastes a paragraph and asks for a **before/after** rewrite showing which rule was violated.

**Do not use** this skill for creative writing, marketing copy, jokes, or any text where voice, nuance, or persuasion is the point. STE is deliberately flat and literal. A request to "make this funnier" or "write a tagline" is the opposite of STE.

## Core Rules

| Rule | Do | Don't |
|---|---|---|
| One word, one meaning | Pick one verb for one action. Use the same verb every time. | Rotate synonyms for the same idea across a paragraph. |
| One part of speech per word | "Apply oil to the valve" (oil = noun). | "Oil the valve" (oil = verb) when "oil" is only approved as a noun. |
| Active voice | "The agent deletes the file." | "The file is deleted." — unless the actor is genuinely unknown or irrelevant. |
| Simple tenses only | "We received the report." (simple past) | "We have received the report." (present perfect) |
| One instruction per sentence | "Open the file. Read line 3." | "Open the file and read line 3, then check if it matches." |
| Sentence length | ≤20 words for procedures. ≤25 words for descriptions. | Long compound/subordinate-clause sentences. |
| Noun clusters | ≤3 nouns stacked ("fuel pump valve"). | 4+ nouns stacked ("high pressure fuel pump inlet valve assembly"). |
| No ellipsis | Keep the subject, verb, and article explicit. | Drop words to save space — STE warns this creates ambiguity rather than clarity. |
| One topic per paragraph | ≤6 sentences per paragraph. | Multi-topic paragraphs. |
| Lists for sequences | Use a numbered or bulleted list for 3+ steps or conditions. | Bury a sequence inside one prose sentence. |
| Safety first | Safety-critical instructions open with a clear command or condition. | Bury warnings mid-sentence. |

Full rule summary and citations: see `references/writing-rules.md`.

## Process

1. Read the input text once for meaning. Do not start rewriting before you understand what it must still say afterward.
2. Walk it sentence by sentence. For each sentence, check the rules above in this order: tense, voice, length, ellipsis, noun clusters, ambiguous verbs.
3. Rewrite each flagged sentence to fix the violation. Preserve every fact, condition, and scope qualifier in the original.
4. If a rewrite would drop necessary precision (a safety condition, a number, a scope qualifier), keep the longer phrasing and flag the trade-off instead of silently simplifying.
5. If the input already complies, say so. Do not force changes onto compliant text.
6. Output the result in the format below.

## Output Format

Always use this template. Adapt column widths to your renderer.

```markdown
| Rule violated | Original | Simplified |
|---|---|---|
| Present perfect tense | "We have received your request." | "We received your request." |
| Noun cluster (4+ words) | "the agent task queue priority handler" | "the handler that sets task-queue priority" |
| Passive voice with unknown actor | "The file is deleted." | (Specify actor or leave only if genuinely irrelevant.) |
```

After the table, add one line for anything you deliberately did **not** simplify, and why. Example:

> Did not simplify: kept "less than 5 seconds" verbatim — STE allows the qualifier, but rounding to "quickly" would lose the safety window.

## Gotchas

These are the mistakes the agent makes most often when applying STE without guidance:

- **Over-shortening drops meaning.** STE forbids ellipsis to *shorten* — but you can still keep a clause when the clause carries required precision. A safety condition is not "fluff." If a number, scope qualifier, or exception is in the original, it must be in the rewrite.
- **Present perfect looks like past tense.** "We have received" reads like past tense but is forbidden. "We received" is the simple past STE allows. Same trap with "had been," "will have been," "is being."
- **Active voice requires a real actor.** Don't write "The system does X" when the original said "X is done" with no actor — first find the actor, then name it. If no actor exists, passive is allowed only in descriptive text, not in procedures.
- **"Check" vs "verify" vs "confirm".** STE wants one verb for one action. Pick "check" and use it every time in the same document. Mixing "check," "verify," "confirm," "make sure" for the same action forces the reader to wonder if they mean different things.
- **Noun clusters can be broken with "of" or "that".** "Fuel pump valve" stays (3 nouns). "High pressure fuel pump valve" becomes "valve of the high-pressure fuel pump" or "valve that controls the high-pressure fuel pump." Don't write a long prepositional chain either — pick the shortest that reads clearly.
- **Technical nouns and verbs are exempt from the base dictionary.** STE allows a project-specific glossary for terms the base ~900-word dictionary does not cover. If "kubernetes," "Lambda," or "tRPC" is in the original, keep it; just don't use it as both noun and verb in the same paragraph.
- **STE rewrites preserve format.** Tables, lists, code, and commands stay as-is. STE applies to prose only.

## Boundaries

**Will:**

- Rewrite ambiguous or dense English into short, single-meaning, active-voice sentences.
- Flag exactly which rule a sentence violates before rewriting it.
- Preserve every fact, condition, and scope qualifier in the original.
- Suggest a one-line glossary entry for domain terms that must stay.

**Will not:**

- Reproduce ASD's official ~900-word dictionary verbatim. Always treat the official download as the source of truth for exact approved wording.
- Simplify creative, marketing, or persuasive copy where voice is the point.
- Silently drop a safety condition, exception, or scope qualifier to shorten a sentence. Flag the trade-off instead.
- Guarantee an aerospace/defense-grade STE-compliant document. This is a general-purpose clarity tool inspired by STE, not a certified STE authoring tool.

## Sources

- ASD-STE100 Issue 9 (Jan 2025) — official standard, https://www.asd-ste100.org/
- ASD Europe — Simplified Technical English — https://www.asd-europe.org/standards-specifications/simplified-technical-english/
- Adapted from danyuchn/asd-ste100-skill (MIT) — original skill structure.

## Additional Resources

- **`references/writing-rules.md`** — full rule summary with citations to the official standard.
- **`examples/before-after.md`** — worked examples for agent output, error messages, tool descriptions.
