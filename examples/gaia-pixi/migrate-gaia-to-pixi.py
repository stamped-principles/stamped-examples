"""Adapt the completed Gaia project without replacing its Python metadata."""
from pathlib import Path

import tomlkit

def migrate():
    path = Path("pyproject.toml")
    project = tomlkit.parse(path.read_text())
    project.setdefault("tool", {})["pixi"] = {
        "workspace": {
            "channels": ["conda-forge"],
            "platforms": [
                {"platform": "linux-64", "glibc": "2.34"},
                {"platform": "osx-arm64", "macos": "14.0"},
            ],
        },
        "dependencies": {"git": "*", "curl": "*", "coreutils": "*"},
        "pypi-dependencies": {"datalad": "*", "git-annex": "*"},
        "tasks": {
            "fetch": {"cmd": "test -f raw/gaia_nearby.csv || python code/fetch_data.py raw/gaia_nearby.csv"},
            "compute": {
                "cmd": "python code/compute_distances.py raw/gaia_nearby.csv output/distances.csv",
                "depends-on": ["fetch"],
                "inputs": ["raw/gaia_nearby.csv", "code/compute_distances.py", "pyproject.toml", "pixi.lock"],
                "outputs": ["output/distances.csv"],
            },
            "all": {"depends-on": ["compute"]},
            "clean": {"cmd": "rm -f output/distances.csv"},
            "reference": {"cmd": "sh test/fetch_reference_distances.sh", "depends-on": ["all"]},
            "test": {"cmd": "python test/verify_distances.py", "depends-on": ["reference"]},
        },
    }
    path.write_text(tomlkit.dumps(project))
    for name in ("Makefile", "requirements.txt"):
        Path(name).unlink(missing_ok=True)
    ignore = Path(".gitignore")
    if ".pixi/" not in ignore.read_text().splitlines():
        with ignore.open("a") as stream:
            stream.write("\n.pixi/\n")
    readme = Path("README.md")
    text = readme.read_text().replace("make test", "pixi run test").replace("make clean", "pixi run clean")
    text = text.replace("make\n", "pixi run all\n")
    text = text.replace("pip install -r requirements.txt", "pixi run test")
    text = text.replace("- Python >= 3.10", "- Pixi")
    readme.write_text(text)
    Path("test/reproduce_from_scratch.sh").write_text('''#!/bin/sh
    set -eu
    source_repo=$(git rev-parse --show-toplevel)
    clone_dir=$(mktemp -d)
    trap 'rm -rf "$clone_dir"' EXIT
    git clone "$source_repo" "$clone_dir/project"
    cd "$clone_dir/project"
    pixi run --locked clean
    pixi run --locked test
    ''')


def prepare(source, output):
    """Clone the pinned baseline, preserving it while deriving a new analysis."""
    import hashlib
    import json
    import os
    import shutil
    import subprocess

    script = Path(__file__).resolve()
    source = source.resolve()
    output = output.resolve()
    if output.exists():
        raise SystemExit(f"{output} already exists; choose a new --output directory")
    if not (source / "pyproject.toml").is_file():
        raise SystemExit("Initialize the Gaia submodule with git submodule update --init")

    def git(*args, cwd):
        return subprocess.check_output(["git", *args], cwd=cwd, text=True).strip()

    if git("status", "--porcelain", cwd=source):
        raise SystemExit("The Gaia baseline has uncommitted changes; use a clean committed baseline")
    bundle_root = Path(git("rev-parse", "--show-toplevel", cwd=script.parent))
    source_paths = [str(script.parent.relative_to(bundle_root)),
                    "content/examples/pixi-stellar-distance-walkthrough.md"]
    provenance = {
        "source_commit": git("rev-parse", "HEAD", cwd=bundle_root),
        "source_paths": source_paths,
        "source_dirty": bool(git("status", "--porcelain", "--", *source_paths, cwd=bundle_root)),
        "gaia_commit": git("rev-parse", "HEAD", cwd=source),
        "migration_sha256": hashlib.sha256(script.read_bytes()).hexdigest(),
    }
    subprocess.run(["git", "clone", "--no-hardlinks", str(source), str(output)], check=True)
    subprocess.run(["git", "switch", "-c", "pixi-analysis"], cwd=output, check=True)
    shutil.copytree(script.parent / "extension", output / "code/extension",
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    shutil.copy2(script.parent / "data/gaia_uncertainties.csv", output / "raw/gaia_uncertainties.csv")
    shutil.copy2(script.parent / "data/README.md", output / "raw/gaia_uncertainties.README.md")
    provenance["extension_sha256"] = {
        str(path.relative_to(script.parent)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted((script.parent / "extension").glob("*.py"))
    }
    provenance["catalog_sha256"] = hashlib.sha256(
        (script.parent / "data/gaia_uncertainties.csv").read_bytes()).hexdigest()
    shutil.copy2(script, output / script.name)
    (output / "pixi-source.json").write_text(json.dumps(provenance, indent=2) + "\n")
    previous = Path.cwd()
    try:
        os.chdir(output)
        migrate()
    finally:
        os.chdir(previous)
    print(f"Migrated {provenance['gaia_commit']} into {output}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path(__file__).resolve().parent / "gaia")
    parser.add_argument("--output", type=Path, default=Path("analysis"))
    args = parser.parse_args()
    prepare(args.source, args.output)
