# e-prime

An [Agent Skill](https://agentskills.io) that teaches LLM agents to
draft, rewrite, audit, and calibrate prose in E-Prime — English without
any form of the verb "to be" (`be`, `am`, `is`, `are`, `was`, `were`,
`been`, `being`, and their contractions).

## Why strip the copula?

General semantics blames the copula for two habits: the "is of identity"
(`X is Y`) freezes a live process into a label, and the
"is of predication" (`X is red`) passes a speaker's evaluation off
as a property of the world. E-Prime (D. David Bourland, Jr., 1949) removes the copula
entirely, which forces writers to name their observers, name their
agents, and date their claims. Practitioners — Albert Ellis in
psychotherapy, Robert Anton Wilson in fiction, generations of technical
writers — report prose that comes out clearer, livelier, and harder to
mistake for gospel:

```text
"Mistakes were made."            →  "We made mistakes."
"Python is the best language."   →  "I rate Python above every language I've used."
```

Strict E-Prime suits some jobs; elsewhere it reads stilted. So the skill
carries two depths and the judgment to pick between them: **strict**
(remove every token) and **soft / E-Choice** (fix risky identity and
predication claims, keep harmless forms, add observer attribution).

## Eight modes, one skill

| Mode | What the agent does |
| ---- | -------------------- |
| `audit` | Inventory every copula form: line, function, risk, repair |
| `rewrite` | Strict conversion preserving meaning, register, and tone |
| `prime` | Soft E-Choice pass: fix risky claims, keep harmless forms |
| `diff` | Annotated before/after with per-change rationales |
| `draft` | Compose new prose natively in E-Prime |
| `converse` | The agent itself speaks only in E-Prime, session-long |
| `tutor` | Capsule lessons, graduated drills, graded feedback |
| `guard` | De-absolutize prompts; emit constraint snippets for other LLMs |

Ask naturally ("convert this to E-Prime") and the skill's description
triggers it — or invoke it by name: `/e-prime` in Claude Code, `$e-prime`
in Codex CLI, `/skill:e-prime` in pi.

## The judgment ships with the skill

Token matching alone satisfies nobody, so the skill carries its own
epistemics:

- **Standard carve-outs.** Quoted wording, code, URLs, titles, and
  proper names stay verbatim — flagged, never rewritten. (A purist
  switch converts everything.)
- **Spirit rules, not letter rules.** No euphemistic swaps ("exists as"
  still spells identity), no I-creep from constant attribution, no
  smuggled dogma through attributive adjectives. Clean token counts fail
  if the prose turns stilted or the claim sneaks back.
- **A mandatory self-verification loop.** The agent rescans every
  deliverable and, with shell access, runs the bundled deterministic
  linter — published experiments put first-pass LLM compliance near 50%,
  and self-report does not suffice.

## Does it help?

Honest headline first: capable models often already "know" E-Prime — on
this repo's harness (`pi` runtime, Ollama `:cloud` models), they pass
easy rewrites from prior knowledge, never opening the skill. A clean
reply that never consulted the skill proves nothing about it, so
unconsulted runs fail by design. The harness reads two signals from the
event stream, never from self-report:

- **activation** — did the model consult the skill's files before
  answering?
- **compliance** — does the final reply pass the linter?

A pre-launch sweep scored five models across four families (seven
cases, three sessions per case; raw logs in
`skills/e-prime/evals/results/`):

| Signal                          | deepseek-v4-pro | kimi-k2.6 | minimax-m2.7 | minimax-m3 | glm-5.3\* |
| ------------------------------- | --------------- | --------- | ------------ | ---------- | --------- |
| Skill advertised (auto)         | 15/15           | 15/15     | 15/15        | 14/15†     | 5/5       |
| Skill consulted (auto)          | 10/15           | 14/15     | 9/15         | 12/15      | 0/5       |
| SKILL.md injected (slash)       | 6/6             | 6/6       | 6/6          | 6/6        | 2/2       |
| Rewrite compliance              | 14/15           | 15/15     | 15/15        | 15/15      | 5/5       |
| Self-verify (linter, all runs)  | 5/21            | 15/21     | 1/21         | 9/21       | 2/7       |
| Verdicts                        | 16/21           | 20/21     | 15/21        | 18/21      | 2/7       |

\* glm-5.3 numbers come from the repo's first, single-run measurements;
every other model ran three sessions per case.
† one 240 s session produced no events (timeout under the concurrent
sweep) — infrastructure, not a model verdict.

Three patterns held:

1. **Prior knowledge travels.** Unconsulted rewrites ran 59/60
   lint-clean across the swept models — easy cases prove nothing about
   the skill.
2. **Activation varies wildly by model.** `kimi-k2.6` consulted the
   advertised skill on 14/15 plain prompts and self-verified with the
   linter in 15/21 runs; `glm-5.3` never consulted at all.
3. **The skill helps wherever it loads.** All 24 injected runs passed
   the linter — but the self-verification loop transfers unevenly
   (15/21 down to 1/21), so treat discipline claims per model.

Caveats, kept honest: small n — three runs per case, five models, one
runtime — directional, not statistical, and the ~50% first-pass figure
describes the research population, not your model. Score your target
model before shipping claims about it:

```bash
python3 skills/e-prime/evals/run_evals.py --model 'your-model' --runs 3
```

## Install

`skills/e-prime/` follows the open [Agent Skills](https://agentskills.io)
specification; the runtimes below load it unchanged.

- **Claude Code**: `claude plugin marketplace add meowsus/e-prime`, then
  `claude plugin install e-prime@e-prime-skills` — or copy
  `skills/e-prime/` into `~/.claude/skills/` (personal) or
  `.claude/skills/` (project)
- **Codex CLI**: drop into `.agents/skills/` (project) or
  `~/.agents/skills/` (user)
- **Gemini CLI**: drop into `~/.gemini/skills/` (user) or
  `.gemini/skills/` (workspace)
- **GitHub Copilot**: drop into `~/.copilot/skills/` (personal) or
  `.github/skills/` (project)
- **GitHub CLI**: `gh skill install meowsus/e-prime e-prime` — installs
  for any of the agents it supports
- **claude.ai / Claude API**: zip `skills/e-prime` so `e-prime/` sits at
  the archive root, upload under **Customize → Skills**, or POST it to
  the Skills API (`/v1/skills`)

## Validation

The skill obeys its own rule: `SKILL.md` passes the linter it ships —
and so does this README. The linter needs only `python3`: stdlib, zero
dependencies.

```bash
python3 skills/e-prime/scripts/eprime_lint.py skills/e-prime/SKILL.md                  # exit 0
python3 skills/e-prime/scripts/eprime_lint.py skills/e-prime/evals/fixtures/tricky.txt # exit 1 (by design)
python3 skills/e-prime/evals/run_evals.py --model 'your-model' --runs 3                # behavioral evals (pi + a reachable model)
```

## License

MIT — see [LICENSE](LICENSE).