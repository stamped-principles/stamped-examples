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
  materialize_stem: "stellar-distance-walkthrough"
---

```sh
#!/bin/sh
# pragma: testrun full-build
# pragma: render hidden
# pragma: requires sh git python3 curl make
# pragma: timeout 600
# pragma: materialize stellar-distance

set -eux
PS4='> '

# Random temp dir for containment and security (no deterministic paths under /tmp)
cd "$(mktemp -d "${TMPDIR:-/tmp}/stellar-XXXXXXX")"

# Build venv — tools needed by later steps
python3 -m venv .venv
. .venv/bin/activate
pip install pip-tools datalad requests
```

## What we're building

Most research code starts the same way: a script that works, on your machine, right now.
That's a starting point.

Here we take a real analysis (computing distances to nearby stars from European Space Agency data) and gradually turn it into something anyone can verify, reproduce, and build on.
No new frameworks.
No heavyweight infrastructure.
Just a series of small, practical steps, each one solving a concrete problem: "which version of the data did I use?", "why doesn't this run on my colleague's laptop?", "how do I prove these numbers are right?"

Along the way, we note which [STAMPED]({{< ref "stamped_principles" >}}) properties (Self-contained, Tracked, Actionable, Modular, Portable, Ephemeral, Distributable) each step improves.
By the end, we have a research object that passes a from-scratch reproduction test in a throwaway directory.
Most of the steps turn out to be things we might already be doing, just named and organized.

