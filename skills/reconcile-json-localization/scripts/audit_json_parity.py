#!/usr/bin/env python3
"""Read-only structural audit for English and Chinese locale JSON files."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys
from typing import Any


class AuditInputError(ValueError):
    """Raised when an input cannot be audited reliably."""


class DuplicateKeyError(ValueError):
    """Raised when a JSON object contains a duplicate key."""


class NonStandardConstantError(ValueError):
    """Raised when Python's JSON parser encounters NaN or Infinity."""


def reject_nonstandard_constant(value: str) -> None:
    raise NonStandardConstantError(f"non-standard JSON constant {value!r}")


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate key {key!r}")
        result[key] = value
    return result


def load_json_object(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8-sig") as handle:
            value = json.load(
                handle,
                object_pairs_hook=reject_duplicate_keys,
                parse_constant=reject_nonstandard_constant,
            )
    except FileNotFoundError as exc:
        raise AuditInputError(f"file not found: {path}") from exc
    except PermissionError as exc:
        raise AuditInputError(f"cannot read {path}: permission denied") from exc
    except DuplicateKeyError as exc:
        raise AuditInputError(f"{path}: {exc}") from exc
    except NonStandardConstantError as exc:
        raise AuditInputError(f"{path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise AuditInputError(
            f"{path}:{exc.lineno}:{exc.colno}: invalid JSON: {exc.msg}"
        ) from exc
    except UnicodeError as exc:
        raise AuditInputError(f"{path}: invalid UTF-8: {exc}") from exc

    if not isinstance(value, dict):
        raise AuditInputError(
            f"{path}: locale JSON must have an object at the top level"
        )
    return value


TOKEN_RE = re.compile(
    r"""
    (?P<double_brace>\{\{\s*[A-Za-z_][\w.-]*\s*\}\})
    |(?P<dollar_brace>\$\{\s*[A-Za-z_][\w.-]*\s*\})
    |(?P<python_named>%\([A-Za-z_][\w.-]*\)[#0+\- ]*\d*(?:\.\d+)?[a-zA-Z])
    |(?P<printf>%(?:\d+\$)?[#0+\- ]*\d*(?:\.\d+)?[a-zA-Z%])
    |(?P<brace>\{\s*[A-Za-z_][\w.-]*\s*(?=[,}]))
    """,
    re.VERBOSE,
)
MARKDOWN_DESTINATION_RE = re.compile(r"\]\(([^)\s]+)(?:\s+['\"][^'\"]*['\"])?\)")
HTML_TAG_RE = re.compile(r"</?[A-Za-z][^<>]*?>")
TRANSLATABLE_HTML_ATTRIBUTE_RE = re.compile(
    r"\b(?:title|alt|aria-label|placeholder)\s*=\s*(?:\"([^\"]*)\"|'([^']*)')",
    re.IGNORECASE,
)
HTML_ATTRIBUTE_RE = re.compile(
    r"(?<![\w:-])([A-Za-z_:][\w:.-]*)"
    r"(?:\s*=\s*(?:\"([^\"]*)\"|'([^']*)'|([^\s\"'=<>`]+)))?"
)
TRANSLATABLE_HTML_ATTRIBUTE_NAMES = frozenset(
    {"title", "alt", "aria-label", "placeholder"}
)
INLINE_CODE_RE = re.compile(r"(?<!`)`[^`\n]+`(?!`)")
URL_RE = re.compile(r"\b(?:https?://|mailto:)[^\s<>\"')]+", re.IGNORECASE)
EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PATH_RE = re.compile(r"(?<![\w.])(?:\.{0,2}/|/)[A-Za-z0-9._~!$&'()*+,;=:@%/-]+")
CLI_FLAG_RE = re.compile(r"(?<![\w-])--?[A-Za-z][A-Za-z0-9-]*\b")
VERSION_RE = re.compile(r"\bv?\d+(?:\.\d+){1,}(?:[-+][A-Za-z0-9.-]+)?\b")
ICU_MESSAGE_RE = re.compile(
    r"\{\s*(?P<arg>[A-Za-z_][\w.-]*)\s*,\s*(?P<kind>plural|select|selectordinal)\s*,"
)
ICU_CONTROL_RE = re.compile(
    r"\b(?:plural|select|selectordinal|offset|zero|one|two|few|many|other)\b"
)
ICU_CLDR_KEYWORDS = frozenset(
    {"offset", "zero", "one", "two", "few", "many", "other"}
)
ASCII_WORD_RE = re.compile(r"[A-Za-z]+(?:['’-][A-Za-z]+)*")
SOURCE_MULTIWORD_NAME_RE = re.compile(
    r"\b[A-Z][A-Za-z0-9+.#-]*(?:\s+[A-Z][A-Za-z0-9+.#-]*){1,4}\b"
)
SOURCE_MIXED_IDENTITY_RE = re.compile(
    r"\b(?:[A-Za-z]+[A-Z][A-Za-z0-9]*|"
    r"[A-Za-z][A-Za-z0-9]*(?:[.+#/@_-][A-Za-z0-9]+)+|"
    r"[A-Za-z]+\d+[A-Za-z0-9]*)\b"
)
SOURCE_ACRONYM_RE = re.compile(r"\b[A-Z][A-Z0-9]*(?:[.+#/-][A-Z0-9]+)*\b")
SOURCE_CAPITALIZED_RE = re.compile(r"\b[A-Z][a-z][A-Za-z0-9+.#-]*\b")
HAN_RE = re.compile(
    r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\U00020000-\U0003134f]"
)


