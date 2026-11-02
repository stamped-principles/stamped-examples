"""Prepare the distributable extension with the original Gaia dataset as input.

Maintainer utility: readers clone the materialized project, with its committed
manifest, lockfile, scripts, input subdataset, and recorded results.
"""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import subprocess


def git(*args, cwd):
    return subprocess.check_output(["git", *args], cwd=cwd, text=True).strip()


def prepare(source, output):
    bundle = Path(__file__).resolve().parent
    source, output = source.resolve(), output.resolve()
    if output.exists():
        raise SystemExit(f"{output} already exists; choose a new --output directory")
    if not (source / ".git").exists():
        raise SystemExit("Initialize the Gaia submodule with git submodule update --init")
    if git("status", "--porcelain", cwd=source):
        raise SystemExit("The Gaia baseline must be a clean committed dataset")
    parent = Path(git("rev-parse", "--show-toplevel", cwd=bundle))
    relative = str(bundle.relative_to(parent) / "gaia")
    url = git("config", "-f", ".gitmodules", "--get", f"submodule.{relative}.url", cwd=parent)
    if not url.startswith(("https://", "git@")):
        raise SystemExit("The Gaia submodule needs a public distribution URL")
    revision = git("rev-parse", "HEAD", cwd=source)
    output.mkdir(parents=True)
    git("init", "-b", "main", cwd=output)
    # Local cloning reuses the available checkout; only the public URL is saved.
    git("-c", "protocol.file.allow=always", "submodule", "add", str(source), "inputs/gaia", cwd=output)
    git("checkout", "--detach", revision, cwd=output / "inputs/gaia")
    git("submodule", "set-url", "inputs/gaia", url, cwd=output)
    for name in ("pyproject.toml", "pixi.lock"):
        shutil.copy2(bundle / name, output / name)
    shutil.copy2(bundle / "project-README.md", output / "README.md")
    shutil.copytree(bundle / "extension", output / "code",
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    (output / ".gitignore").write_text(".pixi/\n__pycache__/\n")
    files = [bundle / "prepare-project.py", bundle / "pyproject.toml", bundle / "pixi.lock",
             bundle / "project-README.md", *sorted((bundle / "extension").glob("*.py"))]
    provenance = {
        "source_commit": git("rev-parse", "HEAD", cwd=parent),
        "source_dirty": bool(git("status", "--porcelain", "--", str(bundle.relative_to(parent)), cwd=parent)),
        "gaia_commit": revision,
        "gaia_url": url,
        "source_sha256": {str(p.relative_to(bundle)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
    }
    (output / "source.json").write_text(json.dumps(provenance, indent=2) + "\n")
    git("add", ".", cwd=output)
    print(f"Prepared {output} with Gaia {revision}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path(__file__).resolve().parent / "gaia")
    parser.add_argument("--output", type=Path, default=Path("analysis"))
    args = parser.parse_args()
    prepare(args.source, args.output)
