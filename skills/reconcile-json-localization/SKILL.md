---
name: reconcile-json-localization
description: >
  Use this skill to reconcile a maintained Chinese locale JSON file against its
  English source of truth. Apply it when English and Chinese locale files must
  be brought into complete parity, including keys, nesting, value types, array
  shape, key order, placeholders, message syntax, protected tokens, and current
  meaning. Add missing translations, update stale or mismatched Chinese text,
  and remove obsolete target-only entries. Do not use it for application i18n
  setup, non-JSON formats, or unrelated one-off translation.
compatibility: Requires Python 3.10+ to run the bundled read-only auditor.
---

# Reconcile JSON Localization

Make the current Chinese locale JSON a faithful derivative of the current
English locale JSON. Reconciliation is a full current-state comparison, not an
incremental translation based on version-control history.

## Hard rules

1. **English is authoritative.** Never edit the English source unless the user
   explicitly asks for a separate source correction.
2. **Check the complete files.** A clean diff or equal key count does not prove
   reconciliation.
3. **Preserve correct Chinese.** Do not rephrase an existing translation that
   already expresses the current English meaning and satisfies project style.
4. **Reach structural parity.** Keys, nesting, value types, array length and
   order, and object key order must match the English source.
5. **Remove obsolete target entries.** A Chinese-only path is an error unless
   the project has an explicit documented exemption.
6. **Preserve runtime contracts.** Do not lose, add, rename, or corrupt
   placeholders, selectors, markup, escapes, URLs, commands, paths, or other
   protected tokens.
7. **Do not hide uncertainty.** Invalid JSON, duplicate keys, ambiguous source
   text, and unverified message syntax are blockers, not reasons to guess.
8. **Completion means zero unexplained differences.** Mechanical validation
   must pass and every translatable string must be semantically reviewed.
9. **Translate by default.** English preserved in the Chinese target requires a
   precise protected span or path plus a reason code for the current run;
   "technical term" is not a sufficient reason.
10. **Classify every source string.** Sampling and key parity cannot establish
    translation coverage. No string leaf may remain unreviewed.
11. **Leave no project artifacts.** Do not create or require a localization
    policy, glossary, manifest, cache, sidecar, or other support file. The only
    project file changed by this workflow is the requested Chinese locale JSON.
12. **Discover exceptions automatically.** Never ask the user to enumerate
    brands or terms up front. Scan the complete English source first, decide
    which exact spans should remain English, and keep the decision in memory
    only for the current run.
13. **Scope punctuation naturalization.** Choose punctuation from Chinese
    meaning, not by replacing English glyphs one-for-one, but apply this
    punctuation redesign only to paths that were missing or fully untranslated
    at the start of the run. Do not modernize punctuation in existing Chinese
    translations.

## Flow

```text
1 RESOLVE FILES
      ↓
2 SCAN ENGLISH SOURCE
      ↓
3 AUDIT CURRENT STRUCTURE
      ↓
4 RECONCILE JSON SHAPE
      ↓
5 RECONCILE MESSAGE CONTRACTS
      ↓
6 RECONCILE MEANING
      ↓
7 VALIDATE AGAIN
      ↓
8 REPORT
```

## 1 Resolve files

1.1 Identify the English source and Chinese target from the user's paths,
repository conventions, locale configuration, or neighboring locale files.

1.2 Confirm that both inputs are strict JSON. JSONC, JavaScript modules, YAML,
PO, ARB, and generated bundles are outside this version of the skill; report
the format boundary instead of parsing them as JSON.

1.3 Determine the intended Chinese variant from project evidence. Preserve the
existing variant and voice; do not silently convert between Simplified and
Traditional Chinese.

1.4 Read project instructions and existing terminology before translating.
Do not invent a new glossary when stable Chinese terms already exist.

1.5 Do not require project localization configuration and do not ask the user
to supply a list of English exceptions.

## 2 Scan the English source

Read the entire English JSON before translating or reviewing the Chinese file.
This is a mandatory source-first discovery pass, not an optional reaction to
English residue found later.

Read
[references/non-translatable-content.md](references/non-translatable-content.md),
then build an in-memory decision ledger containing the exact JSON Pointer path,
exact span or whole value, reason code, and evidence. Automatically consider:

- official product, company, feature, plan, and trademark names;
- package, library, framework, language, standard, and protocol names;
- acronyms, initialisms, commands, code, identifiers, and external literals;
- domain terms that the intended Chinese technical audience conventionally
  writes in English because a Chinese rendering is less natural or less clear.

Do not preserve a candidate merely because it is capitalized or technical.
Ordinary prose and concepts with a natural Chinese expression remain
translatable. Protect the smallest exact span, never the surrounding sentence.

The auditor's `sourceEnglishCandidates` list is a discovery queue, not an
automatic exemption list. Review it completely, then inspect the source for
lowercase domain terms the lexical queue cannot recognize. Resolve decisions
autonomously from source context, repeated usage, existing Chinese terminology,
and standard Chinese industry usage. Ask the user only when product identity or
meaning is genuinely undecidable and materially changes the result.

Scope every decision to its path. The same spelling may be a product name in
one message and ordinary prose in another. Keep the ledger in the agent's
working context and never pass it through CLI flags or write it into the target
repository.

## 3 Audit current structure

Run the bundled read-only auditor from the skill directory:

```bash
python3 scripts/audit_json_parity.py <english.json> <chinese.json> --format json
```

The script receives only the English and Chinese JSON paths. It does not accept
terminology decisions, configuration, or generated support files.

Exit status `0` means mechanical parity with no English review items, `1` means
mechanical reconciliation differences exist, `2` means an input could not be
validated, and `3` means mechanical parity with English spans that require the
agent's semantic decision. The script never edits either file. Exit `3` is not
a failure and not completion by itself: review every reported path against the
source-first decision ledger.

If the script cannot run, reproduce the same checks with available JSON
capabilities and state that the bundled validation was unavailable.

## 4 Reconcile JSON shape

Read [references/json-reconciliation.md](references/json-reconciliation.md)
before editing structural differences.

Process every reported path:

| Difference | Required action |
| --- | --- |
| Missing in Chinese | Add the path in the English position and translate strings |
| Extra in Chinese | Remove it unless an explicit exemption exists |
| Type mismatch | Rebuild the target value with the English type and shape |
| Array-length mismatch | Match English length and element order |
| Key-order mismatch | Reorder the Chinese object to match English |
| Non-string scalar mismatch | Copy the authoritative English scalar |
| Empty translation | Translate it, or preserve empty only when English is empty |

Use minimal edits. Preserve the target file's indentation, newline convention,
Unicode style, and trailing newline unless the project formatter requires a
different canonical representation.

## 5 Reconcile message contracts

Read [references/message-contracts.md](references/message-contracts.md) when a
string contains placeholders, interpolation, plural/select syntax, HTML,
Markdown, URLs, commands, paths, or escape-sensitive content.

Read [references/non-translatable-content.md](references/non-translatable-content.md)
before deciding that any English span or complete value should remain English.

For every shared string:

5.1 Compare the source and target argument set and protected-token multiset.

5.2 Preserve token spelling exactly while allowing Chinese word order to
change around it.

5.3 Use the project's parser or message compiler when the format has one. The
bundled auditor recognizes common token shapes but is not a complete parser for
every message language.

5.4 A token mismatch is not resolved until the target parses and the runtime
receives the same arguments and control branches it expects.

## 6 Reconcile meaning

Read [references/translation-judgment.md](references/translation-judgment.md)
before deciding whether an existing Chinese value is current.

Review every translatable source-target string pair, including pairs not
reported by the mechanical auditor. For large files, work in bounded batches
and keep a complete path checklist; sampling cannot establish reconciliation.

Before editing, classify each path from the initial target state. Mark a path
`PUNCTUATION_ELIGIBLE` only when it is absent, empty while the source is not, or
reported as `untranslated_identical` or `english_only_target` after approved
English spans are accounted for. Do not include intentionally English or
non-linguistic values. Keep this path set in working context; do not write a
baseline or metadata file.

Classify each string:

- **VALID** — accurately expresses the current English meaning; preserve it.
- **MISSING** — no Chinese value exists; translate it.
- **STALE** — reflects an older English meaning; replace it.
- **MISMATCHED** — present but semantically wrong or incomplete; replace it.
- **INTENTIONALLY UNTRANSLATED** — product name, code, protocol value, or other
  justified invariant covered by a path-scoped decision and reason code;
  preserve it and record the reason.
- **AMBIGUOUS** — cannot be translated reliably from available context; report
  the exact path and missing decision instead of guessing.