def extract_translatable_html_attributes(match: re.Match[str]) -> str:
    values: list[str] = []
    for attribute in TRANSLATABLE_HTML_ATTRIBUTE_RE.finditer(match.group(0)):
        values.append(attribute.group(1) or attribute.group(2) or "")
    return f" {' '.join(values)} "


def icu_message_spans(value: str) -> list[tuple[int, int]]:
    """Return brace-balanced spans of ICU plural/select messages."""

    spans: list[tuple[int, int]] = []
    for match in ICU_MESSAGE_RE.finditer(value):
        depth = 0
        index = match.start()
        closed = -1
        while index < len(value):
            character = value[index]
            if character == "'":
                # ICU quote escape ('{ or ''): skip the escaped character.
                index += 2
                continue
            if character == "{":
                depth += 1
            elif character == "}":
                depth -= 1
                if depth == 0:
                    closed = index
                    break
            index += 1
        end = closed + 1 if closed >= 0 else len(value)
        spans.append((match.start(), end))
    return spans


def icu_branch_options(
    value: str, spans: list[tuple[int, int]]
) -> list[tuple[str, int, int]]:
    """Collect branch option names at the direct child level of ICU messages.

    Only words at a branch boundary — right after the message header or after
    a sibling branch body closes — are options. A body-text word before a
    nested placeholder (`Error, see {link}`) never qualifies.
    """

    options: list[tuple[str, int, int]] = []
    span_by_start = {start: (start, end) for start, end in spans}
    for message in ICU_MESSAGE_RE.finditer(value):
        span = span_by_start.get(message.start())
        if span is None:
            continue
        index, end = message.end(), span[1]
        while index < end:
            character = value[index]
            if character in " \t\r\n":
                index += 1
                continue
            if character == "}":
                break
            word_match = re.match(r"[A-Za-z_][\w.-]*", value[index:end])
            if word_match is None:
                break
            word_start = index
            word = word_match.group(0)
            index += word_match.end()
            while index < end and value[index] in " \t\r\n":
                index += 1
            if word == "offset" and index < end and value[index] == ":":
                index += 1
                while index < end and value[index] in " \t\r\n":
                    index += 1
                number = re.match(r"[+-]?\d+", value[index:end])
                if number is None:
                    break
                index += number.end()
                continue
            if index >= end or value[index] != "{":
                break
            options.append((word, word_start, word_start + len(word)))
            index += 1
            depth = 1
            while index < end and depth > 0:
                character = value[index]
                if character == "'":
                    index += 2
                    continue
                if character == "{":
                    depth += 1
                elif character == "}":
                    depth -= 1
                index += 1
    return options


