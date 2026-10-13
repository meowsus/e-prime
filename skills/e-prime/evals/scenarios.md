# evals — Scenarios and fixtures

## Deterministic linter checks

```bash
python3 scripts/eprime_lint.py evals/fixtures/tricky.txt    # expect exit 1
python3 scripts/eprime_lint.py --strict evals/fixtures/tricky.txt  # expect exit 1
python3 scripts/eprime_lint.py SKILL.md                     # expect exit 0
```

### Fixture expectations — `evals/fixtures/tricky.txt`

| Category | Default | `--strict` |
|----------|---------|------------|
| `to_be` | 16 counted (4 more reported, tagged `[quoted]`) | 20 |
| `contraction` | 9 | 9 |
| `being_noun` | 1 | 1 |
| `possible` | 0 counted (3 reported) | 3 |
| **total counted** | **26** | **33** |

Traps the fixture exercises — each must behave exactly this way:

- Substring false positives never trip: `Island`, `maybe`, `this`,
  `its` produce zero hits.
- `let's` (twice) stays exempt (*let us*).
- `He's gone`, `She's been`, `John's book` land in `possible`, uncounted
  by default.
- `It's raining` — straight and curly apostrophe both — counts as a
  contraction.
- `"To be, or not to be"` and `"Whatever you say it is, it is not."` get
  tagged `[quoted]` and preserved (standard carve-out).
- The fenced block (`is_be = "was"`), the inline code
  (`x = "is not"`), and the URL (`https://example.com/is_a_test`) stay
  masked: zero hits.
- `IS-Architecture.md` stays quiet (hyphen-prefix rule).
- `well-being` exposes its `being` (post-hyphen note); `human being` lands
  in `being_noun` with the strict/soft note.
- `thou art` and `'twas` count as archaic contractions.
- The `was—is—` em-dash pair flags both tokens.
- `I'd` stays skipped (a *would* contraction, not a `to be` form).

### SKILL.md self-check

`python3 scripts/eprime_lint.py SKILL.md` exits 0 with zero counted
violations: the skill's own prose obeys the rule it teaches. Its handful of
`possible` hits all resolve as true possessives (`Bourland's`, `user's`,
`request's`, `speaker's`, `skill's`), and the two quoted terms
("is of identity", "is of predication") count as quoted material under
the standard carve-out.

## Behavioral scenarios

| # | Example prompt | Expected mode | Pass criteria |
|---|----------------|---------------|---------------|
| 1 | "Convert this to E-Prime: The report was late and the summary is missing." | rewrite | Zero banned tokens in the deliverable; meaning preserved; agents named where possible; change count reported outside the text |
| 2 | "Audit this paragraph for to-be verbs: …" | audit | Table with line, form, function, risk, suggested repair; hit count agrees with the linter |
| 3 | "Make this less dogmatic: Python is the best language and Java is dead." | prime | Identity/predication claims change; observer attribution added; harmless auxiliaries may survive; report of what stayed |
| 4 | "Rewrite, and show me what you changed and why" | rewrite + diff | Numbered log with one-line rationales; final text passes the linter |
| 5 | "Write a 100-word product update in E-Prime about our new dashboard" | draft | Verbs carry the prose; zero banned tokens; natural register (no I-creep) |
| 6 | "From now on, speak only in E-Prime" | converse | Every subsequent reply passes the linter; voice stays natural; meta-questions get announced frame-steps |
| 7 | "Teach me E-Prime" | tutor | Capsule lesson + drill items from the playbook bank + grading offer |
| 8 | "Add an E-Prime constraint to my prompt" | guard | Snippet contains the full form list + self-rescan clause + no-meta-commentary rule + task-fit warning, checked against the `llm-notes.md` table |
| 9 | "Rewrite this into E-Prime: Bob said, 'It is what it is.' See https://x.com/is_real" | rewrite (standard) | Quote stays verbatim, gets flagged, gets an offered paraphrase; URL untouched |
| 10 | "Convert everything, quotes too" | rewrite (purist) | Quoted material converted; each alteration marked |
| 11 | "Rewrite: The proposal is a disaster." | rewrite (spirit test) | No euphemistic swaps (`exists as a disaster` fails); observer/mechanism repair instead |
| 12 | Any rewrite deliverable | self-verify | Rescan performed (linter when available); zero counted hits before delivery |

Scoring: the automated part runs on linter exit codes; the qualitative part
needs a reviewer (or a second model pass) applying the spirit rules —
euphemistic swaps, smuggled identity, I-creep, and register damage all fail
even when tokens pass.

The `cases.json` suite automates scenarios 1, 2, 3, 5, and 9-adjacent
contraction traps via `run_evals.py`; see the next section.

## Automated runs on the pi runtime

`run_evals.py` executes the cases in `cases.json` against a live `pi`
session and scores two signals from the event stream — never from the
model's self-report. (Live testing on this repo caught the host model
denying a skills block that sat in its own system prompt; published
experiments put first-pass compliance near 50%. The event stream supplies
ground truth; the model supplies only the text under test.)

- **activation** — did the runtime advertise the skill in
  `<available_skills>`, and did the model open skill resources
  (SKILL.md, references/, scripts/eprime_lint.py) before answering?
- **compliance** — does the final reply pass the linter with zero counted
  violations? (`possible` hits — ambiguous `X's` — surface as warnings,
  since `he's gone` reads as *has* and stays legal; see the traps table
  above.)

Case modes:

- `auto` — plain prompt. An unconsulted run FAILS by design, even when
  the reply lints clean: a prior-knowledge answer proves nothing about
  the skill.
- `slash` — the `/skill:e-prime` prefix; pi injects the full SKILL.md,
  so these runs measure the skill's effect when consultation happens for
  certain. The model should also invoke the linter itself (the mandatory
  self-verification loop); the harness reports that under `self-verify`.

```bash
python3 evals/run_evals.py                        # full suite
python3 evals/run_evals.py --only easy-passage --runs 3
python3 evals/run_evals.py --model 'claude*'      # score a target model
```

Requirements: `pi` on PATH, a reachable model, and the skill hooked into
the runtime (project `.pi/skills/e-prime` plus project trust, or a
user-level `~/.pi/agent/skills/` drop-in) so auto cases get advertised.
Add cases to `cases.json` — each needs `id`, `mode`, `deliverable`
(`rewrite` = the linter must pass; `report` = activation-only), and
`prompt`.

First measurements on this repo (Ollama's `glm-5.3:cloud` as host
model, hookup active):
auto-mode consultation ran 0/5 — the model answers easy rewrites from
prior knowledge and ignores both the advertised skill and a load-first
instruction carried in the description; injected runs passed 2/2,
invoked the linter unprompted, and disambiguated the contraction traps
correctly (`He's gone` kept as *has*, `manager's in` repaired as *is*).
Compliance effects run wildly model-idiosyncratic (see
`references/llm-notes.md`), so score the target model before shipping
claims about it.