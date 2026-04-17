"""Tests for the materialization infrastructure.

Covers snippet_parser, materialize_examples, and dematerialize_examples.
"""
from __future__ import annotations

import os
import subprocess
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

# Ensure scripts/ is importable
import sys

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from snippet_parser import FENCE_RE, ScriptBlock, iter_script_blocks, parse_pragmas

# Import the scripts (no .py extension) using importlib.util
import importlib.machinery
import importlib.util

_SCRIPTS_DIR = _REPO_ROOT / "scripts"


def _load_script(name: str):
    path = _SCRIPTS_DIR / name
    spec = importlib.util.spec_from_loader(
        name,
        importlib.machinery.SourceFileLoader(name, str(path)),
        origin=str(path),
    )
    mod = importlib.util.module_from_spec(spec)
    mod.__file__ = str(path)
    spec.loader.exec_module(mod)
    return mod


materialize_mod = _load_script("materialize_examples")
dematerialize_mod = _load_script("dematerialize_examples")


# ---------------------------------------------------------------------------
# Unit tests: snippet_parser
# ---------------------------------------------------------------------------


class TestParsePragmas:
    def test_single_pragma(self):
        code = "#!/bin/sh\n# pragma: testrun scenario-1\necho hello\n"
        result = parse_pragmas(code)
        assert result["testrun"] == "scenario-1"

    def test_multiple_string_pragmas(self):
        code = textwrap.dedent("""\
            #!/bin/sh
            # pragma: testrun scenario-2
            # pragma: requires sh awk make git
            # pragma: timeout 120
            echo hello
        """)
        result = parse_pragmas(code)
        assert result["testrun"] == "scenario-2"
        assert result["requires"] == "sh awk make git"
        assert result["timeout"] == "120"

    def test_single_materialize(self):
        code = "# pragma: testrun s1\n# pragma: materialize grocery-analysis\n"
        result = parse_pragmas(code)
        assert result["materialize"] == ["grocery-analysis"]

    def test_multiple_materialize(self):
        code = textwrap.dedent("""\
            # pragma: testrun scenario-4
            # pragma: materialize grocery-analysis
            # pragma: materialize raw-data-work
        """)
        result = parse_pragmas(code)
        assert result["materialize"] == ["grocery-analysis", "raw-data-work"]

    def test_no_pragmas(self):
        code = "#!/bin/sh\necho hello\n"
        result = parse_pragmas(code)
        assert result == {}

    def test_pragma_without_value(self):
        code = "# pragma: testrun\n"
        result = parse_pragmas(code)
        assert result["testrun"] == ""


class TestFenceRe:
    def test_matches_sh_block(self):
        md = "text\n```sh\necho hello\n```\nmore text\n"
        matches = list(FENCE_RE.finditer(md))
        assert len(matches) == 1
        assert "echo hello" in matches[0].group(1)

    def test_matches_bash_block(self):
        md = "text\n```bash\necho hello\n```\n"
        matches = list(FENCE_RE.finditer(md))
        assert len(matches) == 1

    def test_skips_other_languages(self):
        md = "```python\nprint('hi')\n```\n"
        matches = list(FENCE_RE.finditer(md))
        assert len(matches) == 0


class TestIterScriptBlocks:
    def test_yields_testrun_blocks(self, tmp_path):
        md = tmp_path / "example.md"
        md.write_text(textwrap.dedent("""\
            # Example

            ```sh
            # pragma: testrun demo-1
            # pragma: materialize myrepo
            echo hello
            ```

            ```sh
            # no pragma here
            echo world
            ```
        """))
        blocks = list(iter_script_blocks(md))
        assert len(blocks) == 1
        assert blocks[0].file_stem == "example"
        assert blocks[0].pragmas["testrun"] == "demo-1"
        assert blocks[0].pragmas["materialize"] == ["myrepo"]

    def test_file_stem_extraction(self, tmp_path):
        md = tmp_path / "stamped-awk-evolution.md"
        md.write_text("```sh\n# pragma: testrun s1\necho hi\n```\n")
        blocks = list(iter_script_blocks(md))
        assert blocks[0].file_stem == "stamped-awk-evolution"


# ---------------------------------------------------------------------------
# Unit tests: materialize_examples
# ---------------------------------------------------------------------------


class TestBranchName:
    def test_basic(self):
        result = materialize_mod.branch_name(
            "stamped-awk-evolution", "scenario-2", "grocery-analysis"
        )
        assert result == "examples/stamped-awk-evolution/scenario-2/grocery-analysis"

    def test_multiple_repos(self):
        b1 = materialize_mod.branch_name(
            "stamped-awk-evolution", "scenario-4", "grocery-analysis"
        )
        b2 = materialize_mod.branch_name(
            "stamped-awk-evolution", "scenario-4", "raw-data-work"
        )
        assert b1 != b2
        assert "scenario-4" in b1
        assert "scenario-4" in b2