def mask_protected_content(value: str) -> tuple[str, list[dict[str, str]]]:
    coverage_text = HTML_TAG_RE.sub(extract_translatable_html_attributes, value)
    candidates: list[tuple[int, int, str, str, str, str]] = []

    def collect(
        pattern: re.Pattern[str],
        reason: str,
        origin: str,
        group: int = 0,
        note: str = "",
    ) -> None:
        for match in pattern.finditer(coverage_text):
            start, end = match.span(group)
            if start != end:
                candidates.append(
                    (start, end, reason, match.group(group), origin, note)
                )

    collect(INLINE_CODE_RE, "CODE_OR_COMMAND", "syntax")
    collect(URL_RE, "PATH_OR_ADDRESS", "syntax")
    collect(EMAIL_RE, "PATH_OR_ADDRESS", "syntax")
    collect(PATH_RE, "PATH_OR_ADDRESS", "syntax")
    collect(CLI_FLAG_RE, "MACHINE_IDENTIFIER", "syntax")
    collect(VERSION_RE, "VERSION_OR_CODE", "syntax")
    collect(MARKDOWN_DESTINATION_RE, "PATH_OR_ADDRESS", "syntax", group=1)

    icu_spans = icu_message_spans(coverage_text)
    icu_header_spans = [
        match.span() for match in ICU_MESSAGE_RE.finditer(coverage_text)
    ]

    def within(start: int, end: int, spans: list[tuple[int, int]]) -> bool:
        return any(s <= start and end <= e for s, e in spans)

    for match in TOKEN_RE.finditer(coverage_text):
        start, end = match.span(0)
        if match.lastgroup == "brace" and within(start, end, icu_spans):
            if not within(start, end, icu_header_spans):
                # Inside an ICU message body a bare {word} is branch text,
                # not a placeholder; leave it visible for residue detection.
                # Message-head arguments are protected as RUNTIME_TOKEN.
                continue
        candidates.append(
            (start, end, "RUNTIME_TOKEN", match.group(0), "syntax", "")
        )

    if ICU_MESSAGE_RE.search(coverage_text):
        collect(ICU_CONTROL_RE, "RUNTIME_TOKEN", "syntax")
        for word, start, end in icu_branch_options(coverage_text, icu_spans):
            candidates.append(
                (start, end, "RUNTIME_TOKEN", word, "syntax", "")
            )

    masked = list(coverage_text)
    protected: list[dict[str, str]] = []
    occupied = [False] * len(masked)
    for start, end, reason, raw, origin, note in sorted(
        candidates, key=lambda item: (item[0], -(item[1] - item[0]))
    ):
        if any(occupied[start:end]):
            continue
        for index in range(start, end):
            occupied[index] = True
            masked[index] = " "
        protected.append(
            {"value": raw, "reason": reason, "origin": origin, "note": note}
        )

    return "".join(masked), protected


