# JSON Reconciliation

Use these rules when the structural audit reports differences between the
English source and Chinese target.

## Comparison model

Address values with JSON Pointer paths. The root is `/`; object keys escape
`~` as `~0` and `/` as `~1`. Array elements use numeric segments.

Reconciliation requires equality of the data model, not byte-for-byte file
identity:

- object key sets and nesting are equal;
- object key order follows the source for stable review;
- arrays have equal length and corresponding element order;
- corresponding values have the same JSON type;
- non-string scalars have the same value;
- strings carry equivalent meaning and runtime contracts.

Whitespace, indentation, Unicode escaping, and the final newline follow the
repository's established formatter or, when none exists, the target file's
existing style.

## Objects

For every source object:

1. Add keys absent from the target at the same relative position.
2. Remove target-only keys unless an explicit documented exemption exists (see
   the hard rules in SKILL.md).
3. Recurse into shared keys.
4. Reorder the final target keys to match the source.

Do not infer that a renamed source key maps to a target-only key merely because
their values look similar. The English key set is authoritative. Remove the old
path and add the new one unless project evidence establishes an alias contract.

## Arrays

Array position is part of the contract. Match source length, order, and element
types. Translate string elements in place; recurse into object and array
elements; copy numbers, booleans, and null values exactly.

Do not treat an array as an unordered set without explicit project evidence.
Sorting translated values independently can detach labels from positional
meaning.

## Scalars

- Strings are translation units unless classified as protected or intentionally
  untranslated.
- Numbers, booleans, and null are copied from the source.
- A non-empty English string paired with an empty Chinese string is incomplete.
- An empty English string may remain empty; do not invent content.

JSON distinguishes booleans from numbers even in languages whose runtime type
systems do not. Preserve the JSON type exactly.

## Duplicate keys

Duplicate object keys make the source ambiguous because parsers may keep the
first value, keep the last value, or reject the file. Stop and report the
duplicate. Do not reconcile against whichever value a permissive parser kept.

## Minimal edits

Full reconciliation requires full review, not full rewriting. Preserve valid
Chinese values and avoid serializer churn. If canonical project tooling rewrites
the file, use it and identify the formatter in the final report.
