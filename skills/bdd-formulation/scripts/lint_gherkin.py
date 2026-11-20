#!/usr/bin/env python3
"""Dependency-free Gherkin syntax and BRIEF heuristic linter.

Validates .feature files for structural Gherkin correctness (errors) and
BRIEF specification quality heuristics (warnings).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable

FEATURE_RE = re.compile(r"^Feature:\s*(.*)$")
RULE_RE = re.compile(r"^Rule:\s*(.*)$")
BACKGROUND_RE = re.compile(r"^Background:\s*(.*)$")
SCENARIO_RE = re.compile(r"^(?:Scenario|Example):\s*(.*)$")
OUTLINE_RE = re.compile(r"^Scenario\s+(?:Outline|Template):\s*(.*)$")
EXAMPLES_RE = re.compile(r"^(?:Examples|Scenarios):\s*(.*)$")
STEP_RE = re.compile(r"^(Given|When|Then|And|But|\*)\s*(.*)$")
TAG_RE = re.compile(r"^@")

PRIMARY_KEYWORDS = {"Given", "When", "Then"}

IMPERATIVE_UI_RE = re.compile(
    r"\b(?:click|clicks|double-click|hover|dropdown|checkbox|radio button|"
    r"text box|input field|xpath|css selector|locator|modal dialog)\b"
    r"|(?:[\"'])#[a-zA-Z][a-zA-Z0-9_-]*(?:[\"'])"
    r"|(?:^|\s)#[a-zA-Z][a-zA-Z0-9_-]+\b",
    re.IGNORECASE,
)

HTTP_VERB_PATH_RE = re.compile(r"\b(?:GET|POST|PUT|PATCH|DELETE)\s+/")
TECHNICAL_LEAKAGE_RE = re.compile(
    r"(?:\bstatus\s+code\s+\d{3}\b|https?://|\b(?:SQL|SELECT\s+\*|database\s+table|"
    r"foreign\s+key|JSON\s+payload|localStorage|sessionStorage)\b)",
    re.IGNORECASE,
)
PLACEHOLDER_DATA_RE = re.compile(
    r"\b(?:foo|bar|baz|foobar|asdf|qwerty|test123)\b",
    re.IGNORECASE,
)
VAGUE_TITLE_RE = re.compile(r"^(?:test|verify\s+that|check)\b", re.IGNORECASE)
PLACEHOLDER_TOKEN_RE = re.compile(r"<([^<>\n\r]+)>")


@dataclass
class Issue:
    file: str
    line: int
    severity: str  # "error" | "warning"
    code: str
    message: str


@dataclass
class ExampleTable:
    line: int
    headers: list[str] | None = None
    row_count: int = 0


@dataclass
class BlockState:
    kind: str  # "background" | "scenario" | "outline"
    line: int
    title: str
    step_count: int = 0
    last_primary: str | None = None
    has_when: bool = False
    has_then: bool = False
    seen_then: bool = False
    reported_multi_when: bool = False
    placeholders: set[str] = field(default_factory=set)
    examples: list[ExampleTable] = field(default_factory=list)
    in_examples: bool = False


def split_table_row(stripped: str) -> list[str] | None:
    """Split a Gherkin data table row on unescaped '|', returning cell values or None if malformed."""
    if not stripped.startswith("|"):
        return None
    cells: list[str] = []
    current: list[str] = []
    pipe_positions: list[int] = []
    i = 0
    n = len(stripped)
    while i < n:
        ch = stripped[i]
        if ch == "\\" and i + 1 < n:
            current.append(ch)
            current.append(stripped[i + 1])
            i += 2
            continue
        if ch == "|":
            pipe_positions.append(i)
            if len(pipe_positions) > 1:
                cells.append("".join(current).strip())
                current = []
            i += 1
            continue
        current.append(ch)
        i += 1

    # Must end with an unescaped '|' (trailing comment after table row isn't standard Gherkin)
    if not pipe_positions or pipe_positions[-1] != n - 1 or len(pipe_positions) < 2:
        return None
    return cells


def extract_placeholders(text: str) -> set[str]:
    return {match.group(1).strip() for match in PLACEHOLDER_TOKEN_RE.finditer(text) if match.group(1).strip()}


def lint_file(path: Path) -> list[Issue]:
    issues: list[Issue] = []
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    file_str = str(path)

    feature_count = 0
    in_feature = False
    current_block: BlockState | None = None
    docstring_fence: str | None = None
    docstring_start_line = 0
    active_table_cols: int | None = None
    active_table_is_examples = False

    def add_issue(line_no: int, severity: str, code: str, message: str) -> None:
        issues.append(Issue(file=file_str, line=line_no, severity=severity, code=code, message=message))

    def check_step_heuristics(line_no: int, step_body: str) -> None:
        if IMPERATIVE_UI_RE.search(step_body):
            add_issue(
                line_no,
                "warning",
                "IMPERATIVE_UI",
                f"Step leaks UI mechanics or selectors: {step_body!r}",
            )
        if HTTP_VERB_PATH_RE.search(step_body) or TECHNICAL_LEAKAGE_RE.search(step_body):
            add_issue(
                line_no,
                "warning",
                "TECHNICAL_LEAKAGE",
                f"Step exposes HTTP/SQL/storage implementation details: {step_body!r}",
            )
        if PLACEHOLDER_DATA_RE.search(step_body):
            add_issue(
                line_no,
                "warning",
                "PLACEHOLDER_DATA",
                f"Step uses generic placeholder data instead of domain values: {step_body!r}",
            )

    def finalize_block() -> None:
        nonlocal current_block, active_table_cols, active_table_is_examples
        active_table_cols = None
        active_table_is_examples = False
        if current_block is None:
            return
        blk = current_block
        current_block = None

        if blk.kind == "background":
            if blk.step_count > 4:
                add_issue(
                    blk.line,
                    "warning",
                    "BACKGROUND_TOO_LONG",
                    f"Background has {blk.step_count} steps (limit <= 4 to avoid incidental detail).",
                )
            return

        # Scenario or Scenario Outline
        if not blk.title.strip():
            add_issue(blk.line, "warning", "VAGUE_TITLE", "Scenario title is empty.")
        elif VAGUE_TITLE_RE.search(blk.title.strip()):
            add_issue(
                blk.line,
                "warning",
                "VAGUE_TITLE",
                f"Scenario title {blk.title!r} describes testing mechanics rather than behavior.",
            )

        if not blk.has_when:
            add_issue(blk.line, "error", "MISSING_WHEN", f"Scenario {blk.title!r} is missing a 'When' step.")
        if not blk.has_then:
            add_issue(blk.line, "error", "MISSING_THEN", f"Scenario {blk.title!r} is missing a 'Then' step.")
        if blk.step_count > 7:
            add_issue(
                blk.line,
                "warning",
                "SCENARIO_TOO_LONG",
                f"Scenario {blk.title!r} has {blk.step_count} steps (recommended <= 7).",
            )

        if blk.kind == "outline":
            if not blk.examples:
                add_issue(
                    blk.line,
                    "error",
                    "MISSING_EXAMPLES",
                    f"Scenario Outline {blk.title!r} has no 'Examples:' table.",
                )
            else:
                all_headers: set[str] = set()
                for ex in blk.examples:
                    if ex.headers is None or ex.row_count == 0:
                        add_issue(
                            ex.line,
                            "error",
                            "EMPTY_EXAMPLES",
                            "Examples block must contain a header row and at least one data row.",
                        )
                        continue
                    header_set = set(ex.headers)
                    all_headers.update(header_set)
                    missing = sorted(blk.placeholders - header_set)
                    for name in missing:
                        add_issue(
                            ex.line,
                            "error",
                            "UNDEFINED_PLACEHOLDER",
                            f"Placeholder <{name}> used in Scenario Outline is missing from Examples header.",
                        )
                if all_headers:
                    unused = sorted(all_headers - blk.placeholders)
                    for col in unused:
                        add_issue(
                            blk.examples[0].line,
                            "error",
                            "UNUSED_EXAMPLE_COLUMN",
                            f"Examples column {col!r} is never referenced as <{col}> in Scenario Outline.",
                        )

    for idx, raw_line in enumerate(lines, start=1):
        stripped = raw_line.strip()

        # Handle multiline docstrings cleanly
        if docstring_fence is not None:
            if stripped.startswith(docstring_fence):
                docstring_fence = None
            elif current_block and current_block.kind == "outline" and not current_block.in_examples:
                # Scan docstrings for explicit <placeholder> tokens that look like identifiers
                for token in extract_placeholders(raw_line):
                    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_ -]*", token):
                        current_block.placeholders.add(token)
            continue

        if stripped.startswith('"""') or stripped.startswith("```"):
            docstring_fence = stripped[:3]
            docstring_start_line = idx
            active_table_cols = None
            active_table_is_examples = False
            continue

        if not stripped or stripped.startswith("#"):
            continue

        if TAG_RE.match(stripped):
            active_table_cols = None
            active_table_is_examples = False
            continue

        # Data table / Examples table row
        if stripped.startswith("|"):
            cells = split_table_row(stripped)
            if cells is None:
                add_issue(idx, "error", "MALFORMED_TABLE", "Malformed Gherkin table row (missing closing '|').")
                continue

            if active_table_cols is None:
                active_table_cols = len(cells)
                if current_block and current_block.in_examples and current_block.examples:
                    ex = current_block.examples[-1]
                    if ex.headers is None:
                        ex.headers = cells
                        active_table_is_examples = True
                    else:
                        ex.row_count += 1
                        active_table_is_examples = True
            else:
                if len(cells) != active_table_cols:
                    add_issue(
                        idx,
                        "error",
                        "MALFORMED_TABLE",
                        f"Table row has {len(cells)} columns; expected {active_table_cols}.",
                    )
                if active_table_is_examples and current_block and current_block.examples:
                    current_block.examples[-1].row_count += 1

            # Check placeholders inside step data tables and placeholder words in data rows
            if current_block:
                is_header = (
                    active_table_is_examples
                    and current_block.examples
                    and current_block.examples[-1].row_count == 0
                )
                if current_block.kind == "outline" and not current_block.in_examples:
                    for cell in cells:
                        current_block.placeholders.update(extract_placeholders(cell))
                if not is_header:
                    row_joined = " ".join(cells)
                    if PLACEHOLDER_DATA_RE.search(row_joined):
                        add_issue(
                            idx,
                            "warning",
                            "PLACEHOLDER_DATA",
                            f"Table row uses generic placeholder data: {stripped!r}",
                        )
            continue

        # Any non-table line ends an active table
        active_table_cols = None
        active_table_is_examples = False

        if FEATURE_RE.match(stripped):
            finalize_block()
            feature_count += 1
            in_feature = True
            if feature_count > 1:
                add_issue(idx, "error", "MULTIPLE_FEATURES", "File contains more than one 'Feature:' declaration.")
            continue

        if RULE_RE.match(stripped):
            finalize_block()
            if not in_feature:
                add_issue(idx, "error", "RULE_OUTSIDE_FEATURE", "'Rule:' appears before 'Feature:'.")
            continue

        if BACKGROUND_RE.match(stripped):
            finalize_block()
            if not in_feature:
                add_issue(idx, "error", "BLOCK_OUTSIDE_FEATURE", "'Background:' appears before 'Feature:'.")
            current_block = BlockState(kind="background", line=idx, title="Background")
            continue

        m_outline = OUTLINE_RE.match(stripped)
        if m_outline:
            finalize_block()
            if not in_feature:
                add_issue(idx, "error", "BLOCK_OUTSIDE_FEATURE", "'Scenario Outline:' appears before 'Feature:'.")
            current_block = BlockState(kind="outline", line=idx, title=m_outline.group(1).strip())
            continue

        m_scenario = SCENARIO_RE.match(stripped)
        if m_scenario:
            finalize_block()
            if not in_feature:
                add_issue(idx, "error", "BLOCK_OUTSIDE_FEATURE", "'Scenario:' appears before 'Feature:'.")
            current_block = BlockState(kind="scenario", line=idx, title=m_scenario.group(1).strip())
            continue

        if EXAMPLES_RE.match(stripped):
            if current_block is None or current_block.kind != "outline":
                add_issue(idx, "error", "EXAMPLES_OUTSIDE_OUTLINE", "'Examples:' must appear inside a Scenario Outline.")
            else:
                current_block.in_examples = True
                current_block.examples.append(ExampleTable(line=idx))
            continue

        m_step = STEP_RE.match(stripped)
        if m_step:
            keyword, body = m_step.group(1), m_step.group(2)
            if current_block is None:
                add_issue(
                    idx,
                    "error",
                    "STEP_OUTSIDE_BLOCK",
                    f"Step {stripped!r} appears outside a Background, Scenario, or Scenario Outline.",
                )
                continue
            if current_block.in_examples:
                add_issue(
                    idx,
                    "error",
                    "STEP_AFTER_EXAMPLES",
                    f"Step {stripped!r} appears after 'Examples:' in Scenario Outline.",
                )
                continue

            current_block.step_count += 1
            if keyword in PRIMARY_KEYWORDS:
                resolved = keyword
                current_block.last_primary = keyword
            else:
                resolved = current_block.last_primary or "Given"

            if current_block.kind == "background":
                if resolved in {"When", "Then"}:
                    add_issue(
                        idx,
                        "error",
                        "INVALID_BACKGROUND_STEP",
                        f"Background may only contain 'Given' preconditions (found {keyword} resolving to {resolved}).",
                    )
            else:
                if resolved == "When":
                    current_block.has_when = True
                    if current_block.seen_then and keyword == "When" and not current_block.reported_multi_when:
                        current_block.reported_multi_when = True
                        add_issue(
                            idx,
                            "warning",
                            "MULTIPLE_WHEN_THEN",
                            "Scenario contains a 'When' after a 'Then'; split multi-behavior journeys into separate scenarios.",
                        )
                elif resolved == "Then":
                    current_block.has_then = True
                    current_block.seen_then = True

            if current_block.kind == "outline":
                current_block.placeholders.update(extract_placeholders(body))

            check_step_heuristics(idx, body)
            continue

    if docstring_fence is not None:
        add_issue(
            docstring_start_line,
            "error",
            "UNCLOSED_DOCSTRING",
            f"Docstring starting with {docstring_fence} was never closed.",
        )

    finalize_block()

    if feature_count == 0:
        add_issue(1, "error", "NO_FEATURE", "File is missing a 'Feature:' declaration.")

    return issues