def extract_tokens(value: str) -> Counter[str]:
    tokens: Counter[str] = Counter()
    icu_spans = icu_message_spans(value)
    for match in TOKEN_RE.finditer(value):
        kind = match.lastgroup or "token"
        raw = match.group(0)
        if kind == "brace":
            start, end = match.span(0)
            if any(s <= start and end <= e for s, e in icu_spans):
                # Inside an ICU message the head argument is compared as
                # icu_arg and body text words are not placeholders at all.
                continue
            name_match = re.match(r"\{\s*([A-Za-z_][\w.-]*)", raw)
            assert name_match is not None
            raw = name_match.group(1)
        tokens[f"{kind}:{raw}"] += 1
    exact_patterns = (
        (INLINE_CODE_RE, "inline_code", 0),
        (URL_RE, "url", 0),
        (EMAIL_RE, "email", 0),
        (PATH_RE, "path", 0),
        (CLI_FLAG_RE, "cli_flag", 0),
        (VERSION_RE, "version", 0),
        (MARKDOWN_DESTINATION_RE, "markdown_destination", 1),
    )
    exact_candidates: list[tuple[int, int, str, str]] = []
    for pattern, kind, group in exact_patterns:
        for match in pattern.finditer(value):
            start, end = match.span(group)
            exact_candidates.append((start, end, kind, match.group(group)))
    occupied = [False] * len(value)
    for start, end, kind, raw in sorted(
        exact_candidates, key=lambda item: (item[0], -(item[1] - item[0]))
    ):
        if any(occupied[start:end]):
            continue
        for index in range(start, end):
            occupied[index] = True
        tokens[f"{kind}:{raw}"] += 1

    for tag_index, match in enumerate(HTML_TAG_RE.finditer(value)):
        raw = match.group(0)
        name_match = re.match(r"</?\s*([A-Za-z][\w:-]*)", raw)
        assert name_match is not None
        direction = "close" if raw.startswith("</") else "open"
        closing = "self" if raw.rstrip().endswith("/>") else direction
        tokens[
            f"html_sequence:{tag_index}:{closing}:{name_match.group(1).lower()}"
        ] += 1
        if direction == "close":
            continue
        attribute_text = raw[name_match.end() :]
        for attribute in HTML_ATTRIBUTE_RE.finditer(attribute_text):
            name = attribute.group(1).lower()
            attribute_value = (
                attribute.group(2)
                or attribute.group(3)
                or attribute.group(4)
                or ""
            )
            if name in TRANSLATABLE_HTML_ATTRIBUTE_NAMES:
                tokens[f"html_attribute:{tag_index}:{name}"] += 1
            else:
                tokens[
                    f"html_attribute:{tag_index}:{name}={attribute_value}"
                ] += 1
    if icu_spans:
        has_plural = False
        has_fallback = False
        for match in ICU_MESSAGE_RE.finditer(value):
            tokens[f"icu_arg:{match.group('arg')}"] += 1
            tokens[f"icu_selector:{match.group('kind')}"] += 1
            has_plural = has_plural or match.group("kind") == "plural"
        for name, _start, _end in icu_branch_options(value, icu_spans):
            if name == "other":
                has_fallback = True
            if name not in ICU_CLDR_KEYWORDS:
                tokens[f"icu_option:{name}"] += 1
        if has_plural and "#" in value:
            # Existence, not count: dropping a locale-irrelevant branch such
            # as `one` legitimately removes its `#` occurrences.
            tokens["icu_number_sign"] += 1
        if has_fallback:
            tokens["icu_fallback"] += 1
    if "\n" in value:
        tokens["control:newline"] += value.count("\n")
    if "\t" in value:
        tokens["control:tab"] += value.count("\t")
    return tokens


def json_type(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, list):
        return "array"
    if isinstance(value, str):
        return "string"
    if isinstance(value, (int, float)):
        return "number"
    raise TypeError(f"unsupported JSON value: {type(value).__name__}")


