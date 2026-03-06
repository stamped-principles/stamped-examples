---
title: "Container venv Overlay for Python Development"
date: 2026-03-02
description: "Using containers as reusable environment providers with lightweight venv overlays for fast Python development"
summary: "Demonstrates how to mount local code into stock or third-party containers and create lightweight venv overlays, bridging the container's fixed environment with project-specific dependencies."
tags: ["container", "docker", "singularity", "venv", "uv", "python", "development"]
stamped_principles: ["S", "A", "P", "E"]
fair_principles: ["R", "A"]
instrumentation_levels: ["pattern"]
aspirations: ["reproducibility", "efficiency"]
params:
  tools: ["docker", "uv", "python"]
  difficulty: "intermediate"
  verified: false
---

## The misconception

A common objection to containers goes like this: "I tried Docker, but I
have to rebuild the image every time I change my code.  I can't use my
editor normally.  It's too slow for development."

This treats containers as monolithic, sealed artifacts — you either bake
everything in, or you don't use them at all.  The result is that
developers either avoid containers entirely (losing reproducibility) or
endure painfully slow rebuild-restart cycles (losing productivity).

The reality is simpler: containers are **reusable environment providers**.
You can mount your local source code into a running container via a bind mount,
and the container would supply only what is hard to set up locally — a specific
Python version, system libraries, pre-compiled packages, GPU drivers.
Your code stays on the host, editable with your normal tools, and changes
are visible inside the container instantly.

## The pattern

{{< mermaid >}}
flowchart TB
    subgraph host["HOST FILESYSTEM"]
        code["📁 Source code + pyproject.toml"]
        venv["📁 .venv/<br>(persistent on host)"]
    end

    runtime["Container runtime"]

    subgraph container["CONTAINER"]
        env["Python + system libs +<br>pre-installed packages"]
        work["📁 /work/ = bind-mounted 📁"]:::dashed
    end

    runtime -.->|starts| container
    code ==>|"bind mount<br>(same files, two views)"| work
    env -->|base packages| venv
    work -->|"pip install ."| venv

    classDef dashed stroke-dasharray: 5 5
{{< /mermaid >}}

Both the container runtime and your source code live on the **host**.
The runtime starts the container and sets up bind mounts — it is not
inside the container itself.  The bind mount creates an overlap: your
code appears inside the container at `/work/` folder, while physically remaining
on your filesystem, editable with your normal tools.

The **container** provides the heavy, slow-to-build parts: a pinned Python
version, compiled system libraries, and optionally pre-installed Python
packages.  The **host** provides the fast-changing parts: your source code
(bind-mounted into the container) and a `pyproject.toml` (or lock file)
that declares project-specific dependencies.

The **venv** bridges the two.  It can operate in two modes:

- **Fresh venv** (plain `python -m venv` or `uv venv`, without `--system-site-packages`) — a clean,
  isolated environment where only explicitly installed packages are
  available.  Use this with minimal containers that provide Python but no
  pre-installed packages.
- **Overlay venv** (`python -m venv --system-site-packages`) — inherits
  all packages already installed in the container, and installs only the
  additional dependencies your project needs on top.  Use this to take
  full advantage of a container that already ships heavy dependencies.

## Scenario 1: Stock uv container + pyproject.toml