def collect_feature_files(paths: Iterable[str]) -> list[Path]:
    collected: list[Path] = []
    seen: set[Path] = set()
    for raw in paths:
        p = Path(raw)
        if not p.exists():
            raise FileNotFoundError(f"Path not found: {raw}")
        if p.is_file():
            resolved = p.resolve()
            if resolved not in seen:
                seen.add(resolved)
                collected.append(p)
        else:
            for item in sorted(p.rglob("*.feature")):
                resolved = item.resolve()
                if resolved not in seen:
                    seen.add(resolved)
                    collected.append(item)
    return collected


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Lint Gherkin .feature files for syntax and BRIEF quality.")
    parser.add_argument("paths", nargs="+", help="Feature files or directories to scan recursively for *.feature")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero on warnings as well as errors.")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Emit machine-readable JSON output.")
    args = parser.parse_args(argv)

    try:
        files = collect_feature_files(args.paths)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if not files:
        print("error: no .feature files found.", file=sys.stderr)
        return 2

    all_issues: list[Issue] = []
    for fpath in files:
        all_issues.extend(lint_file(fpath))

    errors = sum(1 for i in all_issues if i.severity == "error")
    warnings = sum(1 for i in all_issues if i.severity == "warning")

    if args.as_json:
        payload = {
            "files_checked": len(files),
            "errors": errors,
            "warnings": warnings,
            "issues": [asdict(i) for i in all_issues],
        }
        print(json.dumps(payload, indent=2))
    else:
        for issue in all_issues:
            print(f"{issue.file}:{issue.line}: {issue.severity.upper()} [{issue.code}] {issue.message}")
        print(f"Checked {len(files)} file(s): {errors} error(s), {warnings} warning(s).")

    if errors > 0 or (args.strict and warnings > 0):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
