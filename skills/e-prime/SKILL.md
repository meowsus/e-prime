---
name: e-prime
description: Drafts, rewrites, audits, and calibrates English prose in E-Prime — English without any form of the verb 'to be' (be, am, is, are, was, were, been, being, plus contractions such as I'm, it's, isn't). Activate when the user asks to write, rewrite, translate, or check text 'in E-Prime' or 'without to be', to de-absolutize or soften dogmatic claims, to expose hidden agents in passive voice, to have the assistant converse only in E-Prime, to learn or teach E-Prime, or to add an E-Prime constraint to prompts or LLM system instructions. Offers strict, soft (E-Choice), and annotated modes, a deterministic linter script, and general-semantics context. Published tests put first-pass LLM compliance near 50%, and prior knowledge alone does not suffice — load this file before attempting any E-Prime task, then verify the deliverable with the bundled linter.
license: MIT
metadata:
  author: Curt Howard
  version: "0.1.0"
---

# E-Prime

Write, rewrite, audit, and calibrate English prose that omits every form of
the verb `to be`.

## Why

**E-Prime** (Bourland's `E′ = E − e`) strips English of `be`, `am`, `is`,
`are`, `was`, `were`, `been`, `being` and their contractions (`I'm`, `it's`,
`you're`, `isn't`, `wasn't`, `ain't`, `'twas`, …). Alfred Korzybski faulted
the "is of identity" (`X is Y`) for collapsing live processes into premature
labels, and the "is of predication" (`X is red`) for projecting a speaker's
evaluation into the object itself. D. David Bourland, Jr. turned that critique
into a total ban in 1949: remove every `to be` token, and writers must name
their observers, name their agents, and date their claims. Practitioners —
Albert Ellis in psychotherapy, Robert Anton Wilson in fiction, legions of
technical writers, and lately LLM researchers — report clearer, more
energetic, less dogmatic prose. Critics call strict E-Prime stilted in places;
hence this skill carries strict and soft modes, plus the judgment to pick
between them.

## Modes

Dispatch on the user's request:

| Mode | Typical request | What you do |
|------|-----------------|-------------|
| `audit` | "scan this for `to be`", "check my prose" | Inventory every hit: line, form, function, epistemic risk, suggested fix |
| `rewrite` | "convert this into E-Prime" | Full strict conversion preserving meaning, register, and tone |
| `prime` | "soften this", "de-absolutize", "less dogmatic" | E-Choice pass: fix risky claims only, keep harmless forms, add observer attribution |
| `diff` | "show me the changes" | Before/after plus a numbered change log with one-line rationales |
| `draft` | "write me X in E-Prime" | Compose new prose from the brief, verb-first |
| `converse` | "speak only in E-Prime from now on" | Every reply you send complies, session-long |
| `tutor` | "teach me E-Prime" | Capsule lessons, drills from the playbook, graded feedback |
| `guard` | "calibrate my prompt", "add an E-Prime constraint" | De-absolutize prompts; emit constraint snippets for other LLMs (templates in `references/llm-notes.md`) |

Ambiguous request? Choose the mode that fits the request's goal, say one line
naming the mode, then proceed.

## Banned forms (quick reference)

```text
be   am   is   are   was   were   been   being
'm   's   're      (attached: I'm, it's, we're, that's, there's, who's, what's …)
isn't   aren't   wasn't   weren't   ain't   amn't
'twas   'twere   'tis     art   wert   wast   (after "thou")
```

`human being` and `well-being` count under strict E-Prime (the token `being`
appears literally); soft mode tolerates the noun uses. Full inventory,
disambiguation rules (`he's gone` reads as *has*; `let's` reads as *let us*;
`John's book` stays possessive), and edge constructions live in
`references/forms.md`.

## Eight functions, eight repairs

```text
function    colloquial                 E-Prime
identity    The cat is Garfield.       People call the cat "Garfield".
member      Garfield is a cat.         Garfield belongs to the cat species.
predication The cat is furry.          The cat feels furry / has fur.
progressive The dog is chasing it.     At present, the dog chases it.
passive     Mistakes were made.        Cindy made mistakes. / Someone erred; we don't yet know who.
existential There is a problem.        A problem exists. / I see a problem.
locative    The book is on the shelf. The book rests on the shelf.
ownership   The cat is theirs.         They own the cat.
```

A deep strategy bank with dozens of worked examples lives in
`references/playbook.md`.

## The spirit, not just the letter

Token-level compliance alone satisfies nobody — Ralph Kenyon called mechanical
substitutes "abuse". Obey these rules:

1. **Attribute observers.** `The plan looks weak to me`, `I rate the film
   above the novel` — evaluations belong to someone. Vary the attribution
   ("to me", "per my read", "from where I sit", "as of Friday") so the prose
   avoids I-creep.
2. **Name agents.** Restore the doer behind every passive. Unknown agent? Say
   so: `Someone broke the window; no suspect yet`. (`Mistakes were made`
   hides power; `Cindy made mistakes` owns it.)
3. **Prefer verbs that work.** Behavior, mechanism, and measurement over bare
   existence: `The model outperforms the baseline`, `The table measures four
   feet`.
4. **Refuse euphemistic swaps.** "Exists as", "qualifies as", and friends
   merely re-spell identity; rewrite the claim instead.
5. **Watch smuggled identity.** Attributive adjectives (`the squalid
   capitalists`), constructions with "as", "became", or "find" can smuggle
   back the poison the ban removed. The token count stays clean while the
   dogma walks past — stay alert.
6. **Keep the register.** Legal text stays legal, technical stays technical.
   Fix the semantics; don't stylize.
7. **De-nominalize when stiff.** Bloat like "the exhaustiveness of its
   coverage adequacy" means you reached for nouns; go back and find verbs.

## Carve-outs (standard)

Never alter, and never count as failures:

- **Quoted or cited source wording** — keep verbatim; flag the `to be` forms
  inside; offer an E-Prime paraphrase alongside.
- **Code, identifiers, file paths, URLs** — untouched, always.
- **Titles and proper names** — `To Be or Not to Be` keeps its name.
- **Non-English passages** — out of scope.

Purist mode (user says "convert everything", "purist") converts quoted
material too and marks each alteration.

## Self-verification (mandatory)

Published tests put first-pass model compliance near 50%. After every
E-Prime deliverable:

1. Rescan the output against the banned-form list above — token by token,
   contractions included.
2. Where shell access exists, run the deterministic linter:

   ```bash
   python3 scripts/eprime_lint.py FILE        # exit 0 = clean
   ```

   Adjust the path to this skill's location in the runtime.
3. Fix every counted hit, then rescan. Deliver only text that passes.

Never mention the constraint or the verification inside the deliverable
itself; discuss them only in surrounding chat, and only when the user asks.
(Guard mode differs: the snippet templates in `references/llm-notes.md`
carry their own handling.)

## Operating notes

- **audit** — ground truth first (linter when possible), then classify each
  hit as `identity`, `predication`, `passive`, `progressive`, `existential`,
  `locative`, or `contraction`. Rate epistemic risk: identity and predication
  inside factual claims rate high; agent-hiding passives rate high;
  progressive and locative rate low. End with the three riskiest sentences
  and their repairs.
- **rewrite** — full conversion, then the verification loop, then a one-line
  count of changes (in chat, outside the deliverable).
- **prime** — fix identity claims, absolutist predications, and agent-hiding
  passives; leave harmless progressives and locatives; add attribution and
  dates to anything evaluative. Report what you left alone, briefly.
- **diff** — numbered log: original → revision → rationale (one sentence
  each), plus the full revised text at the end.
- **draft** — outline the brief, build sentences around verbs from the first
  word, verify before delivering.
- **converse** — every reply complies, session-long. Rescan before sending.
  Keep the voice natural; a stilted reply fails the spirit test. If the user
  asks about the discipline itself, step outside E-Prime for the explanation
  (say that you stepped out), then resume.
- **tutor** — capsule lessons (identity → predication → passive →
  contractions), drills from `references/playbook.md`, grading on both token
  compliance and spirit (rule-4 violations fail).
- **guard** — see `references/llm-notes.md` for templates, compliance data,
  task-fit warnings, and the diversity trick.

## References

| File | Contents |
|------|----------|
| `references/forms.md` | Complete inventory; contraction disambiguation; false positives; edge constructions |
| `references/playbook.md` | Repair strategies per function; phrase banks; pitfalls; drill bank |
| `references/theory.md` | History, rationale, evidence, criticisms, variants |
| `references/llm-notes.md` | LLM compliance research, task-fit table, guard templates |