**The science**: we compute the distance to 100 nearby stars using parallax measurements from the [Gaia DR3](https://www.cosmos.esa.int/web/gaia/dr3) catalog.
The math is one line: `distance_pc = 1000 / parallax_mas`.
The result is a CSV of stellar distances in parsecs, verified against Gaia's own pipeline estimates to within 0.3%.

The analysis is deliberately simple so the focus stays on *how* we organize, track, and share the work.

## Steps

### 1. Start a project

```sh
# pragma: testrun full-build
# pragma: render hidden
git init stellar-distance
cd stellar-distance
git config user.email "demo@example.com"
git config user.name "Demo User"

# snippet: compute-everything
cat > compute_everything.py <<'PYEOF'
#!/usr/bin/env python3
"""Quick proof of concept: fetch Gaia parallax data and compute distances."""

import csv
import io
import urllib.request
import urllib.parse

GAIA_TAP_URL = "https://gea.esac.esa.int/tap-server/tap/sync"
QUERY = (
    "SELECT TOP 100 source_id, parallax "
    "FROM gaiadr3.gaia_source "
    "WHERE parallax > 10 AND parallax_error/parallax < 0.1 "
    "ORDER BY parallax DESC"
)

params = urllib.parse.urlencode({
    "REQUEST": "doQuery",
    "LANG": "ADQL",
    "FORMAT": "csv",
    "QUERY": QUERY,
})

with urllib.request.urlopen(f"{GAIA_TAP_URL}?{params}") as resp:
    raw = resp.read().decode()

reader = csv.DictReader(io.StringIO(raw))
with open("distances.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["source_id", "distance_pc"])
    writer.writeheader()
    for star in reader:
        distance_pc = 1000.0 / float(star["parallax"])
        writer.writerow({"source_id": star["source_id"], "distance_pc": f"{distance_pc:.4f}"})

print("Done — wrote distances.csv")
PYEOF
# /snippet

python3 compute_everything.py
git add compute_everything.py distances.csv
git commit -m "Initial analysis: compute stellar distances"
```

We start with a single Python script that does everything: queries the Gaia TAP API, fetches parallax measurements for 100 nearby stars, computes distances, and writes a CSV.

{{< snippet id="compute-everything" lang="python" lines="1-2,9-15,31-32" >}}

The above is abbreviated. To follow along, see the {{< step-link step="1" text="full project at this step" >}}.

When we run `python3 compute_everything.py`, we get a `distances.csv` with 100 rows.
Proxima Centauri shows up at ~1.30 parsecs. Looks right!

We put the script and its output in a directory and run `git init`.
Two things happen at once: we draw a boundary around the project (Self-containment), and we start recording its history (Tracking).
The project boundary follows the "don't look up" rule: everything needed for this work lives inside one root, and nothing outside should be implicitly required.
Git gives us content-addressed version control, so we can track changes over time and identify each project state by its commit.

From now on, every change is recorded and reversible.
That makes all subsequent steps low-risk.

```
stellar-distance/
├── compute_everything.py
└── distances.csv
```

This is where most analyses live forever, and that's fine for exploration.
But what happens when we come back in six months and can't remember which query parameters we used?
When a collaborator asks "how do I run this?"
When a reviewer asks us to recompute with updated data?

Each step that follows addresses one of these failure modes.

**Advances**: S (everything reachable from one root), T (content identification, change history)

### 2. Split scripts and fetch data with provenance

```sh
# pragma: testrun full-build
# pragma: render hidden
# snippet: fetch-data
cat > fetch_data.py <<'PYEOF'
#!/usr/bin/env python3
"""Fetch nearby star parallax data from Gaia DR3 via TAP query."""

import sys
import urllib.parse
import urllib.request

GAIA_TAP_URL = "https://gea.esac.esa.int/tap-server/tap/sync"

QUERY = """\
SELECT TOP {limit}
    source_id, parallax
FROM gaiadr3.gaia_source
WHERE parallax > {min_parallax}
    AND parallax_error / parallax < {max_error_ratio}
ORDER BY parallax DESC
"""


def fetch(output_path, limit=100, min_parallax=10, max_error_ratio=0.1):
    query = QUERY.format(
        limit=limit,
        min_parallax=min_parallax,
        max_error_ratio=max_error_ratio,
    )
    params = urllib.parse.urlencode({
        "REQUEST": "doQuery",
        "LANG": "ADQL",
        "FORMAT": "csv",
        "QUERY": query,
    })
    with urllib.request.urlopen(f"{GAIA_TAP_URL}?{params}") as resp:
        data = resp.read().decode()

    with open(output_path, "w") as f:
        f.write(data)

    n_stars = data.count("\n") - 1
    print(f"Fetched {n_stars} stars -> {output_path}")


if __name__ == "__main__":
    output = sys.argv[1] if len(sys.argv) > 1 else "gaia_nearby.csv"
    fetch(output)
PYEOF
# /snippet

# snippet: compute-distances
cat > compute_distances.py <<'PYEOF'
#!/usr/bin/env python3
"""Compute stellar distances from Gaia parallax measurements."""

import csv
import sys


def main(input_path, output_path):
    with open(input_path) as f:
        reader = csv.DictReader(f)
        stars = list(reader)

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["source_id", "distance_pc"])
        writer.writeheader()
        for star in stars:
            distance_pc = 1000.0 / float(star["parallax"])
            writer.writerow({
                "source_id": star["source_id"],
                "distance_pc": f"{distance_pc:.4f}",
            })

    print(f"Computed distances for {len(stars)} stars -> {output_path}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
PYEOF
# /snippet

git rm compute_everything.py
git rm distances.csv
git add fetch_data.py compute_distances.py
git commit -m "Split into fetch and compute scripts"
```

The monolithic script does two things (fetch and compute) and there's no way to re-run one without the other.
We split it into two scripts: `fetch_data.py` to retrieve data from Gaia, and `compute_distances.py` to calculate distances from that data.

{{< snippet id="fetch-data" lang="python" lines="1-2,20,35-36" >}}

{{< snippet id="compute-distances" lang="python" lines="1-2,8,16-17" >}}

{{< step-link step="2" >}}

Now we do something important: instead of just running `fetch_data.py`, we wrap it with `datalad run`:

```sh
# pragma: testrun full-build
datalad run \
  --message "Fetch 100 nearest stars from Gaia DR3" \
  --output gaia_nearby.csv \
  python3 fetch_data.py gaia_nearby.csv
```

```sh
# pragma: testrun full-build
# pragma: render hidden
```

This records exactly what command produced the data, creating a machine-readable provenance record in the commit message.
The data is no longer just "a CSV that appeared somehow." It has a documented origin that anyone can inspect and replay with `datalad rerun`.

This also addresses a Self-containment concern.
Our analysis depends on an external network resource (the Gaia TAP API), which means it could break if the API changes or goes offline.
Once we've fetched the data with `datalad run`, we have our own versioned copy.
The API is still the authoritative source, but we're no longer silently dependent on it. The provenance record documents where the data came from, and the committed CSV means the analysis can proceed offline.

`datalad run` works on plain git repositories. No special initialization required.
It creates a normal git commit whose message includes a machine-readable run record (the command, inputs, and outputs), so `git log` still tells the whole story.

```
stellar-distance/
├── compute_distances.py
├── fetch_data.py
└── gaia_nearby.csv
```

**Advances**: T (programmatic provenance), S (versioned local copy of external data), A (provenance is re-executable)

### 3. Organize into directories

```sh
# pragma: testrun full-build
# pragma: render hidden
python3 compute_distances.py gaia_nearby.csv distances.csv
git add distances.csv
git commit -m "Compute distances from fetched data"

mkdir -p code raw output
git mv fetch_data.py code/
git mv compute_distances.py code/
git mv gaia_nearby.csv raw/
git mv distances.csv output/
git commit -m "Organize into code/, raw/, output/"
```

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

{{< step-link step="3" >}}

This is Modularity at its simplest: not separate repositories, just separate directories with clear roles.

**Advances**: M (logical separation of concerns), S (clearer boundary)

### 4. Record the analysis with provenance

```sh
# pragma: testrun full-build
# pragma: render hidden
git rm output/distances.csv
git commit -m "Remove output to re-compute with provenance"
mkdir -p output
```

Just as we used `datalad run` for the fetch in step 2, we now use it for the analysis:

```sh
# pragma: testrun full-build
datalad run \
  --message "Compute distances for 100 nearest stars" \
  --input raw/gaia_nearby.csv \
  --input code/compute_distances.py \
  --output output/distances.csv \
  python3 code/compute_distances.py raw/gaia_nearby.csv output/distances.csv
```

```sh
# pragma: testrun full-build
# pragma: render hidden
```

The `--input` flags declare inputs and `--output` declares outputs.
Now the full pipeline, from raw data to final results, has machine-readable provenance.
Anyone can inspect the commit messages to see exactly how each file was produced.

{{< step-link step="4" >}}

**Advances**: T (full pipeline provenance), A (analysis is re-executable via `datalad rerun`)

### 5. Write a README

```sh
# pragma: testrun full-build
# pragma: render hidden
# snippet: readme
cat > README.md <<'README'
# Stellar Distance from Gaia Parallax

Compute distances to nearby stars using parallax measurements from the
[Gaia DR3](https://www.cosmos.esa.int/web/gaia/dr3) catalog.

**Input**: Gaia source IDs and parallax (milliarcseconds), fetched via TAP query.
**Output**: Source IDs and computed distances (parsecs).
**Method**: `distance_pc = 1000 / parallax_mas`

## Reproduce

    python3 code/fetch_data.py raw/gaia_nearby.csv
    python3 code/compute_distances.py raw/gaia_nearby.csv output/distances.csv
README
# /snippet

git add README.md
git commit -m "Add README with reproduction instructions"
```

We add a README explaining what this project does, what the inputs and outputs are, and how to run it:

{{< snippet id="readme" lang="markdown" >}}

{{< step-link step="5" >}}

Without a README, the project is only usable by the person who wrote it, and only while they remember how.
A README makes it usable by anyone who can read.
This is the minimum viable Actionability (A.1): sufficient instructions to reproduce all results.

**Advances**: A (someone can now follow instructions to reproduce), S (project is self-describing)

### 6. Write a Makefile

```sh
# pragma: testrun full-build
# pragma: render hidden
# snippet: makefile
cat > Makefile <<'MAKE'
.POSIX:

all: output/distances.csv

raw/gaia_nearby.csv:
	python3 code/fetch_data.py raw/gaia_nearby.csv

output/distances.csv: raw/gaia_nearby.csv code/compute_distances.py
	python3 code/compute_distances.py raw/gaia_nearby.csv output/distances.csv

clean:
	rm -f output/distances.csv

.PHONY: all clean
MAKE
# /snippet

# Update README: replace manual commands with 'make'
sed -i '/^    python3 code\/fetch_data\.py/,/^    python3 code\/compute_distances\.py/c\    make' README.md

git add Makefile README.md
git commit -m "Add Makefile encoding the full pipeline"
```

We encode the pipeline as `make` targets with their dependencies:

{{< snippet id="makefile" lang="makefile" >}}

{{< step-link step="6" >}}

The README *says* how to run the pipeline.
The Makefile *does* it.
This is the jump from documented to executable: the Actionability spectrum in action (A.2).
Make also encodes dependencies: it knows what to re-run when an input changes, which is itself a lightweight form of provenance.

Now `make` is the single command to reproduce everything. We update the README accordingly.

**Advances**: A (executable specification, a runnable recipe)

### 7. Add a test

```sh
# pragma: testrun full-build
# pragma: render hidden
mkdir -p test

# snippet: fetch-reference
cat > test/fetch_reference_distances.sh <<'TESTSH'
#!/bin/sh
# Fetch GSP-Phot reference distances for the exact stars we computed
set -eu

ids=$(tail -n +2 output/distances.csv | cut -d, -f1 | paste -sd,)

curl -s -o test/reference_distances.csv \
  --data-urlencode "REQUEST=doQuery" \
  --data-urlencode "LANG=ADQL" \
  --data-urlencode "FORMAT=csv" \
  --data-urlencode "QUERY=SELECT source_id, distance_gspphot FROM gaiadr3.gaia_source WHERE source_id IN ($ids) AND distance_gspphot IS NOT NULL" \
  "https://gea.esac.esa.int/tap-server/tap/sync"

echo "Fetched $(tail -n +2 test/reference_distances.csv | wc -l) reference distances"
TESTSH
# /snippet
chmod +x test/fetch_reference_distances.sh

# snippet: verify-distances
cat > test/verify_distances.py <<'PYEOF'
#!/usr/bin/env python3
"""Compare our computed distances against Gaia GSP-Phot reference distances."""

import csv
import sys


def main():
    computed = {}
    with open("output/distances.csv") as f:
        for row in csv.DictReader(f):
            computed[row["source_id"]] = float(row["distance_pc"])

    reference = {}
    with open("test/reference_distances.csv") as f:
        for row in csv.DictReader(f):
            reference[row["source_id"]] = float(row["distance_gspphot"])

    matched = set(computed) & set(reference)
    if not matched:
        print("ERROR: no matching source_ids between computed and reference")
        sys.exit(1)

    max_pct_err = 0
    failures = []
    for sid in sorted(matched):
        c = computed[sid]
        r = reference[sid]
        pct_err = abs(c - r) / r * 100
        max_pct_err = max(max_pct_err, pct_err)
        if pct_err > 0.5:
            failures.append((sid, c, r, pct_err))

    print(f"Compared {len(matched)} stars")
    print(f"Max error: {max_pct_err:.2f}%")

    if failures:
        print(f"\nFAILED: {len(failures)} stars differ by >0.5%:")
        for sid, c, r, pct in failures:
            print(f"  {sid}: computed={c:.4f} ref={r:.4f} err={pct:.1f}%")
        sys.exit(1)
    else:
        print("PASSED: all within 0.5%")


if __name__ == "__main__":
    main()
PYEOF
# /snippet

# Add test target to Makefile
sed -i 's/^\.PHONY: all clean/.PHONY: all test clean/' Makefile
printf '\ntest: output/distances.csv\n\t./test/fetch_reference_distances.sh\n\tpython3 test/verify_distances.py\n' >> Makefile

cat > .gitignore <<'GI'
.venv/
test/reference_distances.csv
GI

# Append Verify section to README
cat >> README.md <<'README'

## Verify

    make test
README

git add test/ Makefile .gitignore README.md
git commit -m "Add verification test against Gaia GSP-Phot reference distances"

make test
```

We write a verification script that fetches independent reference distances from Gaia's GSP-Phot pipeline and compares them to our computed values.

{{< snippet id="verify-distances" lang="python" lines="1-2,8,19,26-31,34-35,43" >}}

We add a `test` target to the Makefile so `make test` runs it:

```
$ make test
Fetched 48 reference distances
Compared 48 stars
Max error: 0.27%
PASSED: all within 0.5%
```

{{< step-link step="7" >}}

Without verification, a research object asks others to trust the results.
A test makes the claim falsifiable: anyone can run `make test` and see for themselves.

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
├── .gitignore
├── Makefile
└── README.md
```

**Advances**: A (verifiable results, not just "trust me")

### 8. Declare and pin dependencies

```sh
# pragma: testrun full-build
# pragma: render hidden
# snippet: fetch-data-requests
cat > code/fetch_data.py <<'PYEOF'
#!/usr/bin/env python3
"""Fetch nearby star parallax data from Gaia DR3 via TAP query."""

import requests
import sys

GAIA_TAP_URL = "https://gea.esac.esa.int/tap-server/tap/sync"

QUERY = """\
SELECT TOP {limit}
    source_id, parallax
FROM gaiadr3.gaia_source
WHERE parallax > {min_parallax}
    AND parallax_error / parallax < {max_error_ratio}
ORDER BY parallax DESC
"""


def fetch(output_path, limit=100, min_parallax=10, max_error_ratio=0.1):
    query = QUERY.format(
        limit=limit,
        min_parallax=min_parallax,
        max_error_ratio=max_error_ratio,
    )
    resp = requests.get(GAIA_TAP_URL, params={
        "REQUEST": "doQuery",
        "LANG": "ADQL",
        "FORMAT": "csv",
        "QUERY": query,
    })
    resp.raise_for_status()

    with open(output_path, "w") as f:
        f.write(resp.text)

    n_stars = resp.text.count("\n") - 1
    print(f"Fetched {n_stars} stars -> {output_path}")


if __name__ == "__main__":
    output = sys.argv[1] if len(sys.argv) > 1 else "raw/gaia_nearby.csv"
    fetch(output)
PYEOF
# /snippet

# snippet: pyproject
cat > pyproject.toml <<'TOML'
[project]
name = "stellar-distance"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
    "requests",
]
TOML
# /snippet
```

Until now the scripts used only Python's standard library (urllib, csv), so there was nothing to declare.
To demonstrate how dependencies are handled, we rewrite the fetch script to use `requests`:

{{< snippet id="fetch-data-requests" lang="python" lines="1-5,19,25-31" >}}

Without declaring the dependency, a fresh machine fails with `ModuleNotFoundError`. This is a Portability failure that only surfaces when someone else tries to run the code.

We add `pyproject.toml` to make the assumption explicit, then generate a hash-locked `requirements.txt`:

{{< snippet id="pyproject" lang="toml" >}}

```sh
# pragma: testrun full-build
pip-compile --generate-hashes -o requirements.txt pyproject.toml
```

```sh
# pragma: testrun full-build
# pragma: render hidden
# Append Requirements section to README
cat >> README.md <<'README'

