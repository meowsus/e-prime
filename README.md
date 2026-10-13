# e-prime

An [Agent Skill](https://agentskills.io) that teaches LLM agents to
draft, rewrite, audit, and calibrate prose in E-Prime — English without
any form of the verb *to be* (`be`, `am`, `is`, `are`, `was`, `were`,
`been`, `being`, and their contractions).

## Why strip *to be*?

General semantics blames the copula for two habits: the "is of identity"
(`X is Y`) freezes a live process into a label, and the "is of predication"
(`X is red`) passes a speaker's evaluation off as a property of the world.
E-Prime (D. David Bourland, Jr., 1949) removes the copula entirely, which
forces writers to name their observers, name their agents, and date their
claims. Practitioners — Albert Ellis in psychotherapy, Robert Anton
Wilson in fiction, generations of technical writers — report prose that
comes out clearer, livelier, and harder to mistake for gospel:

```text
"Mistakes were made."            →  "We made mistakes."
"Python is the best language."   →  "I rate Python above every language I've used."
```

Strict E-Prime suits some jobs; elsewhere it reads stilted. So the skill
carries two depths and the judgment to pick between them: **strict**
(remove every token) and **soft / E-Choice** (fix risky identity and
predication claims, keep harmless forms, add observer attribution).

## What the agent can do

Eight modes, one skill:

| Mode | What the agent does |
| ---- | -------------------- |
| `audit` | Inventory every *to be* form: line, function, epistemic risk, suggested repair |
| `rewrite` | Strict E-Prime conversion preserving meaning, register, and tone |
| `prime` | Soft E-Choice pass: fix risky identity/predication claims, keep harmless forms |
| `diff` | Annotated before/after with per-change rationales |
| `draft` | Compose new prose natively in E-Prime |
| `converse` | The agent itself speaks only in E-Prime, session-long |
| `tutor` | Capsule lessons, graduated drills, graded feedback |
| `guard` | De-absolutize prompts; emit E-Prime constraint snippets for other LLMs |

Ask naturally ("convert this to E-Prime") and the skill's description
triggers it — or invoke it by name: `/e-prime` in Claude Code, `$e-prime`
in Codex CLI, `/skill:e-prime` in pi.

## The judgment ships with the skill

Token matching alone satisfies nobody, so the skill carries its own
epistemics:

- **Standard carve-outs.** Quoted wording, code, URLs, titles, and proper
  names stay verbatim — flagged, never rewritten. (A purist switch exists
  for when you truly want everything converted.)
- **Spirit rules, not letter rules.** No euphemistic swaps ("exists as"
  still spells identity), no I-creep from constant attribution, no
  smuggled dogma through attributive adjectives. Clean token counts fail
  if the prose turns stilted or the claim sneaks back.
- **A mandatory self-verification loop.** The agent rescans every
  deliverable and, wherever it has shell access, runs the bundled
  deterministic linter — because published experiments put first-pass LLM
  compliance near 50%, and self-report does not suffice.

## The skill obeys its own rule

The skill's own `SKILL.md` prose passes the linter it ships. Verify:

```bash
python3 skills/e-prime/scripts/eprime_lint.py skills/e-prime/SKILL.md   # exit 0
```

## Does it help? What we measured

Honest headline first: capable models often already "know" E-Prime. On
this repo's harness (the `pi` runtime, Ollama's `glm-5.3:cloud` as host
model),
the model passed easy rewrites — even the contraction traps — from prior
knowledge, without ever opening the skill.

So the harness measures two independent signals, both read from the
event stream, never from the model's self-report:

- **activation** — did the model consult the skill's files before
  answering?
- **compliance** — does the final reply pass the linter?

A clean reply that never consulted the skill proves nothing about the
skill, so unconsulted runs fail by design. What separated the conditions
was discipline, not compliance: the mandatory self-verification loop
fired only when the skill loaded, and the unconsulted audits invented
their own hit-counting scheme instead of grounding counts in the linter.

| Signal                           | Plain prompt (unconsulted) | Skill loaded (`/skill:e-prime`) |
| -------------------------------- | -------------------------- | ------------------------------- |
| Consulted the skill              | 0/5                        | 2/2                             |
| Invoked the linter (self-verify) | 0/5                        | 2/2                             |
| Rewrite compliance               | 3/3 clean                  | 2/2 clean                       |
| Contraction-trap disambiguation  | correct                    | correct                         |

### Cross-model sweep (pre-launch)

One model proves little, so a pre-launch sweep scored every other
Ollama `:cloud` model the harness could drive: `deepseek-v4-pro:cloud`,
`kimi-k2.6:cloud`, `minimax-m2.7:cloud`, and `minimax-m3:cloud` — seven
cases, three sessions per case, raw logs in
`skills/e-prime/evals/results/`.

