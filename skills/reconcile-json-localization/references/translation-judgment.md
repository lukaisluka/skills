# Translation Judgment

Use this reference to decide whether an existing Chinese value is equivalent to
the current English source.

## Fidelity criteria

A valid translation preserves:

- the subject, action, object, and affected user or resource;
- negation, conditions, exceptions, and causal relationships;
- modality and strength, including must, should, may, cannot, and warnings;
- quantities, limits, units, versions, and comparison direction;
- UI intent such as action, status, title, explanation, or destructive warning;
- distinctions between similar product concepts.

Natural Chinese sentence order is expected. Literal English syntax is not a
fidelity requirement.

## Punctuation for new translations

Apply semantic Chinese punctuation only to paths that were missing from the
target, empty despite a non-empty source, or initially reported as
`untranslated_identical` or `english_only_target` after protected English was
accounted for. Intentionally English and non-linguistic values are not eligible.
Decide eligibility before editing and retain the path set in working context
only.

Do not map punctuation character by character. English often uses multiple
short sentences where natural Chinese uses connected clauses. Depending on
meaning, rhythm, and relationship, an English full stop may become a Chinese
comma or semicolon; a colon may become a comma; or an English terminal mark may
be omitted for a short UI label. Follow established Chinese product style when
it exists.

Preserve punctuation inside placeholders, decimals, versions, URLs, paths,
commands, code, abbreviations, and other protected content.

Do not use this rule to restyle values that already contained Chinese at the
start of the run. In particular:

- do not perform punctuation-only cleanup across the file;
- do not change `。` to `，` merely because a new translation would use `，`;
- do not treat a mixed Chinese-English value as automatically eligible;
- do not rewrite existing Chinese punctuation for consistency with newly added
  keys.

An existing Chinese value may still require punctuation changes when its
meaning must be corrected, a runtime contract is broken, or the user explicitly
requests punctuation editing. That is a separate justification, not
punctuation naturalization.

## Terminology priority

Choose terms in this order:

1. the same concept's established translation in the current target file;
2. a repository glossary or explicit project terminology;
3. matching Chinese locale files in the same product;
4. common domain usage;
5. a new translation, recorded in the report when it establishes terminology.

Do not force one Chinese term onto distinct English concepts merely for visual
consistency. Do not vary a stable term without a semantic reason.

## Existing translations

Preserve an existing Chinese value when it still covers the complete current
English meaning. A source wording change does not require target churn if the
meaning did not change.

Replace a value when it reflects an older state, omits a changed condition,
reverses an action, weakens a warning, or refers to a renamed product concept.
Translate the complete message unit rather than patching isolated words into an
old Chinese sentence.

## Identical source and target strings

Equality containing unprotected English is a blocking untranslated candidate.
Classify each identical pair as one of:

- product or company name;
- code, protocol, path, URL, command, or technical identifier;
- language-neutral symbol, acronym, number, or version;
- deliberately untranslated project term;
- untranslated natural language that must be fixed.

Intentional equality requires a path-scoped in-memory decision and reason from
[non-translatable-content.md](non-translatable-content.md). Short words such as
`OK` require context rather than a blanket rule. Without an approved
classification, translate the value or leave reconciliation incomplete.

## Partial English

A Chinese value is incomplete when unprotected English prose remains after
placeholders, commands, brands, identifiers, and other approved spans are
masked. This includes values that are entirely English but differ from the
source, so source-target equality alone is not a sufficient detector.

Translate the remaining prose and preserve only the classified spans. A mixed
target that translates "Connect your" but leaves `GitHub account` remains
incomplete even when `GitHub` is approved, because `account` is still ordinary
natural language.

## Ambiguity

Use neighboring messages, UI structure, code call sites, product documentation,
and existing terminology to resolve meaning. If materially different Chinese
translations remain possible and the choice affects product behavior, stop at
that path and state the missing decision. Do not conceal ambiguity with a vague
translation.
