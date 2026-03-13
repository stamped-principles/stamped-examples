---
title: "Walkthrough: stellar distances from Gaia parallax"
date: 2026-03-12
description: "Building a STAMPED research object that computes stellar distances from Gaia DR3 parallax data"
summary: "Incrementally builds a research object from a bare script to a tracked, portable, reproducible pipeline — motivated by real problems, not by acronym order."
tags: ["gaia", "parallax", "walkthrough", "python", "datalad", "make"]
stamped_principles: ["S", "T", "A", "M", "P", "E", "D"]
fair_principles: ["R", "A"]
instrumentation_levels: ["workflow"]
aspirations: ["reproducibility", "rigor", "transparency"]
params:
  tools: ["python", "git", "datalad", "make"]
  difficulty: "beginner"
  verified: true
---

## What we're building

Most research code starts the same way: a script that works, on your machine, right now.
That's not a problem — it's a starting point.

Here we take a real analysis — computing distances to nearby stars from European Space Agency data — and gradually turn it into something anyone can verify, reproduce, and build on.
No new frameworks.
No heavyweight infrastructure.
Just a series of small, practical steps, each one solving a concrete problem: "which version of the data did I use?", "why doesn't this run on my colleague's laptop?", "how do I prove these numbers are right?"

Along the way, we note which STAMPED properties each step improves.
By the end, we have a research object that passes a from-scratch reproduction test in a throwaway directory — and most of the steps turn out to be things we might already be doing, just named and organized.

