# Agent instructions

## Agent skills

### Issue tracker

Issues are tracked in this repo's GitHub Issues, via the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Default five triage labels (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: one `CONTEXT.md` + `docs/adr/` at the repo root. See `docs/agents/domain.md`.

## Skill authoring conventions

This repo ships installable Agent Skills. When creating or modifying anything under `skills/`, follow the Agent Skills authoring guides (consult on demand):

- [Best practices](https://agentskills.io/skill-creation/best-practices) — read before creating or substantially editing any skill (scoping, progressive disclosure, calibrating prescriptiveness)
- [Optimizing descriptions](https://agentskills.io/skill-creation/optimizing-descriptions) — read when writing or changing a skill's `description` frontmatter; validate with the trigger queries in `cases/<skill>/trigger-queries.json`
- [Evaluating skills](https://agentskills.io/skill-creation/evaluating-skills) — read when designing or running skill evaluations (case backfill, with/without-skill comparison)
- [Using scripts](https://agentskills.io/skill-creation/using-scripts) — read only when considering a `scripts/` addition; current skills are deliberately markdown-only (see the PRD)

For the investigation skill's methodology and repo conventions, see `docs/prd/integration-test-investigation.md`.