The simplest case: you have a Python project with a `pyproject.toml` and
want a reproducible environment without installing anything on your host
beyond a container runtime.  A stock [uv](https://docs.astral.sh/uv/)
container provides Python and `uv` — you supply the code and dependencies.

Docker / Podman:

```bash
docker run --rm -v "$(pwd)":/work -w /work \
  ghcr.io/astral-sh/uv:python3.12-trixie-slim \
  sh -c '
    uv venv .venv
    uv pip install .
    .venv/bin/python -m myproject
  '
```

Singularity / Apptainer equivalent:

```bash
singularity exec --cleanenv \
  -B "$(pwd)":/work --pwd /work \
  docker://ghcr.io/astral-sh/uv:python3.12-trixie-slim \
  sh -c '
    uv venv .venv
    uv pip install .
    .venv/bin/python -m myproject
  '
```

Because the code is bind-mounted, edits on the host are immediately
visible inside the container — no rebuild needed.  The `.venv/` directory
is also on the host (created inside the bind mount), so subsequent runs
can reuse it without reinstalling everything.

The `uv pip install .` command reads dependencies directly from
`pyproject.toml`.  For **interactive development** (e.g., with `docker run -it`), use
`uv pip install -e .` (editable install) so that changes to your Python
source files take effect immediately without reinstalling.

Use `pyproject.toml` to specify the upper- or/and the lower-bound of your project's dependencies, and `uv` will resolve the compatibilities during the build. However, if you need to pin exact versions for reproducibility, use a lock file (`uv.lock`, `requirements.txt`) instead — the exact versions of packages will be installed.

### A testable example

The following creates a minimal Python project and runs it in the stock
uv container.
If you don't have docker installed yet, follow ["Get Docker"](https://docs.docker.com/get-started/get-docker/) or your OS instructions to get it running.
```sh
#!/bin/sh
# pragma: testrun stock-uv-container
# pragma: requires docker
# pragma: timeout 180

set -eux
PS4='> '
cd "$(mktemp -d "${TMPDIR:-/tmp}/venv-overlay-XXXXXXX")"

# -- create a minimal Python project --
mkdir -p greet
# -- declare dependencies of the project --
cat > pyproject.toml << 'EOF'
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "greet"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = ["pyyaml"]
EOF
# -- write a module that prints items listed in the config file with a greeting --
cat > greet/__init__.py << 'PYEOF'
import yaml
import sys
from pathlib import Path

def main():
    config = yaml.safe_load(Path("config.yaml").read_text())
    print(config["greeting"])
    for item in config["items"]:
        print(f"  - {item}")
    print(f"Python {sys.version_info.major}.{sys.version_info.minor}")

if __name__ == "__main__":
    main()
PYEOF

# -- edit data on the host, but run in container via bind mount --
cat > config.yaml << 'EOF'
greeting: Hello from the container
items:
  - alpha
  - bravo
  - charlie
EOF

# -- run in the stock uv container --
docker run --rm -v "$(pwd)":/work -w /work \
  ghcr.io/astral-sh/uv:python3.12-trixie-slim \
  sh -c '
    uv venv .venv
    uv pip install .
    .venv/bin/python -c "from greet import main; main()"
  '

# -- edit again, no container rebuild needed -- FAST --
cat > config.yaml << 'EOF'
greeting: Edited again on the host
items:
  - alpha
  - bravo
  - charlie
EOF

docker run --rm -v "$(pwd)":/work -w /work \
  ghcr.io/astral-sh/uv:python3.12-trixie-slim \
  sh -c '.venv/bin/python -c "from greet import main; main()"'
```

The second `docker run` reuses the existing `.venv/` (it persists on the
host via the bind mount) and picks up the edited `config.yaml` without
rebuilding anything.

## Scenario 2: Reusing an "unrelated" container (venv overlay)

Sometimes the container you need already exists but was built for a
different purpose — a JupyterHub image, a bioinformatics pipeline image, a
machine learning training image.  These containers typically bundle heavy
dependencies (NumPy, SciPy, TensorFlow, CUDA libraries) that are
time-consuming to install.

The key insight: **you don't need to build a custom image**.  You override the
entrypoint and create a venv overlay that inherits the container's
packages:

Docker / Podman:

```bash
docker run --rm --entrypoint /bin/sh \
  -v "$(pwd)":/work -w /work \
  jupyter/scipy-notebook:latest \
  -c '
    python -m venv --system-site-packages .venv
    . .venv/bin/activate
    pip install .
    python -m my_analysis
  '
```

Singularity / Apptainer equivalent (no entrypoint override needed —
`singularity exec` ignores container entrypoints):

```bash
singularity exec --cleanenv \
  -B "$(pwd)":/work --pwd /work \
  docker://jupyter/scipy-notebook:latest \
  sh -c '
    python -m venv --system-site-packages .venv
    . .venv/bin/activate
    pip install .
    python -m my_analysis
  '
```

The `--system-site-packages` flag is what makes this work: the overlay
venv can import everything already installed in the container (numpy,
scipy, matplotlib, etc.) while `pip install .` adds only the packages
your project needs on top.  You get the container's pre-built environment
**plus** your project's specific dependencies, without building a custom
image.

As in Scenario 1, the `.venv/` lives in the bind-mounted directory and
persists on the host between runs.  Subsequent invocations skip the
install step entirely — just activate and run.  The venv's Python is a
symlink to the container's interpreter, so it only works inside the same
(or compatible) container image.

## Scenario 3: Ephemeral venv for CI and testing

During development, a persistent `.venv/` on the host is convenient — fast
restarts, no reinstalling.  But for CI pipelines and testing, you want the
opposite: a **guaranteed clean state** every run, with no leftover
packages from previous iterations.

The solution: place the venv inside the container's filesystem (e.g.,
`/tmp/venv`) instead of in the bind-mounted directory.  Since container
filesystems are ephemeral, the venv is destroyed when the container exits.

{{< mermaid >}}
flowchart TB
    subgraph host["HOST FILESYSTEM"]
        code["📁 Source code + pyproject.toml"]
    end

    runtime["Container runtime"]

    subgraph container["CONTAINER"]
        env["Python + system libs +<br>pre-installed packages"]
        work["📁 /work/ = bind-mounted 📁"]:::dashed
        venv-eph["📁 /tmp/venv/<br>(ephemeral, destroyed on exit)"]
    end

    runtime -.->|starts| container
    code ==>|bind mount| work
    env -->|"--system-site-packages"| venv-eph
    work -->|"pip install ."| venv-eph

    classDef dashed stroke-dasharray: 5 5
{{< /mermaid >}}

