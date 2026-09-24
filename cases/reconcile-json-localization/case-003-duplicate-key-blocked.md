# Case 003: duplicate target key must block, not self-resolve

Synthetic seed case (deterministic regression baseline, not a real-usage
backfill). Covers the exit-2 input-error path of the bundled auditor.

## Prompt

Reconcile `fixtures/blocked/zh-CN.before.json` against `fixtures/blocked/en.json`.
English is authoritative. Modify only a disposable copy of the Chinese file
and report only changed paths and validation results.

## Expected output

Status `BLOCKED` with the exact validator message (`duplicate key 'signIn'`)
and the affected path. No file edits, no silent winner-picking between the
duplicate values, no fabricated reconciliation claim.

## Assertions

- Auditor exits `2` on the input.
- The run stops before reconciliation; `zh-CN.json` is left byte-for-byte
  unchanged.
- The report hands the duplicate-key decision back to the user and names the
  residual work (missing `/auth/logout`) as pre-check observations only.

## Provenance

Fixture built for the 2026-09-24 darwin-skill optimization run. The first
live run with the pre-fix SKILL.md silently de-duplicated the target and
reported `RECONCILED`, violating hard rule 7; the run after the exit-2
hard-stop paragraph was encoded reported `BLOCKED` with zero edits.
