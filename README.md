# e-prime

Shell repository for an Agent Skill that will teach LLM agents to draft,
rewrite, and audit prose in E-Prime — English without any form of the verb
*to be*. The skill content arrives in a follow-up commit; this scaffolding
holds the layout, distribution manifests, and CI.

## Layout

```text
e-prime/
├── .claude-plugin/
│   ├── marketplace.json     # lets Claude Code add this repo as a marketplace
│   └── plugin.json          # plugin manifest (name, version, author)
├── .github/workflows/validate.yml
├── skills/
│   └── e-prime/             # the skill — drop this folder into any skills dir
│       ├── SKILL.md         # required manifest + instructions
│       ├── references/      # loaded on demand
│       ├── scripts/         # executed, never loaded into context
│       └── evals/           # evaluation scenarios
├── README.md
└── LICENSE
```

## Install (once the skill ships)

- **Claude Code plugin**: `claude plugin marketplace add your-org/e-prime`,
  then `claude plugin install e-prime@e-prime-skills`
- **Manual drop-in**: copy `skills/e-prime/` into a runtime's skills
  directory — `~/.claude/skills/` (Claude Code, personal),
  `.claude/skills/` (project), `.agents/skills/` (Codex CLI),
  `~/.gemini/skills/` (Gemini CLI), `.copilot/skills/` (GitHub Copilot)
- **claude.ai / Claude API**: zip `skills/e-prime` and upload it in
  Settings → Features, or POST it to `/v1/skills`

## Validation

```bash
skills-ref validate skills/e-prime   # agentskills.io reference validator
claude plugin validate .             # plugin + marketplace manifests
```

## License

MIT — see [LICENSE](LICENSE).