**The science**: we compute the distance to 100 nearby stars using parallax measurements from the [Gaia DR3](https://www.cosmos.esa.int/web/gaia/dr3) catalog.
The math is one line: `distance_pc = 1000 / parallax_mas`.
The result is a CSV of stellar distances in parsecs — verified against Gaia's own pipeline estimates to within 0.3%.

The analysis is deliberately simple so the focus stays on *how* we organize, track, and share the work.

## Steps

### 1. Start a project

We start with a single Python script that does everything: queries the Gaia TAP API, fetches parallax measurements for 100 nearby stars, computes distances, and writes a CSV.

```python
# compute_everything.py (abbreviated)
QUERY = (
    "SELECT TOP 100 source_id, parallax "
    "FROM gaiadr3.gaia_source "
    "WHERE parallax > 10 AND parallax_error/parallax < 0.1 "
    "ORDER BY parallax DESC"
)

with urllib.request.urlopen(f"{GAIA_TAP_URL}?{params}") as resp:
    raw = resp.read().decode()

for star in csv.DictReader(io.StringIO(raw)):
    distance_pc = 1000.0 / float(star["parallax"])
```

Run it, get a `distances.csv` with 100 rows.
Proxima Centauri shows up at ~1.30 parsecs — looks right.

We put it in a directory and run `git init`.
Two things happen at once: we draw a boundary around the project (Self-containment), and we start recording its history (Tracking).
The boundary is the "don't look up" rule (S.1): everything needed for this work lives inside one root, and nothing outside should be implicitly required.
Git gives us content-addressed version control — each commit hash is a cryptographic fingerprint of the entire project state, not an ambiguous label like "version 1.0."

From now on, every change is recorded and reversible.
That makes all subsequent steps low-risk.

```
stellar-distance/
├── compute_everything.py
└── distances.csv
```

This is where most analyses live forever — and that's fine for exploration.
But what happens when we come back in six months and can't remember which query parameters we used?
When a collaborator asks "how do I run this?"
When a reviewer asks us to recompute with updated data?

Each step that follows addresses one of these failure modes.

**Advances**: S (everything reachable from one root), T (content identification, change history)

### 2. Split scripts and fetch data with provenance

The monolithic script does two things — fetch and compute — and there's no way to re-run one without the other.
We split it into two scripts: `fetch_data.py` to retrieve data from Gaia, and `compute_distances.py` to calculate distances from that data.

```python
# fetch_data.py
def fetch(output_path):
    params = urllib.parse.urlencode({
        "REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": "csv",
        "QUERY": QUERY,
    })
    with urllib.request.urlopen(f"{GAIA_TAP_URL}?{params}") as resp:
        data = resp.read().decode()
    with open(output_path, "w") as f:
        f.write(data)
```

```python
# compute_distances.py
def main(input_path, output_path):
    with open(input_path) as f:
        stars = list(csv.DictReader(f))
    # ...
    for star in stars:
        distance_pc = 1000.0 / float(star["parallax"])
    # ... write output CSV ...
```

Now we do something important: instead of just running `fetch_data.py`, we wrap it with `datalad run`:

```sh
datalad run \
  -m "Fetch 100 nearest stars from Gaia DR3" \
  -o "gaia_nearby.csv" \
  "python3 fetch_data.py gaia_nearby.csv"
```

This records exactly what command produced the data, creating a machine-readable provenance record in the commit message.
The data is no longer just "a CSV that appeared somehow" — it has a documented origin that anyone can inspect and replay with `datalad rerun`.

This also addresses a Self-containment concern.
Our analysis depends on an external network resource (the Gaia TAP API), which means it could break if the API changes or goes offline.
Once we've fetched the data with `datalad run`, we have our own versioned copy.
The API is still the authoritative source, but we're no longer silently dependent on it — the provenance record documents where the data came from, and the committed CSV means the analysis can proceed offline.

`datalad run` works on plain git repositories — no special initialization required.

```
stellar-distance/
├── compute_distances.py
├── fetch_data.py
├── gaia_nearby.csv
└── distances.csv
```

**Advances**: T (programmatic provenance), S (versioned local copy of external data), A (provenance is re-executable)

### 3. Organize into directories

We create `code/`, `raw/`, and `output/` directories, and move each file to where it belongs:

```
stellar-distance/
├── code/
│   ├── fetch_data.py
│   └── compute_distances.py
├── raw/
│   └── gaia_nearby.csv
└── output/
    └── distances.csv
```

Code is what we write, raw is what we fetch, output is what we compute.
The role of each file is obvious at a glance.
When something breaks, we know where to look.

This is Modularity at its simplest — not separate repositories, just separate directories with clear roles.

**Advances**: M (logical separation of concerns), S (clearer boundary)

### 4. Record the analysis with provenance

Just as we used `datalad run` for the fetch in step 2, we now use it for the analysis:

```sh
datalad run \
  -m "Compute distances for 100 nearest stars" \
  -i "raw/gaia_nearby.csv" \
  -i "code/compute_distances.py" \
  -o "output/distances.csv" \
  "python3 code/compute_distances.py raw/gaia_nearby.csv output/distances.csv"
```

The `-i` flags declare inputs and `-o` declares outputs.
Now the full pipeline — from raw data to final results — has machine-readable provenance.
Anyone can inspect the commit messages to see exactly how each file was produced.

**Advances**: T (full pipeline provenance), A (analysis is re-executable via `datalad rerun`)

### 5. Write a README

We add a README explaining what this project does, what the inputs and outputs are, and how to run it:

```markdown
# Stellar Distance from Gaia Parallax

Compute distances to nearby stars using parallax measurements from the
Gaia DR3 catalog.

**Input**: Gaia source IDs and parallax (milliarcseconds), fetched via TAP query.
**Output**: Source IDs and computed distances (parsecs).
**Method**: `distance_pc = 1000 / parallax_mas`

## Reproduce

    python3 code/fetch_data.py raw/gaia_nearby.csv
    python3 code/compute_distances.py raw/gaia_nearby.csv output/distances.csv
```

Without a README, the project is only usable by the person who wrote it — and only while they remember how.
A README makes it usable by anyone who can read.
This is the minimum viable Actionability (A.1): sufficient instructions to reproduce all results.

**Advances**: A (someone can now follow instructions to reproduce), S (project is self-describing)

### 6. Write a Makefile

We encode the pipeline as `make` targets with their dependencies:

```makefile
all: output/distances.csv

raw/gaia_nearby.csv:
	python3 code/fetch_data.py raw/gaia_nearby.csv

output/distances.csv: raw/gaia_nearby.csv code/compute_distances.py
	python3 code/compute_distances.py raw/gaia_nearby.csv output/distances.csv
```

The README *says* how to run the pipeline.
The Makefile *does* it.
This is the jump from documented to executable — the Actionability spectrum in action (A.2).
Make also encodes dependencies: it knows what to re-run when an input changes, which is itself a lightweight form of provenance.

Now `make` is the single command to reproduce everything. We update the README accordingly.

**Advances**: A (executable specification — not just documentation but a runnable recipe)

### 7. Add a test

We write a verification script that fetches independent reference distances from Gaia's GSP-Phot pipeline and compares them to our computed values.
`make test` runs it.

```
$ make test
Fetched 48 reference distances
Compared 48 stars
Max error: 0.27%
PASSED: all within 0.5%
```

Without verification, a research object asks others to trust the results.
A test makes the claim falsifiable — anyone can run `make test` and see for themselves.

Only 48 of our 100 stars have GSP-Phot distances because Gaia's sophisticated pipeline doesn't produce estimates for every star.
Our simple one-line formula actually covers more stars than the pipeline does.

```
stellar-distance/
├── code/
│   ├── fetch_data.py
│   └── compute_distances.py
├── raw/
│   └── gaia_nearby.csv
├── output/
│   └── distances.csv
├── test/
│   ├── fetch_reference_distances.sh
│   └── verify_distances.py
├── Makefile
└── README.md
```

**Advances**: A (verifiable results, not just "trust me")

### 8. Declare and pin dependencies

Until now the scripts used only Python's standard library (urllib, csv).
We rewrite the fetch script to use `requests` — cleaner API, better error handling — which introduces an external dependency.

```python
# fetch_data.py (rewritten)
import requests

def fetch(output_path, limit=100, min_parallax=10, max_error_ratio=0.1):
    resp = requests.get(GAIA_TAP_URL, params={
        "REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": "csv",
        "QUERY": query,
    })
    resp.raise_for_status()
    with open(output_path, "w") as f:
        f.write(resp.text)
```

Without declaring the dependency, a fresh machine fails with `ModuleNotFoundError` — a Portability failure that only surfaces when someone else tries to run the code.

We add `pyproject.toml` to make the assumption explicit, then generate a hash-locked `requirements.txt`:

```toml
# pyproject.toml
[project]
name = "stellar-distance"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = ["requests"]
```

```sh
pip-compile --generate-hashes -o requirements.txt pyproject.toml
```

There's a big difference between `requests` (any version) and `requests==2.32.5 --hash=sha256:...` (this exact build).
The first is a declaration — it says what we need.
The second is a distribution-ready specification — it says exactly what bytes to install.
Hash pinning means even if a package is re-uploaded with the same version number, the install rejects it rather than silently using different code.
This is where Portability meets Tracking: the environment specification itself is content-addressed.

**Advances**: P (host assumptions documented, reproducible environment), T (pinned versions are content-addressed)

### 9. Reproduce from scratch

We write a script that clones the repository into a fresh temp directory, creates a virtual environment, installs dependencies, runs the pipeline, and runs the tests:

```sh
#!/bin/sh
set -eux
repo_url="${1:?Usage: $0 <repo-url-or-path>}"

cd "$(mktemp -d "${TMPDIR:-/tmp}/stellar-XXXXXXX")"
git clone "$repo_url" stellar-distance
cd stellar-distance

python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt

make
make test

echo "=== PASSED: reproduced from scratch ==="
```

If it passes, the research object doesn't depend on anything from our machine — no accumulated state, no forgotten steps.
The temp directory is thrown away afterward.

This is the integration test for a research object.
Ephemeral reproduction exercises almost every STAMPED property at once: the project must be self-contained (S), the pipeline must actually run (A), it must work in a fresh environment (P), and there's no prior state to lean on (E).
If `reproduce_from_scratch.sh` passes, we have strong evidence that the research object is solid.
If it fails, the error tells us which property broke.

This is the [ephemeral shell reproducer]({{< ref "examples/ephemeral-shell-reproducer" >}}) pattern applied to our own project.

**Advances**: E (results produced without prior state), A (reproduction is a single command), S (validates that nothing outside the boundary is needed)

### 10. Push to GitHub

We push to a [public repository](https://github.com/asmacdo/STAMPED-stellar-distances).
Now anyone can `git clone`, `pip install -r requirements.txt`, `make`, and reproduce the result.

Until this step the research object was self-contained and reproducible — but only on our machine.
Publishing crosses the Distributability threshold (D.1): all components become persistently retrievable by others.

GitHub is hosting, not archival.
For long-term persistence the next step would be depositing on Zenodo or Software Heritage (see "Where to go from here").

```
stellar-distance/
├── code/
│   ├── fetch_data.py
│   └── compute_distances.py
├── raw/
│   └── gaia_nearby.csv
├── output/
│   └── distances.csv
├── test/
│   ├── fetch_reference_distances.sh
│   ├── verify_distances.py
│   └── reproduce_from_scratch.sh
├── Makefile
├── README.md
├── pyproject.toml
└── requirements.txt
```

**Advances**: D (persistently retrievable by others)

## STAMPED scorecard

| Property | Where we ended up |
|---|---|
| **S** Self-contained | All code, data, and instructions under one root. README describes the project. Versioned local copy of fetched data. |
| **T** Tracked | Git tracks all changes. `datalad run` records provenance for both fetch and analysis. Dependencies hash-pinned. |
| **A** Actionable | `make` reproduces results. `make test` verifies. `datalad rerun` replays provenance. README documents the workflow. |
| **M** Modular | code/, raw/, output/, test/ are logically separated. |
| **P** Portable | Dependencies declared in pyproject.toml, pinned in requirements.txt with hashes. No hardcoded paths. |
| **E** Ephemeral | Reproduction script runs the full pipeline in a fresh temp directory with no prior state. |
| **D** Distributable | Repository on GitHub. Anyone can clone and reproduce. |

## Where to go from here

Each STAMPED property is a spectrum.
We've built something solid, but there are natural next steps depending on what the project needs.

### Replay and adapt with datalad rerun

Because we recorded provenance with `datalad run`, we can replay the entire pipeline:

```sh
datalad rerun
```

This re-executes every recorded command in order.
But `datalad rerun` really shines when something changes.

Say we want to expand our sample from 100 to 200 stars.
We update the query parameters in `fetch_data.py`, then re-run just the fetch:

```sh
datalad run \
  -m "Fetch 200 nearest stars from Gaia DR3" \
  -o "raw/gaia_nearby.csv" \
  "python3 code/fetch_data.py raw/gaia_nearby.csv"
```

The new data is committed with a fresh provenance record.
Then `datalad rerun` of the analysis step picks up the new input and recomputes distances — the full pipeline adapts to changed inputs without manual re-orchestration.

This is where modularity and provenance reinforce each other: because the fetch and analysis steps are recorded separately, we can update one without losing the provenance of the other.

### Modularity via subdatasets

Right now our modularity is directory-level: `code/`, `raw/`, `output/`.
That's a good start, but the raw data and the analysis code have different lifecycles — the data might be shared across projects while the analysis code is specific to this one.

DataLad subdatasets take modularity further.
The raw data could live in its own independently versioned dataset:

```sh
datalad clone <data-url> raw/
```

A colleague running a different analysis on the same stars would `datalad install` the data module rather than re-fetching from the API.
The parent dataset records which exact version of each subdataset it depends on, so the full research object remains Self-contained and Tracked even as modules evolve independently.

### Containers for portability and ephemerality

A Dockerfile (pinned by image digest) freezes the OS and Python version.
Running the pipeline inside a disposable container validates that the specifications are complete — if it works in a fresh container, it's not relying on anything from our machine.
See [Container venv overlay for Python development]({{< ref "examples/container-venv-overlay-development" >}}) for a detailed treatment of this pattern.

### CI for ephemeral validation

A GitHub Actions workflow that clones, installs, and runs `make test` on every push.
This catches environment drift automatically — the ephemeral reproduction test from step 9, run by someone else's machine on every change.

### Archival distribution

Deposit the repository on [Zenodo](https://zenodo.org/) for a DOI.
Push the container image to a registry.
Mirror data to multiple remotes so no single point of failure breaks reproducibility.
