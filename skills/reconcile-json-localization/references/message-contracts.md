# Message Contracts

Read this reference when locale strings contain runtime syntax or protected
content. A translation can be linguistically correct and still break the
application if its message contract changes.

## Arguments and placeholders

Preserve the exact argument identifiers and required occurrences used by the
project's message system, including forms such as:

- `{name}` and `{{name}}`
- `${name}`
- `%(name)s`
- `%s`, `%d`, and positional printf arguments
- ICU arguments such as `{count, plural, ...}`

Chinese may reorder arguments. It may not silently drop, rename, duplicate, or
invent them. Literal examples that merely resemble placeholders require
project-specific judgment; validate them with the real message parser when
available.

## ICU and selector syntax

The argument set and control structure must remain compatible with the runtime.
Keep explicit selectors and required fallback branches such as `other`.
Locale-specific plural branches may differ only when the project's message
format and validator explicitly support that difference.

The bundled auditor compares ICU message structure between source and target:
argument names, selector type (plural/select/selectordinal), custom option
names, the presence of the `other` fallback, and the presence of `#` in plural
messages. CLDR branch categories such as `one`, `two`, and `few` may legitimately
differ by locale and are not compared. The auditor still does not validate
nested ICU grammar — run the project's ICU or message-format compiler before
declaring reconciliation complete.

## Markup

Preserve the structure and attributes of markup embedded in messages unless the
project explicitly marks an attribute as translatable. Maintain paired tags and
do not move text outside the element that gives it runtime or accessibility
meaning.

For Markdown, preserve link destinations, inline-code spans, and code-like
identifiers. Link labels may be translated; destinations normally remain exact.

## Protected literals

Classify preserved English for the current run with
[non-translatable-content.md](non-translatable-content.md). Typical protected
content includes:

- product and company names;
- commands, flags, environment variables, and configuration keys;
- file paths, URLs, hostnames, API routes, and protocol values;
- code identifiers and enum values;
- version strings and identifiers supplied by the application.

Natural-language text surrounding a protected literal is still translatable.
Do not protect a complete message solely because one literal is protected.

## Escapes and whitespace

Preserve meaningful newlines, tabs, non-breaking spaces, and escaped delimiters.
Do not assume whitespace is decorative in terminal output, multiline labels,
templating syntax, or Markdown rendered from locale strings.