class TestScriptHash:
    def test_deterministic(self):
        code = "echo hello\n"
        h1 = materialize_mod.script_hash(code)
        h2 = materialize_mod.script_hash(code)
        assert h1 == h2
        assert len(h1) == 64  # SHA-256 hex digest

    def test_different_content(self):
        h1 = materialize_mod.script_hash("echo hello\n")
        h2 = materialize_mod.script_hash("echo world\n")
        assert h1 != h2


class TestDetectRemoteUrl:
    def test_github_env(self):
        with patch.dict(os.environ, {"GITHUB_REPOSITORY": "stamped-principles/stamped-examples"}):
            url = materialize_mod.detect_remote_url("origin")
            assert url == "https://github.com/stamped-principles/stamped-examples"

    def test_git_remote(self):
        with patch.dict(os.environ, {}, clear=True):
            env = {k: v for k, v in os.environ.items() if k != "GITHUB_REPOSITORY"}
            with patch.dict(os.environ, env, clear=True):
                with patch("subprocess.run") as mock_run:
                    mock_run.return_value = subprocess.CompletedProcess(
                        args=[], returncode=0, stdout="git@github.com:foo/bar.git\n"
                    )
                    url = materialize_mod.detect_remote_url("origin")
                    assert url == "git@github.com:foo/bar.git"


class TestRewriteSubmoduleUrls:
    def test_rewrites_relative_url(self, tmp_path):
        repo = tmp_path / "myrepo"
        repo.mkdir()
        subprocess.run(["git", "init", str(repo)], check=True, capture_output=True)
        subprocess.run(
            ["git", "-C", str(repo), "config", "user.email", "test@test.com"],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(repo), "config", "user.name", "Test"],
            check=True,
            capture_output=True,
        )
        (repo / "dummy.txt").write_text("hello")
        subprocess.run(["git", "-C", str(repo), "add", "."], check=True, capture_output=True)
        subprocess.run(
            ["git", "-C", str(repo), "commit", "-m", "init"],
            check=True,
            capture_output=True,
        )

        gitmodules = repo / ".gitmodules"
        gitmodules.write_text(textwrap.dedent("""\
            [submodule "raw-data"]
            \tpath = raw-data
            \turl = ../raw-data.git
        """))
        subprocess.run(
            ["git", "-C", str(repo), "add", ".gitmodules"],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(repo), "commit", "-m", "add submodule ref"],
            check=True,
            capture_output=True,
        )

        materialize_mod.rewrite_submodule_urls(
            repo,
            "stamped-awk-evolution",
            "scenario-4",
            "https://github.com/stamped-principles/stamped-examples",
        )

        content = gitmodules.read_text()
        assert "https://github.com/stamped-principles/stamped-examples" in content
        assert "examples/stamped-awk-evolution/scenario-4/raw-data-work" in content
        assert "../raw-data.git" not in content


# ---------------------------------------------------------------------------
# Integration tests: local branch materialization
# ---------------------------------------------------------------------------


def _init_test_repo(path: Path) -> None:
    """Create a minimal git repo at *path* with content/examples/ dir."""
    subprocess.run(
        ["git", "init", "-b", "main", str(path)],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(path), "config", "user.email", "test@test.com"],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(path), "config", "user.name", "Test"],
        check=True,
        capture_output=True,
    )


def _write_test_md(path: Path, script_body: str = "echo hello") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(f"""\
        # Test

        ```sh
        #!/bin/sh
        # pragma: testrun demo-1
        # pragma: requires sh git
        # pragma: materialize myrepo
        set -eu
        cd "$(mktemp -d "${{TMPDIR:-/tmp}}/mat-test-XXXXXXX")"
        git init myrepo
        cd myrepo
        git config user.email "test@test.com"
        git config user.name "Test"
        echo "{script_body}" > file.txt
        git add -A
        git commit -m "init"
        ```
    """))


