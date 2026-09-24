# Case 002: message contracts and residue fragments

Synthetic seed case (deterministic regression baseline, not a real-usage
backfill). Covers ICU exact-match branches, HTML markup restoration, scalar
type mismatch, array completion, stale meaning, machine-identifier residue,
and locale-legal branch reduction.

## Prompt

Reconcile `fixtures/contracts/zh-CN.before.json` against
`fixtures/contracts/en.json`. English is authoritative. Modify only a
disposable copy of the Chinese file and report only changed paths and
validation results.

## Expected output

The Chinese file reaches structural parity; no exact expected file is pinned
because translation phrasing varies. Graded by checklist.

## Assertions

- Restores the missing `<strong>…</strong>` markup on `/billing/overdue`.
- Restores the missing `=0` exact-match branch on `/billing/items` while the
  locale-legal reduction of the CLDR `one` branch stays removed; the `other`
  fallback is never deleted (auditor must report the gap as missing
  `icu_option:=0`, not as an extra `icu_fallback`).
- Copies `/billing/refundWindow` as the number `30`.
- Completes `/billing/notifications` to English length and order.
- Replaces the stale `/errors/legacy` translation, preserving `Workflows`.
- Removes the target-only `/errors/promo`.
- Reports `ACME_API_KEY` as one whole residue fragment (not `ACME`, `API`,
  `KEY`) plus `shell` and `CLI`, each classifiable against the decision
  ledger.
- Completes the partial translation gap on `/billing/docs` ("for details").
- Leaves `/billing/invoiceReady`, `/billing/apiKeyHint`, and `/errors/network`
  unchanged.
- Does not create policy, glossary, cache, manifest, or sidecar files.

## Provenance

Fixture built for the 2026-09-24 darwin-skill optimization run; it reproduced
two auditor defects (ICU exact-match branch direction inversion, underscore
fragment splitting) and one semantic-review advantage over the no-skill
baseline (the `/billing/docs` partial-translation gap was caught only with
the skill).
