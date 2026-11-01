# Authoring & maintaining the `og-preview` skill

Agent guide for working **inside this skill repository**. Read it before editing `SKILL.md`, the README,
or any plugin manifest.

> Naming (Russian): the adjective for "agent / agentic" is **«агентный»**, never «агентский».

## Repository layout

This skill is packaged for **Claude Code**, **Cursor**, and **OpenAI Codex** (and installs as a plain
skill folder for Kimi Code CLI and others).

```
og-preview/
├─ .claude-plugin/
│  └─ plugin.json        # Claude Code plugin manifest
├─ .cursor-plugin/
│  └─ plugin.json        # Cursor plugin manifest
├─ .codex-plugin/
│  └─ plugin.json        # Codex plugin manifest (interface block + skills: "./")
├─ scripts/
│  └─ og_preview.py      # stdlib-only checker + HTML report renderer
├─ references/
│  ├─ index.md           # summary table + shared baseline + crawler UAs
│  └─ platforms/         # one file per platform - edit only what changes
│     ├─ telegram.md     ├─ x.md            ├─ facebook.md
│     ├─ discord.md      ├─ slack.md        ├─ whatsapp.md
│     └─ linkedin.md     ├─ reddit.md       └─ imessage.md
├─ examples/
│  ├─ neuraldeep.ru.html        # captured page fixture
│  ├─ neuraldeep-preview.html   # rendered report (reference output)
│  └─ neuraldeep-report.json    # machine-readable findings
├─ SKILL.md              # CANONICAL skill: YAML frontmatter + instructions (repo root)
├─ README.md             # human overview
├─ AGENTS.md             # this file
└─ LICENSE
```

## Golden rule: a change anywhere must be synced across the whole skill

- `SKILL.md` at the repo root is **canonical**; `scripts/` and `references/` live next to it and are
  referenced by relative path.
- `version` must be identical in `SKILL.md` frontmatter, `.claude-plugin/plugin.json`,
  `.cursor-plugin/plugin.json`, `.codex-plugin/plugin.json`.
- `description` must stay consistent across all manifests (plus `interface.shortDescription` in Codex).
- The `.claude-plugin/plugin.json` must **not** contain a `category` key - the manifest schema rejects it.
- Every release must be mirrored into the `rpa-skills` catalog (both `marketplace.json` files, README
  table when the description changed, catalog `metadata.version` bump).

## Code

`scripts/og_preview.py` is **standard library only** - no pip installs, the skill must work on a bare
Python 3. Keep it that way. When a platform rule changes, update the checker (`check_common`,
truncation budgets in `render_report`), the platform's file in `references/platforms/<name>.md` and
the summary row in `references/index.md` in the same commit. Regenerate `examples/neuraldeep-preview.html`
when rendering or findings change.

## Commit checklist

- [ ] `SKILL.md` edited where needed.
- [ ] `version` bumped and identical in all four manifests.
- [ ] `description` consistent across manifests.
- [ ] README updated.
- [ ] Release mirrored into `rpa-skills` (both manifests, README row, `metadata.version` bump).
- [ ] `python3 scripts/og_preview.py <fixture>` still produces a report.
- [ ] Conventional commit, e.g. `feat(og-preview): …` / `fix(og-preview): …`.
