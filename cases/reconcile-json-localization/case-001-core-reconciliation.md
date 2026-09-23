# Case 001: core reconciliation

## Prompt

Reconcile `fixtures/core/zh-CN.before.json` against
`fixtures/core/en.json`. English is authoritative. Modify only a disposable
copy of the Chinese file and report only changed paths and validation results.

## Expected output

The resulting Chinese JSON must equal `fixtures/core/zh-CN.expected.json` as a
JSON data model and key order.

## Assertions

- Adds `/auth/account` at the English position.
- Removes `/auth/obsolete`.
- Translates the fully English `/auth/signIn` and `/auth/retry` values.
- Preserves `GitHub` and `` `npm install` `` while translating surrounding
  prose.
- Finishes the partial translation at `/existing/mixed`.
- Corrects the stale meaning at `/existing/stale`.
- Uses a Chinese comma between the two clauses in the newly added
  `/auth/account` value instead of mapping both English full stops directly.
- Leaves `/auth/welcome`, `/auth/docs`, `/cli/install`, and `/existing/stable`
  byte-for-byte unchanged.
- Does not create policy, glossary, cache, manifest, or sidecar files.
- Reports only changed paths, unresolved paths, and compact validation results.
