---
title: "Walkthrough: stellar distances from Gaia parallax"
date: 2026-03-12
description: "A step-by-step walkthrough building a STAMPED research object that computes stellar distances from Gaia DR3 parallax data"
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

<!-- TODO: wordsmith — enthusiastic intro framing the walkthrough as building a research object, not just running an analysis. Tone: practical, motivating, "you'll be surprised how far simple steps get you." -->

We compute the distance to 100 nearby stars using parallax measurements from the European Space Agency's [Gaia DR3](https://www.cosmos.esa.int/web/gaia/dr3) catalog.
The math is one line: `distance_pc = 1000 / parallax_mas`.
The result is a CSV of stellar distances in parsecs — verified against Gaia's own pipeline estimates to within 0.3%.

The analysis is deliberately simple so the focus stays on *how* we organize, track, and share the work.
Each step is a concrete action.
We note which STAMPED properties each step improves.

**Repository**: [TODO: link to GitHub repo]

## Steps

### 1. Proof of concept

Write a Python script that queries the Gaia TAP API, fetches parallax for 100 nearby stars, computes `distance_pc = 1000 / parallax`, and writes a CSV.
Run it. Get a result. Done.

This is where most analyses live forever.
Not STAMPED at all — but it works, and that matters.

<!-- TODO: expand — frame the tension: the script works but is fragile. What happens when you come back in six months? When a collaborator tries to run it? When a reviewer asks how you got the numbers? Each subsequent step addresses one of these failure modes. -->

*We committed this so you can see it, but in real life this might just be a loose file on your desktop.*

**Commit**: [`0d95ecc`](0d95ecc)

### 2. Gather everything under one roof

Put all files in a single project directory.

<!-- TODO: explain the "don't look up" rule from Self-containment (S.1). Right now the script and output are loose — a collaborator would need to know which files go together. Gathering them establishes a boundary. -->

**Advances**: S (everything reachable from one root)

### 3. Organize into directories

Separate `code/`, `raw/`, `output/`.
Code is what you write, raw is what you fetch, output is what you compute.

<!-- TODO: explain why separation matters — it tells you the role of each file at a glance. When something breaks, you know where to look. This is Modularity at its simplest: not separate repos, just separate directories with clear roles. Also: splitting the monolithic script into fetch + compute makes each piece independently testable and replaceable. -->

**Advances**: M (logical separation of concerns), S (clearer boundary)

**Commit**: [`5d7c7fc`](5d7c7fc) (steps 2 and 3 combined)

### 4. Write a README

Explain what this project does, what the inputs and outputs are, and how to run it.

<!-- TODO: frame as the minimum viable Actionability. Without a README, the project is only actionable by the person who wrote it (and only while they remember how). A README makes it actionable by anyone who can read. This is A.1: "sufficient instructions to reproduce." -->

**Advances**: A (someone can now follow instructions to reproduce), S (project is self-describing)

**Commit**: [`7c92a7f`](7c92a7f)

### 5. Initialize version control

`git init`. Add everything. First commit.

From now on, every change is recorded: who, when, what, and (in the commit message) why.
You can always get back to any previous state.

<!-- TODO: explain content-addressed identification (T.1) — each commit hash is a fingerprint of the entire project state. This is stronger than "version 1.0" labels because two people with the same hash provably have the same content. Also: version control is the safety net that makes all subsequent steps low-risk — you can always revert. -->

**Advances**: T (content identification, change history)

*In the companion repository, we initialized git from the start so each step has its own commit. In your own work, this is the point where you'd run `git init`.*

### 6. Write a Makefile

Encode the pipeline as `make` targets: `raw/gaia_nearby.csv` depends on `code/fetch_data.py`, `output/distances.csv` depends on `raw/gaia_nearby.csv` and `code/compute_distances.py`.
`make` runs the whole thing.

<!-- TODO: frame the jump from "documented" to "executable." The README says how to run the pipeline; the Makefile actually runs it. This is the Actionability spectrum in action (A.2): moving from prose instructions to an executable specification. Also note that Make encodes dependencies — it knows what to re-run when inputs change, which is a form of provenance. -->

**Advances**: A (executable specification — not just documentation but a runnable recipe)

**Commit**: [`84ba4a5`](84ba4a5)

### 7. Add a test

Write a verification script that fetches independent reference distances from Gaia's GSP-Phot pipeline and compares them to our computed values.
`make test` runs it.
48 of 100 stars have reference values; all match within 0.3%.

<!-- TODO: explain why testing is Actionability, not just good practice. A research object without verification asks others to trust the results. A test makes the claim falsifiable — anyone can run `make test` and see for themselves. Also note: not all 100 stars have GSP-Phot distances (only 48 do), which actually demonstrates that our simple formula covers more stars than the sophisticated pipeline. -->

**Advances**: A (verifiable results, not just "trust me")

**Commit**: [`2a6cd40`](2a6cd40)

### 8. Declare dependencies

Add `pyproject.toml` listing the Python packages we use (`requests`).

<!-- TODO: frame the problem this solves. Until now, the scripts used only stdlib (urllib). When we rewrote fetch_data.py to use `requests` (cleaner API, better error handling), we introduced an external dependency. Without declaring it, a fresh machine would fail with `ModuleNotFoundError: No module named 'requests'` — a Portability failure. pyproject.toml makes the assumption explicit (P.1, P.2). -->