Preserve conditions, negation, modality, numbers, scope, and user action. Write
natural Chinese rather than copying English syntax, but do not add explanation,
marketing language, or product behavior absent from the source.

For `PUNCTUATION_ELIGIBLE` paths, choose commas, full stops, semicolons, colons,
question marks, exclamation marks, and sentence boundaries from the completed
Chinese meaning. Several short English sentences may become connected Chinese
clauses, and an English full stop may therefore become a Chinese comma. Do not
perform mechanical `.` to `。` substitution.

For every other path that already contained Chinese at the start, preserve its
punctuation unless a semantic correction, runtime contract, or explicit user
request makes a punctuation change necessary. This rule must not cause a
punctuation-only rewrite of existing translations. A partially translated
Chinese-English value is not automatically punctuation-eligible.

## 7 Validate again

7.1 Rerun the auditor after editing. Mechanical differences must reach zero.
Exit `3` is acceptable only after every review item has been classified by the
agent; exit `0` means no semantic English review was needed.

7.2 Require combined mechanical and semantic translation coverage `100%` and
zero unclassified paths. Fix or explicitly classify every
`untranslated_identical`, `english_only_target`, `unprotected_english`, and
`unexpected_script_target` review item. The script's unresolved count includes
items awaiting agent classification and may remain nonzero for intentional
English until that semantic review is complete.

7.3 Run the dedicated English-preservation audit in both directions:

- every term or whole value selected in the source-first decision ledger must
  remain exact at the corresponding target path and occurrence count;
- every other English fragment in the Chinese target must be translated or
  independently justified.

Compare the path-scoped ledger directly with the completed target. Missing,
changed, duplicated, or newly introduced occurrences are blocking. A whole
English sentence must not survive merely because it contains one protected
token.

7.4 Run repository-provided locale parsers, message compilers, linters, and
tests when available. A generic JSON parse does not prove ICU or application-
specific message validity.

7.5 Inspect the final diff. Only the requested Chinese target may change;
supporting files, generated metadata, and unrelated translation churn are
defects.

7.6 Run the punctuation-scope check against the initial path classification:

- every punctuation redesign belongs to a path that was missing or fully
  untranslated at the start; or
- the change is independently required by a semantic correction, runtime
  contract, or explicit user instruction.

Reject punctuation-only churn on pre-existing Chinese translations. For every
eligible new translation, review punctuation from the Chinese sentence meaning
rather than comparing glyphs with the English source.

7.7 If any ambiguity or validator failure remains, report status `BLOCKED` or
`PARTIAL`. Do not describe the files as reconciled.

## 8 Report

Large locale files require change-focused reporting. Full-file review and
unchanged-value checks remain mandatory internally, but do not list, count, or
summarize paths whose target value was left unchanged. Likewise, do not expose
the full source candidate queue or decision ledger in the user-facing report.

Report only:

- paths actually added, updated, removed, reordered, or reshaped;
- blocking or unresolved paths;
- compact validation outcomes.

If no content changed, say so once rather than enumerating unchanged paths.

Use this compact result format:

```markdown
## Localization reconciliation

Source: <English JSON>
Target: <Chinese JSON>
Status: RECONCILED / PARTIAL / BLOCKED

Changes:
- Added: <count and paths>
- Updated: <count and paths>
- Removed: <count and paths>
- Reordered or reshaped: <count and paths>

Validation:
- JSON and duplicate keys: PASS / FAIL
- Structure and order: PASS / FAIL
- Message contracts: PASS / FAIL
- English-preservation audit: PASS / FAIL
- Punctuation scope and naturalness: PASS / FAIL
- Translation coverage: <percent, unresolved count>
- Semantic review coverage: PASS / FAIL
- Project checks: <commands and results, or unavailable>

Unresolved:
- <path, reason, required decision>
```

Write the report in the user's language.

## Resources

- `scripts/audit_json_parity.py` — read-only structural and common-token audit
- [references/json-reconciliation.md](references/json-reconciliation.md) — JSON
  path, object, array, scalar, ordering, and formatting rules
- [references/message-contracts.md](references/message-contracts.md) — runtime
  tokens and format-specific validation boundaries
- [references/non-translatable-content.md](references/non-translatable-content.md)
  — protected-content reason codes, path-scoped decisions, and English review
- [references/translation-judgment.md](references/translation-judgment.md) —
  semantic equivalence, terminology, invariants, and ambiguity handling
