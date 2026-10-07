#!/usr/bin/env python3
"""Exercise Pixi/DataLad replay in a retained, disposable macOS ARM workspace.

Requires Pixi, Git, and Python 3.11+ for the driver. Analysis dependencies are
installed into the fixture's Pixi environment. This does not fetch Gaia data.
Pass a helper that prints commit provenance trailers before each commit.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shlex
import subprocess
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provenance-helper", type=Path, required=True)
    parser.add_argument("--directory", type=Path)
    args = parser.parse_args()
    if (platform.system(), platform.machine()) != ("Darwin", "arm64"):
        parser.error("This bounded fixture currently targets macOS ARM only.")
    root = args.directory or Path(tempfile.mkdtemp(prefix="pixi-datalad-replay-"))
    root.mkdir(parents=True, exist_ok=True)
    if list(root.iterdir()):
        parser.error("Use an empty directory.")
    project = root / "study"
    print(f"FIXTURE: {root}", flush=True)
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["DATALAD_UI_INTERACTIVE"] = "0"
    cases = []
    summary = {"fixture": str(root), "cases": cases}

    def run(*command, cwd=None, capture=False, extra_env=None):
        print("+ " + shlex.join(map(str, command)), flush=True)
        result = subprocess.run(
            list(map(str, command)), cwd=cwd or project,
            env=env | (extra_env or {}), text=True, check=True,
            stdout=subprocess.PIPE if capture else None,
        )
        return result.stdout.strip() if capture else None

    def message(subject):
        trailers = subprocess.check_output(
            [str(args.provenance_helper.resolve())], text=True
        ).strip()
        if "Co-Authored-By:" not in trailers or "Codex-Reasoning-Effort:" not in trailers:
            raise RuntimeError("Provenance helper did not provide required trailers")
        return subject + "\n\n" + trailers

    def git(*command, **kwargs):
        return run("git", *command, **kwargs)

    def pixi(*command, **kwargs):
        return run("pixi", *command, **kwargs)

    def commit(subject):
        git("add", "data.txt", "calc.py", "pixi.toml", "pixi.lock", ".gitignore", ".gitattributes")
        git("commit", "-m", message(subject))

    def save_summary():
        (root / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")

    def observe(name, value, multiplier, package, mode):
        actual = json.loads((project / "result.json").read_text())
        expected = {"value": value, "multiplier": multiplier,
                    "result": value * multiplier, "packaging": package,
                    "mode": mode}
        row = {"case": name, "expected": expected, "actual": actual,
               "passed": actual == expected,
               "manifest_sha256": hashlib.sha256((project / "pixi.toml").read_bytes()).hexdigest(),
               "lock_sha256": hashlib.sha256((project / "pixi.lock").read_bytes()).hexdigest(),
               "head": git("rev-parse", "HEAD", capture=True)}
        cases.append(row)
        save_summary()
        assert row["passed"], row
        print("PASS " + name + " " + json.dumps(actual), flush=True)

    def replay(mode, case, *options):
        assert not git("status", "--porcelain", capture=True), "Replay needs a clean fixture"
        pixi("run", "--locked", "--", "datalad", "rerun", *options,
             "-m", message("test: replay " + case), mode + "-run")

    def select(mode):
        git("checkout", "--detach", mode + "-run")
        pixi("install", "--locked")

    def new_deps():
        manifest = project / "pixi.toml"
        manifest.write_text(manifest.read_text().replace('"==24.2"', '"==25.0"'))
        pixi("install")
        commit("test: select packaging 25.0")

    pixi("init", str(project), cwd=root)
    (project / "pixi.toml").write_text('''[workspace]
name = "pixi-datalad-replay"
channels = ["conda-forge"]
platforms = [{ platform = "osx-arm64", macos = "14.0" }]

[dependencies]
python = "3.12.*"
git = "*"

[pypi-dependencies]
datalad = "==1.7.1"
git-annex = "*"
packaging = "==24.2"

[tasks.record-direct]
cmd = 'datalad run --explicit -m "$REPLAY_MESSAGE" -i data.txt -i calc.py -i pixi.toml -i pixi.lock -o result.json -- python calc.py direct'

[tasks.record-pixi]
cmd = 'datalad run --explicit -m "$REPLAY_MESSAGE" -i data.txt -i calc.py -i pixi.toml -i pixi.lock -o result.json -- pixi run --locked -- python calc.py pixi'
''')
    (project / ".gitignore").write_text(".pixi/\n")
    (project / "data.txt").write_text("2\n")
    (project / "calc.py").write_text('''import json
from pathlib import Path
import sys
import packaging
from packaging.version import Version

multiplier = 3
value = int(Path("data.txt").read_text())
result = dict(value=value, multiplier=multiplier, result=value * multiplier,
              packaging=str(Version(packaging.__version__)), mode=sys.argv[1])
Path("result.json").write_text(json.dumps(result, sort_keys=True) + "\\n")
print(json.dumps(result, sort_keys=True))
''')
    pixi("install")
    summary["versions"] = {
        "pixi": pixi("--version", capture=True),
        "datalad": pixi("run", "--locked", "--", "datalad", "--version", capture=True),
        "python": pixi("run", "--locked", "--", "python", "--version", capture=True),
        "annex": pixi("run", "--locked", "--", "git", "annex", "version", capture=True),
        "host": platform.platform(),
    }
    pixi("run", "--locked", "--", "python", "-c",
         "import sys,datalad; print(sys.executable); print(datalad.__version__)")
    git("init")
    git("config", "user.name", "Replay fixture")
    git("config", "user.email", "codex@openai.com")
    git("config", "commit.gpgsign", "false")
    commit("test: prepare baseline replay fixture")
    git("tag", "initial")

    for mode in ("direct", "pixi"):
        git("checkout", "--detach", "initial")
        pixi("install", "--locked")
        pixi("run", "--locked", "record-" + mode,
             extra_env={"REPLAY_MESSAGE": message("test: record " + mode + " baseline")})
        git("tag", mode + "-run")
        observe(mode + "/baseline", 2, 3, "24.2", mode)

        (project / "data.txt").write_text("5\n")
        commit("test: change only input data")
        git("tag", mode + "-data")
        replay(mode, "changed data")
        observe(mode + "/data-at-head", 5, 3, "24.2", mode)

        select(mode)
        code = project / "calc.py"
        code.write_text(code.read_text().replace("multiplier = 3", "multiplier = 4"))
        commit("test: change only calculation code")
        replay(mode, "changed code")
        observe(mode + "/code-at-head", 2, 4, "24.2", mode)

        select(mode)
        new_deps()
        git("tag", mode + "-deps")
        replay(mode, "changed dependencies")
        observe(mode + "/deps-at-head", 2, 3, "25.0", mode)

        git("checkout", "--detach", mode + "-deps")
        pixi("install", "--locked")
        replay(mode, "historical onto from newer environment", "--onto=",
               "--branch", mode + "-historical")
        observe(mode + "/onto-from-new-env", 2, 3,
                "25.0" if mode == "direct" else "24.2", mode)

        select(mode)
        replay(mode, "historical onto after environment selection", "--onto=",
               "--branch", mode + "-preselected")
        observe(mode + "/onto-after-precheckout", 2, 3, "24.2", mode)

        select(mode)
        replay(mode, "explicit changed-data base", "--onto", mode + "-data",
               "--branch", mode + "-explicit-data")
        observe(mode + "/onto-explicit-data", 5, 3, "24.2", mode)

    # Recreate the preferred-pattern environment in a separate fresh clone.
    fresh = root / "fresh"
    git("clone", "--no-local", str(project), str(fresh), cwd=root)
    git("checkout", "--detach", "direct-run", cwd=fresh)
    git("config", "user.name", "Replay fixture", cwd=fresh)
    git("config", "user.email", "codex@openai.com", cwd=fresh)
    git("config", "commit.gpgsign", "false", cwd=fresh)
    assert not (fresh / ".pixi").exists()
    project = fresh
    replay("direct", "fresh environment", "--onto=", "--branch", "fresh-replay")
    observe("direct/fresh-clone-onto", 2, 3, "24.2", "direct")
    summary["status"] = "passed"
    save_summary()
    print(f"ALL {len(cases)} CASES PASSED; evidence: {root / 'summary.json'}", flush=True)


if __name__ == "__main__":
    main()