## Requirements

- Python >= 3.10
- Dependencies declared in `pyproject.toml`; install with `pip install -r requirements.txt`
README

git add code/fetch_data.py pyproject.toml requirements.txt README.md
git commit -m "Rewrite fetch with requests, declare and pin dependencies"
```

There's a big difference between `requests` (any version) and `requests==2.32.5 --hash=sha256:...` (this exact build).
The first is a declaration: it says what we need.
The second is a distribution-ready specification: it says exactly what bytes to install.
Hash pinning means even if a package is re-uploaded with the same version number, the install rejects it rather than silently using different code.
This is where Portability meets Tracking: the environment specification itself is content-addressed.

{{< step-link step="8" >}}

**Advances**: P (host assumptions documented, reproducible environment), T (pinned versions are content-addressed)

### 9. Reproduce from scratch

```sh
# pragma: testrun full-build
# pragma: render hidden
# snippet: reproduce
cat > test/reproduce_from_scratch.sh <<'TESTSH'
#!/bin/sh
# Reproduce the full pipeline from a clean clone in a temp directory.
set -eux
PS4='> '

repo_url="${1:?Usage: $0 <repo-url-or-path>}"

cd "$(mktemp -d "${TMPDIR:-/tmp}/stellar-XXXXXXX")"
echo "Working in: $(pwd)"

