# Non-Translatable Content

Use this reference before preserving English in the Chinese target. User-facing
natural language is translatable by default. Keeping English is an exception
that requires a narrow classification and a concrete reason.

## Automatic source-first discovery

The agent, not the user, discovers non-translatable content. Before reconciling
the target, scan every English string and build an in-memory decision ledger.
The ledger never becomes a project file.

For each candidate, decide in this order:

1. Is it machine-consumed syntax or an exact external literal?
2. Is it an official proper name whose identity would change if translated?
3. Is it a language, package, framework, standard, protocol, command, or code
   identifier whose English spelling is required for use or searchability?
4. Does the intended Chinese professional audience normally use the English
   term, with a Chinese rendering sounding forced, ambiguous, or less precise?
5. Is the candidate merely ordinary English prose, a generic technical concept,
   or capitalization caused by sentence position or UI title style?

Preserve the smallest exact span for a positive answer to questions 1-4.
Translate question 5. Record the reason and evidence without asking the user to
prepare a terminology list.

The auditor emits `sourceEnglishCandidates` to surface acronyms, mixed-case
identifiers, capitalized words, and possible multiword names. This list is a
review queue only: capitalization does not prove that a term should remain
English, and lowercase industry terms may require separate semantic review.

## Reason codes

Use one of these codes in the in-memory decision ledger:

| Code | Applies to | Why it remains exact |
| --- | --- | --- |
| `RUNTIME_TOKEN` | placeholders, ICU arguments and selector keywords | parsed by the message runtime |
| `MACHINE_IDENTIFIER` | config keys, enum values, event names, flags | consumed or matched by software |
| `CODE_OR_COMMAND` | code, shell commands, package imports | must remain executable or reproducible |
| `PATH_OR_ADDRESS` | paths, URLs, hosts, email addresses, routes | changing it changes the destination |
| `PRODUCT_OR_BRAND` | official product, company, or trademark names | preserves official identity |
| `PACKAGE_OR_LIBRARY` | package, framework, and library names | preserves the installable/searchable name |
| `STANDARD_OR_PROTOCOL` | JSON, HTTP, OAuth 2.0, WebSocket | preserves the normative standard name |
| `VERSION_OR_CODE` | versions, status codes, exact error codes | supports exact compatibility and diagnosis |
| `EXACT_EXTERNAL_LITERAL` | third-party fields, log literals, external UI labels | must match an external system exactly |
| `LANGUAGE_NEUTRAL` | symbols, identifiers, and values with no natural language | translation has no linguistic meaning |

"Technical term" is not a valid reason. Ordinary concepts such as database,
cache, request, permission, account, and settings are normally translated.

Commonly preserved forms may include `API`, `SDK`, `CLI`, `JSON`, `HTTP`,
`OAuth 2.0`, `GitHub`, `React`, `TypeScript`, `PostgreSQL`, `npm`, `Docker`, and
`Kubernetes`, when they retain their official or conventional identity in the
specific message. This is evidence, not a universal allowlist.

Terms such as `prompt`, `token`, `embedding`, `agent`, and `workflow` require
audience and sentence-level judgment. Preserve them when English is the normal,
clear Chinese-industry expression; translate them when the product already has
a natural, unambiguous Chinese term. Apply one decision consistently to the same
concept while allowing a different decision when the word has another meaning.

## Protect spans, not sentences

Translate natural language around protected spans:

```text
Run npm install to continue.       Protect only: npm install
Sign in with GitHub.               Protect only: GitHub
Set API_BASE_URL in .env.          Protect only: API_BASE_URL, .env
Request failed: ERR_TIMEOUT.       Protect only: ERR_TIMEOUT
```

Translate every other word in each message. Do not preserve the whole message
merely because it contains one command, brand, identifier, or acronym.

## Context-dependent strings

Short values such as `OK`, `New`, `Open`, `Settings`, `Pro`, and `Enterprise`
are not globally protected. Decide from the JSON path, UI context, call site,
and project terminology. A UI action is usually translated; an official plan
or product name may remain English.

## Markup boundaries

Preserve tag and attribute names plus machine-facing values such as `href`,
`src`, `id`, `class`, and `data-*`. Translate visible text and natural-language
attributes such as `title`, `alt`, `aria-label`, and `placeholder`.

For Markdown, preserve link destinations and inline code; translate link labels
and surrounding prose.

## In-memory path-scoped decisions

Do not create or depend on a project policy file, and do not pass terminology
decisions through CLI flags. Record each decision only in the agent's current
working context with these fields:

```text
path: /auth/signIn
span: GitHub
reason: PRODUCT_OR_BRAND
evidence: official product name in this message
```

The path is mandatory. The same spelling can be an official name at one path
and translatable prose at another. A whole-value decision is allowed only for
code, a command, an exact external literal, or another value with no
translatable surrounding prose.

Prefer exact paths and spans over broad rules. Never exempt a namespace such as
`/errors` or `/settings`. Re-evaluate every decision from the current English
source each time the skill runs; do not persist it or ask the user to provide
it.

## Translation coverage gate

After masking runtime syntax, the auditor surfaces English in every Chinese
string leaf for semantic review:

- source equals target with English remaining -> `untranslated_identical`;
- target contains only unprotected English -> `english_only_target`;
- Chinese text still contains unprotected English words ->
  `unprotected_english`;
- another unexpected writing system remains -> `unexpected_script_target`.

The auditor does not decide whether a surfaced span is legitimate. The agent
must either translate it or add a path-scoped decision with a reason. The file
is reconciled only when every source string is classified as valid Chinese,
intentionally English by reason, or non-linguistic syntax/data.

## Final preservation audit

Recheck the source-first decision ledger against the completed Chinese target.
This gate is bidirectional:

- **under-translation check:** no unclassified English prose remains;
- **over-translation check:** every classified term remains exact, with the
  same occurrence count at each corresponding string path;
- **whole-value check:** every classified path is byte-for-byte equal to its
  English source value;
- **staleness check:** every ledger decision still refers to content present at
  that path in the current English source.

Any failure blocks reconciliation. This final check prevents a well-intentioned
translator from converting official names or conventional English industry
terms after they were correctly identified in the source-first pass.
