# ASD-STE100 Writing Rules — Summary

This file paraphrases the public, official description of ASD-STE100 (Simplified Technical English) Issue 9 (January 2025). It does **not** reproduce the standard's text or its ~900-word dictionary verbatim. For the authoritative document, request the free download at https://www.asd-ste100.org/.

## What ASD-STE100 Is

ASD-STE100 is a controlled natural language, first released in 1986 (as AECMA Document PSC-85-16598) by what is now ASD (the AeroSpace and Defense Industries Association of Europe). It was built at the request of European airlines — most staffed by non-native English speakers — who needed maintenance documentation that could not be misread, because a misread instruction on an aircraft can kill people. The standard is maintained by the Simplified Technical English Maintenance Group (STEMG) and has been free to download since Issue 6 (2013). The current edition is Issue 9 (January 2025).

## Structure

- **53 writing rules across 9 sections** covering word choice, grammar, sentence structure, and style.
- **A dictionary** of roughly 900 approved words, each restricted to one meaning and one part of speech, plus roughly 1,200 words to avoid with suggested replacements.
- **A terminology allowance**: organizations may define their own dictionary of approved technical nouns and verbs beyond the base ~900 words, for domain-specific vocabulary the base dictionary cannot cover.

## Rule Categories (Paraphrased)

### Word choice

- Use approved words only in their approved meaning and part of speech.
- Each word maps to exactly one meaning. Do not rely on context to disambiguate a word that has several dictionary senses.
- Prefer the plainer, shorter, more common word over a formal or rare synonym.

### Verb forms

- Permitted forms: infinitive, imperative, simple present, simple past, simple future, and past participle used only as an adjective.
- No present perfect, past perfect, or other compound or auxiliary constructions. "We have received" is not allowed. "We received" is.
- "-ing" forms are permitted only as a technical noun or as part of a technical noun, not as a verb form.

### Voice

- Active voice is required for procedures and instructions.
- Passive voice is allowed only in descriptive text, and only when the actor performing the action is genuinely unknown or irrelevant to the reader.

### Sentence structure

- One instruction per sentence.
- Maximum ~20 words per sentence for procedures and instructions. Maximum ~25 words for descriptive text.
- Do not omit sentence parts (verb, subject, article) just to shorten the sentence. STE explicitly warns that this creates ambiguity rather than clarity.
- Noun clusters (strings of nouns stacked as a modifier) are capped at 3 words.

### Paragraph and document structure

- One topic per paragraph.
- Maximum ~6 sentences per paragraph.
- Use vertical (numbered or bulleted) lists for sequences, conditions, or complex enumerations instead of burying them in prose.

### Safety instructions

- Safety-critical instructions must open with a clear command or condition, not be buried mid-sentence.

## Why STE Fits Agent Output

STE was designed to eliminate ambiguity for a reader who cannot ask a follow-up question — a technician on a tarmac, working from a manual, with no author to call. An AI agent parsing another agent's output, a tool description, or a system message is in the same position: no back-channel to resolve "does this passive-voice sentence mean the caller does X, or the callee does X?" The same rule set that protects an airline mechanic from a misread torque spec protects a downstream agent from a misread instruction.

## What This Skill Does Not Do

This skill encodes the rule *categories* of STE, not the dictionary. It applies the underlying *principle* — pick the plainest available word and use it the same way every time — rather than checking against the fixed word list. When exact ASD-approved wording matters (e.g. actual aircraft maintenance documentation), download the official standard and check word-by-word against the real dictionary.

## Sources

- ASD-STE100 official site — https://www.asd-ste100.org/
- ASD-STE100 — About STE — https://www.asd-ste100.org/about_STE.html
- ASD Europe — Simplified Technical English — https://www.asd-europe.org/standards-specifications/simplified-technical-english/
- Simplified Technical English — Wikipedia — https://en.wikipedia.org/wiki/Simplified_Technical_English
- TechScribe — ASD-STE100 Simplified Technical English — https://www.techscribe.co.uk/techw/asd-simplified-technical-english.htm
- SKYbrary — Simplified Technical English (STE) — https://skybrary.aero/articles/simplified-technical-english-ste