git clone "$repo_url" stellar-distance
cd stellar-distance

python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt

make clean
make
make test

echo "=== PASSED: reproduced from scratch ==="
TESTSH
# /snippet
chmod +x test/reproduce_from_scratch.sh

git add test/reproduce_from_scratch.sh
git commit -m "Add ephemeral reproduction script"
```

We write `test/reproduce_from_scratch.sh`, a script that clones the repository into a fresh temp directory, creates a virtual environment, installs dependencies, runs the pipeline, and runs the tests:

{{< snippet id="reproduce" lang="sh" >}}

{{< step-link step="9" >}}

If it passes, the research object doesn't depend on anything from our machine. No accumulated state, no forgotten steps.
The temp directory is thrown away afterward.

This is the integration test for a research object.
Ephemeral reproduction exercises almost every STAMPED property at once: the project must be self-contained (S), the pipeline must actually run (A), it must work in a fresh environment (P), and there's no prior state to lean on (E).
If `reproduce_from_scratch.sh` passes, we have strong evidence that the research object is solid.
If it fails, the error tells us which property broke.

This is the [ephemeral shell reproducer]({{< ref "examples/ephemeral-shell-reproducer" >}}) pattern applied to our own project.

**Advances**: E (results produced without prior state), A (reproduction is a single command), S (validates that nothing outside the boundary is needed)

### 10. Push to GitHub

We push to a public repository.
Now anyone can `git clone`, `pip install -r requirements.txt`, `make`, and reproduce the result.

Until this step the research object was self-contained and reproducible, but only on our machine.
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
├── .gitignore
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
| **M** Modular | `code/`, `raw/`, `output/`, `test/` are logically separated. |
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
  --message "Fetch 200 nearest stars from Gaia DR3" \
  --output raw/gaia_nearby.csv \
  python3 code/fetch_data.py raw/gaia_nearby.csv
```