**Advances**: P (host assumptions are now documented, not implicit)

**Commit**: [`ed1900b`](ed1900b)

### 9. Pin dependency versions

Generate `requirements.txt` with exact versions.
Better: use `pip-compile --generate-hashes` for hash-pinned versions — guarantees byte-identical packages.

<!-- TODO: explain the difference between "requests" (any version) and "requests==2.32.5 --hash=sha256:..." (this exact build). The former is a declaration; the latter is a distribution-ready specification. Hash pinning means even if a package is re-uploaded with the same version number, the install will fail rather than silently use different code. This is where Portability meets Tracking — the environment specification is content-addressed. -->

**Advances**: P (reproducible environment), T (pinned versions are content-addressed)

**Commit**: [`4e63464`](4e63464)

### 10. Record provenance with datalad run

Wrap the fetch and analysis commands with `datalad run`, which records the exact command, inputs, and outputs as machine-readable metadata in each commit.
The provenance is not just inspectable — it's re-executable via `datalad rerun`.

Note: `datalad run` works on plain git repositories — no DataLad dataset or git-annex required.

<!-- TODO: explain what datalad run adds beyond "git commit." A regular commit says "these files changed." A datalad run commit says "these files changed because this command was run with these inputs and produced these outputs." The run record is JSON embedded in the commit message — machine-readable, not just human-readable. This is T.4: programmatic provenance that includes component versions. And because the record is executable, it's also A.2: an executable specification. -->

**Advances**: T (programmatic provenance), A (provenance records are executable specifications)

**Commits**: [`28795f6`](28795f6) (fetch), [`277e8b7`](277e8b7) (compute)

### 11. Push to GitHub

`git push` to a public repository.
Now anyone can `git clone`, `pip install -r requirements.txt`, `make`, and reproduce the result.

<!-- TODO: frame as the Distributability threshold — D.1 says all components must be "persistently retrievable by others." Until this step, the research object was self-contained and reproducible but only on your machine. Publishing makes it distributable. Note: GitHub is not archival — for long-term persistence, Zenodo or Software Heritage would be the next step (see "Where to go from here"). -->

**Advances**: D (persistently retrievable by others)

**Commit**: [TODO: after GitHub push]

### 12. Reproduce from scratch

Write a script that clones the repository into a fresh temp directory, installs dependencies, runs the pipeline, and runs the tests.
If it passes, the research object doesn't depend on anything from your machine — no accumulated state, no forgotten steps.
The temp directory is thrown away afterward.

This is the [ephemeral shell reproducer]({{< ref "examples/ephemeral-shell-reproducer" >}}) pattern applied to our own project.

<!-- TODO: explain why this is the ultimate integration test for STAMPED. Ephemeral reproduction exercises almost every property at once: S (everything needed must be inside the boundary), A (the pipeline must actually run), P (it must work in a fresh environment), E (no prior state). If reproduce_from_scratch.sh passes, you have strong evidence that your research object is STAMPED. If it fails, the error message tells you exactly which property broke. -->

**Advances**: E (results produced without prior state), A (reproduction is a single command), S (validates that nothing outside the boundary is needed)

**Commit**: [`362ad10`](362ad10)

## STAMPED scorecard

| Property | Where we ended up |
|---|---|
| **S** Self-contained | All code, data, and instructions under one root. README describes the project. |
| **T** Tracked | Git tracks all changes. `datalad run` records provenance per computation. Dependencies hash-pinned. |
| **A** Actionable | `make` reproduces results. `make test` verifies. `datalad rerun` replays provenance. README documents the workflow. |
| **M** Modular | code/, raw/, output/, test/ are logically separated. |
| **P** Portable | Dependencies declared in pyproject.toml, pinned in requirements.txt with hashes. No hardcoded paths. |
| **E** Ephemeral | Reproduction script runs the full pipeline in a fresh temp directory with no prior state. |
| **D** Distributable | Repository on GitHub. Anyone can clone and reproduce. |

## Where to go from here

Each STAMPED property is a spectrum.
We've built something solid, but there are natural next steps depending on what your project needs.

**Containers for portability and ephemerality**:
A Dockerfile (pinned by image digest) freezes the OS and Python version.
Running the pipeline inside a disposable container validates that the specifications are complete — if it works in a fresh container, it's not relying on anything from your machine.
See [Container venv overlay for Python development]({{< ref "examples/container-venv-overlay-development" >}}) for a detailed treatment of this pattern.

**CI for ephemeral validation**:
A GitHub Actions workflow that clones, installs, and runs `make test` on every push.
This catches environment drift automatically.

**Modularity via subdatasets**:
The raw data could live in its own DataLad subdataset, independently versioned and reusable.
A colleague running a different analysis on the same stars would `datalad install` the data module rather than re-fetching from the API.

**Reproducible re-execution**:
`datalad rerun` replays the recorded provenance.
If the raw data is updated (say, a new Gaia release), update the input, `datalad rerun`, and the outputs reflect the new data.
Branches can separate outputs produced from different input versions.

**Archival distribution**:
Deposit the repository on [Zenodo](https://zenodo.org/) for a DOI.
Push the container image to a registry.
Mirror data to multiple remotes so no single point of failure breaks reproducibility.
