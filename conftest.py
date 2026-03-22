"""sybil conftest: test shell script snippets embedded in Markdown examples.

Code blocks annotated with ``# pragma: testrun`` are extracted and executed.
See the plan at .claude/plans/ for the full annotation format.
"""
from __future__ import annotations

import os
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
from sybil import Document, Region, Sybil

sys.path.insert(0, str(Path(__file__).resolve().parent / "scripts"))
from snippet_parser import FENCE_RE, _merge_pragmas, parse_pragmas


def shell_script_parser(document: Document):
    """Find ``sh`` code blocks containing ``# pragma: testrun`` and yield Regions.

    Multiple blocks sharing the same ``testrun`` ID are concatenated
    (in document order) into a single Region so they execute as one script.
    """
    groups: dict[str, dict] = {}
    order: list[str] = []

    for m in FENCE_RE.finditer(document.text):
        code = m.group(1)
        if "# pragma: testrun" not in code:
            continue
        pragmas = parse_pragmas(code)
        testrun_id = pragmas.get("testrun", "unnamed")

        if testrun_id not in groups:
            groups[testrun_id] = {
                "codes": [], "pragmas": {},
                "start": m.start(), "end": m.end(),
            }
            order.append(testrun_id)

        groups[testrun_id]["codes"].append(code)
        groups[testrun_id]["end"] = m.end()
        _merge_pragmas(groups[testrun_id]["pragmas"], pragmas)

    for testrun_id in order:
        group = groups[testrun_id]
        combined = "\n".join(group["codes"])
        yield Region(
            start=group["start"],
            end=group["end"],
            parsed={"code": combined, "pragmas": group["pragmas"]},
            evaluator=evaluate_shell_script,
        )


def evaluate_shell_script(example):
    """Run a shell script extracted from markdown and check it succeeds."""
    code = example.parsed["code"]
    pragmas = example.parsed["pragmas"]

    # Check tool requirements
    requires = pragmas.get("requires", "sh").split()
    missing = [t for t in requires if not shutil.which(t)]
    if missing:
        pytest.skip(f"missing: {', '.join(missing)}")

    timeout = int(pragmas.get("timeout", "60"))
    test_id = pragmas.get("testrun", "unnamed")

    # Write to temp file and execute
    fd, path = tempfile.mkstemp(suffix=".sh", prefix=f"sybil-{test_id}-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(code)
        os.chmod(path, os.stat(path).st_mode | stat.S_IEXEC)
        result = subprocess.run(
            ["sh", path],
            timeout=timeout,
        )
        expected_rc = int(pragmas.get("exitcode", "0"))
        if result.returncode != expected_rc:
            raise AssertionError(
                f"Script {test_id} exited with code {result.returncode}"
                f" (expected {expected_rc})"
            )
    except subprocess.TimeoutExpired:
        raise AssertionError(f"Script {test_id} timed out after {timeout}s")
    finally:
        os.unlink(path)


pytest_collect_file = Sybil(
    parsers=[shell_script_parser],
    patterns=["content/examples/*.md"],
).pytest()