The new data is committed with a fresh provenance record.
Then `datalad rerun` of the analysis step picks up the new input and recomputes distances.
The full pipeline adapts to changed inputs without manual re-orchestration.

This is where modularity and provenance reinforce each other: because the fetch and analysis steps are recorded separately, we can update one without losing the provenance of the other.

### Modularity via subdatasets

Right now our modularity is directory-level: `code/`, `raw/`, `output/`.
That's a good start, but the raw data and the analysis code have different lifecycles.
The data might be shared across projects while the analysis code is specific to this one.

DataLad subdatasets take modularity further.
The raw data could live in its own independently versioned dataset:

```sh
datalad clone -d . DATA_URL raw/
```

A colleague running a different analysis on the same stars would `datalad install` the data module rather than re-fetching from the API.
The parent dataset records which exact version of each subdataset it depends on, so the full research object remains Self-contained and Tracked even as modules evolve independently.

### Containers for portability and ephemerality

Our `requirements.txt` pins Python packages, but what about the Python version itself? Or the OS libraries it links against?
A Dockerfile (pinned by image digest) freezes the OS and Python version.
Running the pipeline inside a disposable container validates that the specifications are complete.
If it works in a fresh container, it's not relying on anything from our machine.
See [Container venv overlay for Python development]({{< ref "examples/container-venv-overlay-development" >}}) for a detailed treatment of this pattern.