def escape_pointer_segment(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def child_path(path: str, segment: str | int) -> str:
    escaped = escape_pointer_segment(str(segment))
    return f"/{escaped}" if path == "/" else f"{path}/{escaped}"


def collect_string_paths(value: Any, path: str = "/") -> set[str]:
    paths: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            paths.update(collect_string_paths(child, child_path(path, key)))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            paths.update(collect_string_paths(child, child_path(path, index)))
    elif isinstance(value, str):
        paths.add(path)
    return paths


def collect_string_entries(
    value: Any, path: str = "/"
) -> list[tuple[str, str]]:
    entries: list[tuple[str, str]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            entries.extend(collect_string_entries(child, child_path(path, key)))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            entries.extend(collect_string_entries(child, child_path(path, index)))
    elif isinstance(value, str):
        entries.append((path, value))
    return entries


def discover_source_english_candidates(source: Any) -> list[dict[str, Any]]:
    """Build a review queue for the agent; candidates are not auto-exemptions."""

    patterns = (
        (SOURCE_MULTIWORD_NAME_RE, "multiword_name"),
        (SOURCE_MIXED_IDENTITY_RE, "mixed_identifier"),
        (SOURCE_ACRONYM_RE, "acronym"),
        (SOURCE_CAPITALIZED_RE, "capitalized_word"),
    )
    discovered: dict[str, dict[str, Any]] = {}
    for _path, value in collect_string_entries(source):
        review_text, _ = mask_protected_content(value)
        candidates: list[tuple[int, int, str, str]] = []
        for pattern, kind in patterns:
            for match in pattern.finditer(review_text):
                raw = match.group(0)
                if kind == "acronym" and len(raw) == 1:
                    continue
                candidates.append((match.start(), match.end(), raw, kind))

        occupied = [False] * len(review_text)
        for start, end, raw, kind in sorted(
            candidates, key=lambda item: (item[0], -(item[1] - item[0]))
        ):
            if any(occupied[start:end]):
                continue
            for index in range(start, end):
                occupied[index] = True
            entry = discovered.setdefault(
                raw,
                {"value": raw, "kind": kind, "count": 0},
            )
            entry["count"] += 1

    return sorted(
        (
            item
            for item in discovered.values()
            if item["kind"] != "capitalized_word" or item["count"] > 1
        ),
        key=lambda item: item["value"].casefold(),
    )


def add_finding(
    findings: list[dict[str, Any]],
    severity: str,
    kind: str,
    path: str,
    **detail: Any,
) -> None:
    finding: dict[str, Any] = {
        "severity": severity,
        "kind": kind,
        "path": path,
    }
    finding.update(detail)
    findings.append(finding)


def classify_translation(
    source: str,
    target: str,
    path: str,
    errors: list[dict[str, Any]],
    reviews: list[dict[str, Any]],
    coverage: dict[str, int],
) -> None:
    if source.strip() and not target.strip():
        add_finding(errors, "error", "empty_translation", path)
        return

    remaining, _protected = mask_protected_content(target)
    english_fragments = ASCII_WORD_RE.findall(remaining)
    has_han = HAN_RE.search(remaining) is not None
    has_other_letters = any(
        character.isalpha()
        and not ("A" <= character <= "Z" or "a" <= character <= "z")
        and HAN_RE.match(character) is None
        for character in remaining
    )

    if english_fragments:
        if source == target:
            kind = "untranslated_identical"
        elif has_han:
            kind = "unprotected_english"
        else:
            kind = "english_only_target"
        add_finding(
            reviews,
            "review",
            kind,
            path,
            fragments=english_fragments,
        )
        coverage["review_required"] += 1
        return

    if has_other_letters:
        add_finding(reviews, "review", "unexpected_script_target", path)
        coverage["review_required"] += 1
        return

    if has_han:
        coverage["valid_chinese"] += 1
    else:
        coverage["non_linguistic"] += 1


def compare_values(
    source: Any,
    target: Any,
    path: str,
    errors: list[dict[str, Any]],
    reviews: list[dict[str, Any]],
    coverage: dict[str, int],
) -> None:
    source_type = json_type(source)
    target_type = json_type(target)
    if source_type != target_type:
        add_finding(
            errors,
            "error",
            "type_mismatch",
            path,
            expected=source_type,
            actual=target_type,
        )
        return

    if isinstance(source, dict):
        source_keys = list(source)
        target_keys = list(target)
        source_set = set(source_keys)
        target_set = set(target_keys)

        for key in source_keys:
            key_path = child_path(path, key)
            if key not in target_set:
                add_finding(errors, "error", "missing_key", key_path)
            else:
                compare_values(
                    source[key],
                    target[key],
                    key_path,
                    errors,
                    reviews,
                    coverage,
                )

        for key in target_keys:
            if key not in source_set:
                add_finding(
                    errors,
                    "error",
                    "extra_key",
                    child_path(path, key),
                )

        if source_set == target_set and source_keys != target_keys:
            add_finding(
                errors,
                "error",
                "key_order_mismatch",
                path,
                expected=source_keys,
                actual=target_keys,
            )
        return

    if isinstance(source, list):
        if len(source) != len(target):
            add_finding(
                errors,
                "error",
                "array_length_mismatch",
                path,
                expected=len(source),
                actual=len(target),
            )
        for index, (source_item, target_item) in enumerate(zip(source, target)):
            compare_values(
                source_item,
                target_item,
                child_path(path, index),
                errors,
                reviews,
                coverage,
            )
        return

    if isinstance(source, str):
        source_tokens = extract_tokens(source)
        target_tokens = extract_tokens(target)
        if source_tokens != target_tokens:
            add_finding(
                errors,
                "error",
                "protected_token_mismatch",
                path,
                missing=list((source_tokens - target_tokens).elements()),
                extra=list((target_tokens - source_tokens).elements()),
            )
        classify_translation(
            source,
            target,
            path,
            errors,
            reviews,
            coverage,
        )
        return

    if source != target:
        add_finding(
            errors,
            "error",
            "scalar_value_mismatch",
            path,
            expected=source,
            actual=target,
        )


def aggregate_findings(
    findings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Merge findings that share kind and detail into one entry with all paths."""

    groups: dict[str, dict[str, Any]] = {}
    for finding in findings:
        detail = {
            key: value
            for key, value in finding.items()
            if key not in {"severity", "kind", "path"}
        }
        key = f"{finding['kind']}:{json.dumps(detail, ensure_ascii=False, sort_keys=True)}"
        group = groups.get(key)
        if group is None:
            group = {
                "severity": finding["severity"],
                "kind": finding["kind"],
                "paths": [],
                **detail,
            }
            groups[key] = group
        group["paths"].append(finding["path"])
    return list(groups.values())


def audit(
    source_path: Path,
    target_path: Path,
) -> dict[str, Any]:
    source = load_json_object(source_path)
    target = load_json_object(target_path)
    errors: list[dict[str, Any]] = []
    reviews: list[dict[str, Any]] = []
    source_string_paths = collect_string_paths(source)
    source_english_candidates = discover_source_english_candidates(source)
    coverage = {
        "total_strings": len(source_string_paths),
        "valid_chinese": 0,
        "non_linguistic": 0,
        "review_required": 0,
        "unresolved": 0,
    }

    compare_values(
        source,
        target,
        "/",
        errors,
        reviews,
        coverage,
    )
    resolved = (
        coverage["valid_chinese"]
        + coverage["non_linguistic"]
    )
    coverage["unresolved"] = coverage["total_strings"] - resolved
    coverage["percent"] = (
        100.0
        if coverage["total_strings"] == 0
        else round(100.0 * resolved / coverage["total_strings"], 2)
    )
    if errors:
        status = "differences"
    elif reviews:
        status = "review_required"
    else:
        status = "mechanical_parity"

    return {
        "status": status,
        "source": str(source_path),
        "target": str(target_path),
        "sourceEnglishCandidates": source_english_candidates,
        "summary": {
            "errors": len(errors),
            "reviews": len(reviews),
        },
        "coverage": coverage,
        "errors": aggregate_findings(errors),
        "reviews": aggregate_findings(reviews),
    }


def print_text_report(report: dict[str, Any]) -> None:
    print(f"status: {report['status']}")
    print(f"source: {report['source']}")
    print(f"target: {report['target']}")
    print(
        f"summary: {report['summary']['errors']} error(s), "
        f"{report['summary']['reviews']} review item(s)"
    )
    coverage = report["coverage"]
    print(
        "coverage: "
        f"{coverage['percent']}% "
        f"({coverage['total_strings']} total, "
        f"{coverage['unresolved']} unresolved)"
    )
    for section in ("errors", "reviews"):
        for finding in report[section]:
            detail = {
                key: value
                for key, value in finding.items()
                if key not in {"severity", "kind", "paths"}
            }
            suffix = f" {json.dumps(detail, ensure_ascii=False)}" if detail else ""
            print(
                f"{finding['severity'].upper()} "
                f"{finding['kind']} "
                f"{len(finding['paths'])} path(s): "
                f"{' '.join(finding['paths'])}{suffix}"
            )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Audit structural and common protected-token parity between an "
            "English source locale JSON file and a Chinese target file."
        )
    )
    parser.add_argument("source", type=Path, help="English source JSON")
    parser.add_argument("target", type=Path, help="Chinese target JSON")
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="report format (default: text)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = audit(args.source, args.target)
    except AuditInputError as exc:
        if args.format == "json":
            print(
                json.dumps(
                    {"status": "input_error", "message": str(exc)},
                    ensure_ascii=False,
                    indent=2,
                )
            )
        else:
            print(f"input error: {exc}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_text_report(report)
    if report["status"] == "mechanical_parity":
        return 0
    if report["status"] == "review_required":
        return 3
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
