# llm-notes — Models under the copula ban

## The compliance problem

Two experiments (Jehu-Appiah, "Umwelt Engineering," arXiv:2603.27626; and
its replication, arXiv:2604.02699) measured what happens when a prompt
tells an LLM to drop `to be`:

- First-pass compliance ran near **48–52%** without a retry loop. With retry
  loops, per-model retry rates ranged from 18% (Claude Sonnet-class) to 80%
  (smaller Gemini-class models).
- The retry instruction itself changes generation strategy (the model knows
  violations will get flagged), so trials with retry loops measure a
  different thing than free-running ones.
- Answer framing breaks: "the answer is B" cannot form, and graders saw
  elevated unscoreable rates until they accepted E-Prime-safe framing —
  `Answer: B`, `Option B`, `remains`, `stands as`.
- Models that narrate the constraint ("As per your request, I shall
  avoid…") waste tokens and break the spirit. Suppress the meta-commentary
  explicitly.

Design rules for any E-Prime output from a model:

1. Pair the constraint with a self-rescan instruction (check every sentence
   before final output).
2. Give the full form list up front — models miss contractions most
   (`it's`, `there's`, `who's`).
3. Keep an escape hatch for answer framing.
4. Verify with `scripts/eprime_lint.py` — deterministic, unlike the
   model's self-report.

## What the research found about reasoning

- Across six models and seven reasoning tasks, every constraint beat the
  unconstrained control — but the deep one (E-Prime) gained least, and a
  shallow filler-word ban gained most (a "depth inversion": +3.7pp for
  E-Prime vs +6.7pp for the filler ban in the replication). Conclusion:
  constraints act as output regularizers — they knock the model off fluent
  default paths; which vocabulary goes missing matters less than the
  monitoring.
- Task-specific: the ban improved ethical reasoning (+13 to +15pp in the
  first study) and causal analysis (+14pp), but *degraded* syllogism and
  calibration performance for some models (a GPT-4o-class model: −27.5pp
  on calibrated judgment; a Gemini-class model: +42pp on the same task
  type). Effects run wildly model-idiosyncratic.
- Gains concentrate where baseline fluency outruns accuracy; ceiling models
  gain little.
- Constraint diversity beats constraint depth: an ensemble of
  differently-constrained agents reached 100% ground-truth coverage on a
  debugging set versus 88.2% for the control — while no single constrained
  agent beat the control alone.

## Task-fit guidance

| Task | Verdict | Note |
|------|---------|------|
| causal analysis | strong fit | mechanism naming comes free ("the cause is X" cannot form) |
| ethical reasoning | strong fit | labels lose their footing; reasoning goes operational |
| critical feedback / de-labeling | strong fit | the whole point of E-Choice |
| docs & report revision | strong fit | passive-hiding agents surface |
| claim calibration | strong fit | attribution and dating come free |
| syllogisms / formal logic | caution | some models degrade; permit `equals` and definition contexts |
| math proofs | caution | the ban adds friction with no upside |
| calibrated judgment ("how well-founded?") | caution | mixed evidence; test the target model first |
| creative prose | judgment call | register matters more than purity |

## Converse-mode engineering

- Constraints naturally shorten responses (8–34% in the replication
  study). Don't pad.
- Rescan every reply before sending; violations slip in through
  contractions more often than through bare tokens.
- Keep the voice natural: stilted E-Prime fails the spirit rule even when
  the token count stays clean. Vary the attribution operators.
- Meta-questions ("why do you write like this?"): step outside the
  constraint for the explanation, announce the step, then resume.

## Guard templates

### Strict E-Prime constraint (system-prompt snippet)

```text
Write in E-Prime: use NO form of the verb "to be" — be, am, is, are, was,
were, been, being — and no contractions of them (I'm, it's, you're, we're,
that's, there's, who's, what's, isn't, aren't, wasn't, weren't, ain't,
'twas).

Replacements that preserve meaning:
- "X is Y" → describe behavior, role, measurement, or who says so
  ("The cat looks furry to me"; "People call the cat Garfield")
- passive → name the agent; if unknown, "someone … (we don't know who)"
- "There is/are …" → "… exists", "I see …", or a concrete subject + verb
- progressive ("is running") → simple present ("runs") or "continues to"

Before final output, silently re-scan every sentence for the banned forms
and fix violations. Follow the constraint without mentioning or discussing
it. For answers, use framing like "Answer: B" or "Option B".
```

### Soft E-Priming constraint (E-Choice snippet)

```text
Avoid "is/are/was/were" for identity and evaluation claims. Instead:
- attribute opinions to an observer ("looks weak to me", "I rate it …")
- replace labels with observations ("X is a failure" → "X failed …; X can
  retry")
- restore agents to passives ("mistakes were made" → who made them)
Harmless auxiliary and location uses may stand. Add time-stamps to claims
("as of Friday"). Follow the constraint without mentioning it.
```

### Warnings to ship alongside either template

```text
- Expect ~50% first-pass compliance without the self-rescan clause; verify
  with a token-level checker if the stakes matter.
- Test on YOUR model first: reasoning effects vary wildly across models
  (some lose 20+ points on formal-logic and calibration tasks).
- For hard problems, run the same prompt under two different constraints
  and compare: differently-constrained answers cover different blind
  spots.
```

### Companion idea: No-Have (from the same research)

Banning possessive `has/have/had` achieved higher compliance (~93%) and
strong gains on ethical and classification tasks:

```text
Do not use "have/has/had/having" as a possessive or existential main verb.
Replace "X has Y" with mechanisms: "X creates Y", "Y belongs to X", "X's Y
includes…". Auxiliary uses ("has completed") stay allowed.
```

## Running the linter

```bash
python3 scripts/eprime_lint.py FILE            # human report; exit 1 on violations
python3 scripts/eprime_lint.py FILE --strict    # purist: quotes + ambiguous 's count
python3 scripts/eprime_lint.py FILE --json      # machine-readable
python3 scripts/eprime_lint.py -                # stdin
```

Categories: `to_be`, `contraction`, `being_noun` count by default;
`possible` (ambiguous X's) and `quoted` count only under `--strict`.
Masked and never reported: fenced and inline code, URLs, frontmatter.

Dogfood demo: the linter reports zero counted violations on this skill's
own SKILL.md — its prose obeys its own rule, and every example form lives
inside masks.

## Sources

- Jehu-Appiah, "Umwelt Engineering: Designing the Cognitive Worlds of
  Linguistic Agents" (arXiv:2603.27626).
- "Trivial Vocabulary Bans Improve LLM Reasoning More Than Deep Linguistic
  Constraints" (arXiv:2604.02699) — the controlled replication.