### CI for ephemeral validation

Step 9's reproduction test proves the pipeline works from scratch, but only when we remember to run it.
A GitHub Actions workflow that clones, installs, and runs `make test` on every push catches environment drift automatically: the same ephemeral test from step 9, run by someone else's machine on every change.

### Archival distribution

GitHub is where we collaborate, but repositories can be deleted, reorganized, or made private.
For long-term citability, deposit the repository on [Zenodo](https://zenodo.org/) for a DOI.
Push the container image to a registry.
Mirror data to multiple remotes so no single point of failure breaks reproducibility.

{{< mermaid >}}
graph TD
    subgraph external resources
        direction LR
        TAP[("Gaia TAP server<br/>(source data)")]
        PyPI[("PyPI<br/>(dependencies)")]
    end
    subgraph local machine
        direction LR
        P["research project<br/>(origin of work)"]
        E["ephemeral clone<br/>(verify reproducibility)"]
        style E stroke-dasharray: 5 5
        E2["ephemeral clone<br/>(verify reproducibility)"]
        style E2 stroke-dasharray: 5 5
        P -- "test/reproduce_from_scratch.sh $PWD" --> E
    end
    subgraph sharing and archival
        direction LR
        G["GitHub<br/>(collaborate & share)"]
        Z["Zenodo<br/>(long-term archive)"]
        D["DOI registrar"]
        G -- "archive a copy" --> Z
        Z -. "points" .-> G
        Z -. "mints" .-> D
    end
    TAP -- "datalad run<br/>(fetch parallax data)" --> P
    PyPI -- "pip install -r<br/>requirements.txt" --> E
    PyPI -- "pip install -r<br/>requirements.txt" --> E2
    P -- "git push" --> G
    D -. "resolves to" .-> Z
    G -- "git clone;<br/>make" --> E2
{{< /mermaid >}}

## Conclusion

We started with a script that worked on one machine and ended with a research object that anyone can clone, run, verify, and cite.
None of the individual steps were large: split some files, add a Makefile, write a test, pin dependencies.
Each one addressed a specific failure mode: "I can't remember how to run this," "it doesn't work on your machine," "how do I know the numbers are right?"

The STAMPED properties gave us a vocabulary for those failure modes and a way to check our progress.
Not every project needs every step, but knowing the spectrum makes it easier to decide what's worth doing next.