@pytest.mark.ai_generated
class TestMaterializeLocalBranch:
    """Test that materialization creates local branches + git notes."""

    def test_creates_local_branch(self, tmp_path, monkeypatch):
        repo = tmp_path / "repo"
        _init_test_repo(repo)
        content_dir = repo / "content" / "examples"
        _write_test_md(content_dir / "test-example.md")

        # Need an initial commit so git notes work
        (repo / "README.md").write_text("test")
        subprocess.run(
            ["git", "-C", str(repo), "add", "."],
            check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(repo), "commit", "-m", "init"],
            check=True, capture_output=True,
        )

        monkeypatch.chdir(repo)
        with patch.object(materialize_mod, "CONTENT_DIR", content_dir):
            materialize_mod.main([])

        # Branch should exist locally
        result = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "--verify",
             "refs/heads/examples/test-example/demo-1/myrepo"],
            capture_output=True,
        )
        assert result.returncode == 0, "Local branch was not created"

        # Branch should contain file.txt
        result = subprocess.run(
            ["git", "-C", str(repo), "show",
             "examples/test-example/demo-1/myrepo:file.txt"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert result.stdout.strip() == "echo hello"

    def test_no_marker_commits(self, tmp_path, monkeypatch):
        """The example branch should NOT have extra marker commits."""
        repo = tmp_path / "repo"
        _init_test_repo(repo)
        content_dir = repo / "content" / "examples"
        _write_test_md(content_dir / "test-example.md")

        (repo / "README.md").write_text("test")
        subprocess.run(
            ["git", "-C", str(repo), "add", "."],
            check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(repo), "commit", "-m", "init"],
            check=True, capture_output=True,
        )

        monkeypatch.chdir(repo)
        with patch.object(materialize_mod, "CONTENT_DIR", content_dir):
            materialize_mod.main([])

        # The branch should have exactly 1 commit (the "init" from the script)
        result = subprocess.run(
            ["git", "-C", str(repo), "rev-list", "--count",
             "examples/test-example/demo-1/myrepo"],
            capture_output=True,
            text=True,
        )
        assert result.stdout.strip() == "1", \
            f"Expected 1 commit, got {result.stdout.strip()}"

        # And that commit should NOT contain "Script-Hash"
        result = subprocess.run(
            ["git", "-C", str(repo), "log", "-1", "--format=%B",
             "examples/test-example/demo-1/myrepo"],
            capture_output=True,
            text=True,
        )
        assert "Script-Hash" not in result.stdout

    def test_hash_stored_in_git_notes(self, tmp_path, monkeypatch):
        """Script hash should be in a git note, not a commit."""
        repo = tmp_path / "repo"
        _init_test_repo(repo)
        content_dir = repo / "content" / "examples"
        _write_test_md(content_dir / "test-example.md")

        (repo / "README.md").write_text("test")
        subprocess.run(
            ["git", "-C", str(repo), "add", "."],
            check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(repo), "commit", "-m", "init"],
            check=True, capture_output=True,
        )

        monkeypatch.chdir(repo)
        with patch.object(materialize_mod, "CONTENT_DIR", content_dir):
            materialize_mod.main([])

        # Read the note on the branch tip
        tip = subprocess.run(
            ["git", "-C", str(repo), "rev-parse",
             "refs/heads/examples/test-example/demo-1/myrepo"],
            capture_output=True, text=True, check=True,
        )
        commit = tip.stdout.strip()

        note = subprocess.run(
            ["git", "-C", str(repo), "notes",
             f"--ref={materialize_mod.NOTES_REF}", "show", commit],
            capture_output=True, text=True,
        )
        assert note.returncode == 0
        assert "Script-Hash:" in note.stdout

    def test_cache_hit_skips_regeneration(self, tmp_path, monkeypatch, capsys):
        """Second run with same script content should say 'cache hit'."""
        repo = tmp_path / "repo"
        _init_test_repo(repo)
        content_dir = repo / "content" / "examples"
        _write_test_md(content_dir / "test-example.md")

        (repo / "README.md").write_text("test")
        subprocess.run(
            ["git", "-C", str(repo), "add", "."],
            check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(repo), "commit", "-m", "init"],
            check=True, capture_output=True,
        )

        monkeypatch.chdir(repo)
        with patch.object(materialize_mod, "CONTENT_DIR", content_dir):
            materialize_mod.main([])
            captured = capsys.readouterr()
            assert "cache hit" not in captured.out

            # Second run — should hit the cache
            materialize_mod.main([])
            captured = capsys.readouterr()
            assert "cache hit" in captured.out

    def test_content_change_regenerates(self, tmp_path, monkeypatch):
        """Changing script content should regenerate the branch."""
        repo = tmp_path / "repo"
        _init_test_repo(repo)
        content_dir = repo / "content" / "examples"
        md = content_dir / "test-example.md"

        (repo / "README.md").write_text("test")
        subprocess.run(
            ["git", "-C", str(repo), "add", "."],
            check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(repo), "commit", "-m", "init"],
            check=True, capture_output=True,
        )

        monkeypatch.chdir(repo)
        with patch.object(materialize_mod, "CONTENT_DIR", content_dir):
            _write_test_md(md, "version1")
            materialize_mod.main([])

            result = subprocess.run(
                ["git", "-C", str(repo), "show",
                 "examples/test-example/demo-1/myrepo:file.txt"],
                capture_output=True, text=True,
            )
            assert result.stdout.strip() == "version1"

            # Change content and re-run
            _write_test_md(md, "version2")
            materialize_mod.main([])

            result = subprocess.run(
                ["git", "-C", str(repo), "show",
                 "examples/test-example/demo-1/myrepo:file.txt"],
                capture_output=True, text=True,
            )
            assert result.stdout.strip() == "version2"