Compare with the diagram above: the venv now lives inside the container,
not in the project folder.  Nothing persists on the host except your
source code.

```bash
docker run --rm --entrypoint /bin/sh \
  -v "$(pwd)":/work -w /work \
  jupyter/scipy-notebook:latest \
  -c '
    python -m venv --system-site-packages /tmp/venv
    . /tmp/venv/bin/activate
    pip install .
    python -m my_analysis
  '
```

Every run starts from the container's base packages and installs project
dependencies fresh.  This is slower than the persistent approach but
guarantees that the environment matches what a new user (or CI runner)
would see.

## The generalizable recipe

The pattern has two independent dimensions:

1. **Isolated vs Overlay**: whether the venv inherits the container's
   pre-installed packages (`--system-site-packages`) or starts clean.
2. **Persistent vs Ephemeral**: whether the venv lives in the bind-mounted
   directory (persists on host between runs) or inside the container's
   filesystem (recreated every run).

| | **Isolated** (fresh venv) | **Overlay** (`--system-site-packages`) |
|---|---|---|
| **Persistent** (`.venv/` in bind mount) | Scenario 1 | Scenario 2 |
| **Ephemeral** (`/tmp/venv` in container) | *(valid but less common)* | Scenario 3 |

**Persistent + Isolated** (Scenario 1 — stock uv container):

```bash
uv venv .venv
uv pip install .
.venv/bin/python -m myproject
```

**Persistent + Overlay** (Scenario 2 — reuse heavy container):

```bash
python -m venv --system-site-packages .venv
. .venv/bin/activate
pip install .
python -m myproject
```

**Ephemeral + Overlay** (Scenario 3 — CI/testing):

```bash
python -m venv --system-site-packages /tmp/venv
. /tmp/venv/bin/activate
pip install .
python -m myproject
```

For projects that are not a full Python package (e.g., a standalone script
with a few dependencies), you likely would not have `pyproject.toml`.
Then just create a simple `requirements.txt` with list of (versioned) dependencies and 
use `pip install -r requirements.txt` or
`uv pip install -r requirements.txt` instead of `pip install .`.

**Key flags:**

- **`--system-site-packages`** — makes the container's installed packages
  importable in the overlay venv.  `pip` respects them during dependency
  resolution (avoids duplicating what is already installed), but `uv`
  currently ignores system packages during resolution and may reinstall
  packages already present — functionally correct but wastes space.
- **`--entrypoint /bin/sh`** (Docker) — overrides the container's default
  entrypoint so you can run arbitrary commands.  Not needed with
  Singularity/Apptainer, which always uses `exec` semantics.
- **`-v $(pwd):/work -w /work`** (Docker) or **`-B $(pwd):/work --pwd /work`**
  (Singularity) — bind-mounts your local code into the container.
  Alternatively, use **`-v $(pwd):$(pwd) -w $(pwd)`** to keep the same
  path inside and outside the container — useful when tools record
  absolute paths for provenance, or when you want to avoid confusion about
  where files actually live.

## Examples in the wild

This pattern is not theoretical — it is deployed in production across
multiple projects.

**DANDI JupyterHub** — The
[DANDI Archive](https://dandiarchive.org/) JupyterHub uses a
[lightweight venv overlay](https://docs.dandiarchive.org/user-guide-using/dandi-hub/#lightweight-venv-overlay)
on top of its conda base environment.  Users get a fully configured
scientific Python stack from the container and can install additional
packages in their personal overlay without affecting the base image or
other users.  The overlay is cheap to create, fast to customize, and
disposable.

**NeuroDesk** — [NeuroDesk](https://www.neurodesk.org/) provides
neuroimaging software (FreeSurfer, FSL, ANTs, and dozens more) through
transparent Singularity/Apptainer containers.  Rather than building one
container per tool, NeuroDesk packages related tools into shared
containers and makes them accessible via a desktop environment
(NeuroDesktop) or command-line modules (NeuroCommand).  Users bind-mount
their data into whichever container provides the tool they need.  The
same container image serves many researchers across institutions —
reuse ([FAIR R]({{< ref "fair_principles/r" >}})) at scale.

## STAMPED analysis

| Property | How the pattern embodies it |
|---|---|
| [Self-contained]({{< ref "stamped_principles/s" >}}) | `pyproject.toml` declares all dependencies; combined with a pinned container tag (or digest), the full environment is specified |
| [Actionable]({{< ref "stamped_principles/a" >}}) | A single `docker run` or `singularity exec` command reproduces the environment — no manual setup steps |
| [Portable]({{< ref "stamped_principles/p" >}}) | The container pins the Python version and system libraries; `pyproject.toml` (or a lock file) pins package versions; the pattern works on any host with a container runtime |
| [Ephemeral]({{< ref "stamped_principles/e" >}}) | Each container invocation starts from a clean base; the overlay venv can be ephemeral (Scenario 3 — recreated every run for guaranteed reproducibility) or persistent (Scenarios 1–2 — kept across runs for faster iteration) — the choice is yours |
