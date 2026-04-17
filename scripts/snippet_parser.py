"""Shared parsing utilities for shell script snippets in Markdown examples.

Extracts fenced ``sh``/``bash`` code blocks and their ``# pragma:`` annotations.
Used by both ``conftest.py`` (Sybil test runner) and ``materialize_examples``
(branch materializer).
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Iterator, NamedTuple

# Regex: fenced code block with sh or bash language tag.
# Captures the code content between the opening and closing fences.
FENCE_RE = re.compile(
    r"^```(?:sh|bash)\s*\n(.*?)^```",
    re.MULTILINE | re.DOTALL,
)


def parse_pragmas(code: str) -> dict[str, str | list[str]]:
    """Extract ``# pragma: key value`` directives from script text.

    Most keys map to a single string value.  ``materialize`` may appear
    multiple times and is always returned as a list.
    """
    pragmas: dict[str, str | list[str]] = {}
    for line in code.splitlines():
        stripped = line.strip()
        if stripped.startswith("# pragma:"):
            # e.g. "# pragma: testrun scenario-1"
            parts = stripped.split(None, 3)  # ['#', 'pragma:', key, value...]
            if len(parts) >= 3:
                key = parts[2]
                value = parts[3] if len(parts) > 3 else ""
                if key == "materialize":
                    pragmas.setdefault("materialize", [])
                    assert isinstance(pragmas["materialize"], list)
                    pragmas["materialize"].append(value)
                else:
                    pragmas[key] = value
    return pragmas


class ScriptBlock(NamedTuple):
    """A fenced shell code block extracted from a Markdown file."""

    code: str
    pragmas: dict[str, str | list[str]]
    file_stem: str


def _merge_pragmas(
    target: dict[str, str | list[str]],
    source: dict[str, str | list[str]],
) -> None:
    """Merge *source* pragmas into *target* (first-wins for scalars)."""
    for k, v in source.items():
        if k == "materialize":
            target.setdefault("materialize", [])
            assert isinstance(target["materialize"], list)
            assert isinstance(v, list)
            target["materialize"].extend(v)
        elif k not in target:
            target[k] = v


def iter_script_blocks(md_path: str | Path) -> Iterator[ScriptBlock]:
    """Yield :class:`ScriptBlock` instances from a Markdown file.

    Only blocks containing ``# pragma: testrun`` are yielded.

    When multiple blocks share the same ``testrun`` identifier they are
    concatenated (in document order) into a single :class:`ScriptBlock`.
    Scalar pragmas use first-wins semantics; ``materialize`` lists are
    concatenated.
    """
    md_path = Path(md_path)
    text = md_path.read_text(encoding="utf-8")
    file_stem = md_path.stem

    groups: dict[str, dict] = {}  # testrun_id -> {"codes": [...], "pragmas": {...}}
    order: list[str] = []

    for m in FENCE_RE.finditer(text):
        code = m.group(1)
        if "# pragma: testrun" not in code:
            continue
        pragmas = parse_pragmas(code)
        testrun_id = pragmas.get("testrun", "")

        if testrun_id not in groups:
            groups[testrun_id] = {"codes": [], "pragmas": {}}
            order.append(testrun_id)

        groups[testrun_id]["codes"].append(code)
        _merge_pragmas(groups[testrun_id]["pragmas"], pragmas)

    for testrun_id in order:
        group = groups[testrun_id]
        combined = "\n".join(group["codes"])
        yield ScriptBlock(code=combined, pragmas=group["pragmas"], file_stem=file_stem)