@pytest.mark.ai_generated
class TestMaterializeWorktree:
    """The --worktrees-under mode still works."""

    def test_worktree_creation(self, tmp_path):
        content_dir = tmp_path / "content" / "examples"
        _write_test_md(content_dir / "test-example.md")

        worktrees = tmp_path / "worktrees"

        with patch.object(materialize_mod, "CONTENT_DIR", content_dir):
            materialize_mod.main(["--worktrees-under", str(worktrees)])

        expected = worktrees / "examples" / "test-example" / "demo-1" / "myrepo"
        assert expected.is_dir(), f"Expected worktree at {expected}"
        assert (expected / "file.txt").exists()
        assert (expected / "file.txt").read_text().strip() == "echo hello"


# ---------------------------------------------------------------------------
# Tests for dematerialize_examples
# ---------------------------------------------------------------------------


@pytest.mark.ai_generated
class TestDematerialize:
    """Test local (and remote) branch deletion."""

    @staticmethod
    def _setup_repo_with_local_branches(tmp_path: Path) -> Path:
        """Create a repo with local example branches."""
        repo = tmp_path / "repo"
        _init_test_repo(repo)
        (repo / "README.md").write_text("test")
        subprocess.run(
            ["git", "-C", str(repo), "add", "."],
            check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(repo), "commit", "-m", "init"],
            check=True, capture_output=True,
        )

        # Create local example branches
        for branch in [
            "examples/test/demo-1/myrepo",
            "examples/test/demo-2/myrepo",
        ]:
            subprocess.run(
                ["git", "-C", str(repo), "branch", branch],
                check=True, capture_output=True,
            )

        # Add a note to one branch tip so we test note pruning
        tip = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True,
        )
        subprocess.run(
            ["git", "-C", str(repo), "notes",
             f"--ref={dematerialize_mod.NOTES_REF}", "add", "-m",
             "Script-Hash: abc123", tip.stdout.strip()],
            check=True, capture_output=True,
        )

        return repo

    def test_list_local_branches(self, tmp_path):
        repo = self._setup_repo_with_local_branches(tmp_path)
        result = subprocess.run(
            ["git", "-C", str(repo), "branch", "--list", "examples/*",
             "--format=%(refname:short)"],
            capture_output=True, text=True,
        )
        branches = [b.strip() for b in result.stdout.splitlines() if b.strip()]
        assert len(branches) == 2
        assert "examples/test/demo-1/myrepo" in branches

    def test_dry_run_preserves_branches(self, tmp_path, monkeypatch):
        repo = self._setup_repo_with_local_branches(tmp_path)
        monkeypatch.chdir(repo)

        dematerialize_mod.main(["--dry-run"])

        result = subprocess.run(
            ["git", "branch", "--list", "examples/*",
             "--format=%(refname:short)"],
            capture_output=True, text=True,
        )
        branches = [b.strip() for b in result.stdout.splitlines() if b.strip()]
        assert len(branches) == 2

    def test_delete_local_branches(self, tmp_path, monkeypatch):
        repo = self._setup_repo_with_local_branches(tmp_path)
        monkeypatch.chdir(repo)

        dematerialize_mod.main([])

        result = subprocess.run(
            ["git", "branch", "--list", "examples/*",
             "--format=%(refname:short)"],
            capture_output=True, text=True,
        )
        branches = [b.strip() for b in result.stdout.splitlines() if b.strip()]
        assert len(branches) == 0

    def test_notes_pruned(self, tmp_path, monkeypatch):
        repo = self._setup_repo_with_local_branches(tmp_path)
        monkeypatch.chdir(repo)

        dematerialize_mod.main([])

        result = subprocess.run(
            ["git", "notes", f"--ref={dematerialize_mod.NOTES_REF}", "list"],
            capture_output=True, text=True,
        )
        assert result.stdout.strip() == ""