| Signal                          | deepseek-v4-pro | kimi-k2.6 | minimax-m2.7 | minimax-m3 | glm-5.3\* |
| ------------------------------- | --------------- | --------- | ------------ | ---------- | --------- |
| Skill advertised (auto)         | 15/15           | 15/15     | 15/15        | 14/15†     | 5/5       |
| Skill consulted (auto)          | 10/15           | 14/15     | 9/15         | 12/15      | 0/5       |
| SKILL.md injected (slash)       | 6/6             | 6/6       | 6/6          | 6/6        | 2/2       |
| Rewrite compliance              | 14/15           | 15/15     | 15/15        | 15/15      | 5/5       |
| Self-verify (linter, all runs)  | 5/21            | 15/21     | 1/21         | 9/21       | 2/7       |
| Verdicts                        | 16/21           | 20/21     | 15/21        | 18/21      | 2/7       |

\* the glm-5.3 column restates the single-run measurements above.
† one 240 s session produced no events (timeout under the concurrent
sweep) — infrastructure, not a model verdict; excluding it, 12/14
consulted.

Three patterns held across model lines:

1. **Prior knowledge travels.** Rewrite compliance on plain prompts ran
   59/60 lint-clean across the swept models — easy cases prove nothing
   about the skill, and the harness scores accordingly.
2. **Activation varies wildly by model.** `kimi-k2.6` consulted the
   advertised skill on 14/15 plain prompts and invoked the linter
   unprompted in 15/21 runs; `glm-5.3` never consulted at all;
   `deepseek-v4-pro` triaged — it opened the skill for audits,
   softening passes, and the contraction traps, then answered the
   easiest rewrites from memory.
3. **The skill helps wherever it loads.** All 24 injected runs passed
   the linter, across every family tested. The self-verification loop,
   however, transfers unevenly (15/21 down to 1/21), so treat
   discipline claims per model.

Not every pulled model runs: pi resolves `--model` against its bundled
catalog, not against Ollama's pulled manifests. Verify a name with
`pi --list-models <pattern>` before scoring it — pi 1.2.0 rejected seven
newer pulls outright.

Caveats, kept honest: small n — three runs per case, five models, four
families, one runtime — directional, not
statistical — and the ~50% first-pass figure describes the research
population, not your model. Compliance effects run wildly
model-idiosyncratic (see `skills/e-prime/references/llm-notes.md`).
Score your target model before shipping claims about it:

```bash
python3 skills/e-prime/evals/run_evals.py --model 'your-model' --runs 3
```

## Layout

```text
e-prime/
├── .claude-plugin/
│   ├── marketplace.json     # lets Claude Code add this repo as a marketplace
│   └── plugin.json          # plugin manifest (name, version, author)
├── .github/workflows/validate.yml
├── skills/
│   └── e-prime/             # the skill — drop this folder into any skills dir
│       ├── SKILL.md         # manifest + mode dispatch + core rules
│       ├── references/      # loaded on demand
│       │   ├── forms.md     # complete banned-form inventory, edge cases, false positives
│       │   ├── playbook.md  # repair strategies, phrase banks, pitfalls, drill bank
│       │   ├── theory.md    # history, rationale, evidence, criticisms, variants
│       │   └── llm-notes.md # LLM compliance research, task-fit table, guard templates
│       ├── scripts/         # executed, never loaded into context
│       │   └── eprime_lint.py   # deterministic to-be detector (stdlib-only)
│       └── evals/           # evaluation scenarios + pi-runtime harness
│           ├── scenarios.md     # deterministic expectations + scenario bank
│           ├── cases.json      # machine-readable eval cases
│           ├── run_evals.py    # activation/compliance harness (pi)
│           ├── results/        # raw logs from the published benchmark sweeps
│           └── fixtures/tricky.txt
├── README.md
└── LICENSE
```

## Install

`skills/e-prime/` follows the open [Agent Skills](https://agentskills.io)
specification; the runtimes below load it as-is.

- **Claude Code (plugin)**: `claude plugin marketplace add meowsus/e-prime`,
  then `claude plugin install e-prime@e-prime-skills`
- **Claude Code (manual)**: copy `skills/e-prime/` into `~/.claude/skills/`
  (personal) or `.claude/skills/` (project)
- **Codex CLI**: drop into `.agents/skills/` (project) or
  `~/.agents/skills/` (user)
- **Gemini CLI**: drop into `~/.gemini/skills/` (user) or
  `.gemini/skills/` (workspace)
- **GitHub Copilot**: drop into `~/.copilot/skills/` (personal) or
  `.github/skills/` (project)
- **GitHub CLI**: `gh skill install meowsus/e-prime e-prime` — installs
  for any of the agents it supports
- **claude.ai / Claude API**: zip `skills/e-prime` so `e-prime/` sits at
  the archive root, upload it under **Customize → Skills**, or POST it to
  the Skills API (`/v1/skills`)

## Validation

```bash
skills-ref validate skills/e-prime      # Agent Skills spec validator (from the agentskills.io reference repo)
claude plugin validate .                # plugin + marketplace manifests (needs Claude Code)
python3 skills/e-prime/scripts/eprime_lint.py skills/e-prime/SKILL.md   # exit 0
python3 skills/e-prime/scripts/eprime_lint.py skills/e-prime/evals/fixtures/tricky.txt  # exit 1 (by design)
python3 skills/e-prime/evals/run_evals.py   # behavioral evals on the pi runtime (needs pi + a reachable model; Ollama works)
```

The linter needs only `python3` — stdlib only, zero dependencies.

## License

MIT — see [LICENSE](LICENSE).