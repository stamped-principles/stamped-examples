---
title: "Pixi walkthrough: stellar distances from Gaia parallax"
date: 2026-10-07
description: "Building a STAMPED research object that computes stellar distances from Gaia DR3 parallax data"
summary: "Incrementally builds a research object from a bare script to a tracked, portable, reproducible pipeline — motivated by real problems, not by acronym order."
tags: ["STAMPED-intro", "gaia", "parallax", "walkthrough", "python", "datalad", "pixi"]
stamped_principles: ["S", "T", "A", "M", "P", "E", "D"]
fair_principles: ["R", "A"]
instrumentation_levels: ["workflow"]
aspirations: ["reproducibility", "rigor", "transparency"]
params:
  tools: ["python", "git", "datalad", "pixi"]
  difficulty: "beginner"
  verified: false
  materialize_stem: "pixi-stellar-distance-walkthrough"
state: wip
---

```sh
#!/usr/bin/env bash
# pragma: testrun full-build
# pragma: render hidden
# pragma: requires sh bash git pixi
# pragma: timeout 600
# pragma: materialize stellar-distance

# The snippet runner invokes sh; activation below requires Bash.
if [ -z "${BASH_VERSION:-}" ]; then
    exec bash "$0" "$@"
fi

set -eux
PS4='> '

# Random temp dir for containment and security (no deterministic paths under /tmp)
cd "$(mktemp -d "${TMPDIR:-/tmp}/stellar-XXXXXXX")"
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
Each principle describes a spectrum: STAMPED gives us a vocabulary for choosing how much structure and tracking the work needs.

**The science**: we compute the distance to 100 nearby stars using parallax measurements from the [Gaia DR3](https://www.cosmos.esa.int/web/gaia/dr3) catalog.
The math is one line: `distance_pc = 1000 / parallax_mas`.
The result is a CSV of stellar distances in parsecs, verified against Gaia's own pipeline estimates to within 0.3%.

The analysis is deliberately simple so the focus stays on *how* we organize, track, and share the work.

## Steps

### 1. Set up our project

Install [Pixi](https://pixi.sh/latest/installation/) before starting.
Create the project and enter its environment:

```sh
pixi init stellar-distance --platform linux-64 --platform osx-arm64 --platform osx-64
cd stellar-distance/
pixi workspace platform edit linux-64 --glibc 2.34
pixi workspace platform edit osx-arm64 --macos 14.0
pixi workspace platform edit osx-64 --macos 15.0
pixi add "python>=3.10" git curl
pixi add --pypi datalad git-annex
pixi shell
git init

printf '\npixi.lock\n' >> .gitignore
```

Our project depends on Python and tools such as Git, curl, and DataLad.
`pixi add` installs these dependencies and records them in the `pixi.toml` manifest.
We track this manifest alongside the code.
Pixi keeps installed tools in the ignored `.pixi/` directory; we will consider retaining the generated lockfile in step 8.
`pixi shell` means all subsequent commands have access to the dependencies installed into the environment.

{{< detail title="Platform requirements for git-annex" >}} The platform settings declare the minimum host requirements for the git-annex wheel: glibc 2.34 on Linux, macOS 14 on Apple Silicon, and macOS 15 on Intel.
These settings let Pixi select compatible packages for each declared platform. {{< /detail >}}

```sh
# pragma: testrun full-build
# pragma: render hidden
pixi init stellar-distance --platform linux-64 --platform osx-arm64 --platform osx-64
cd stellar-distance/
pixi workspace platform edit linux-64 --glibc 2.34
pixi workspace platform edit osx-arm64 --macos 14.0
pixi workspace platform edit osx-64 --macos 15.0
pixi add "python>=3.10" git curl
pixi add --pypi datalad git-annex
eval "$(pixi shell-hook --shell bash)"
git init
git config user.email "demo@example.com"
git config user.name "Demo User"

printf '\npixi.lock\n' >> .gitignore

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
git add compute_everything.py distances.csv pixi.toml .gitignore .gitattributes
git commit -m "Initial analysis: compute stellar distances"
```

We start with a single Python script that does everything: queries the Gaia TAP API, fetches parallax measurements for 100 nearby stars, computes distances, and writes a CSV.

{{< snippet id="compute-everything" lang="python" lines="1-2,9-15,31-32" >}}

The above is abbreviated.
To follow along, see the {{< step-link step="1" text="full project at this step" >}}.

When we run `python3 compute_everything.py`, we get a `distances.csv` with 100 rows.
Proxima Centauri shows up at ~1.30 parsecs.
Looks right!

We put the script and its output in a directory and run `git init`.
Two things happen at once: we draw a boundary around the project (Self-containment), and we start recording its history (Tracking).
The project boundary follows the "don't look up" rule: everything needed for this work lives inside one root, and nothing outside should be implicitly required.
Git gives us content-addressed version control, so we can track changes over time and identify each project state by its commit.

From now on, every change is recorded and reversible.
That makes all subsequent steps low-risk.

```
stellar-distance/
├── compute_everything.py
├── distances.csv
└── pixi.toml
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
The data is no longer just "a CSV that appeared somehow."
It has a documented origin that anyone can inspect and replay with `datalad rerun`.

This also addresses a Self-containment concern.
Our analysis depends on an external network resource (the Gaia TAP API), which means it could break if the API changes or goes offline.
Once we've fetched the data with `datalad run`, we have our own versioned copy.
The API is still the authoritative source, but we're no longer silently dependent on it.
The provenance record documents where the data came from, and the committed CSV means the analysis can proceed offline.

`datalad run` works on plain git repositories.
No special initialization required.
It creates a normal git commit whose message includes a machine-readable run record (the command, inputs, and outputs), so `git log` still tells the whole story.

```
stellar-distance/
├── compute_distances.py
├── fetch_data.py
├── gaia_nearby.csv
└── pixi.toml
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
├── output/
│   └── distances.csv
└── pixi.toml
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

### 6. Define Pixi tasks

```sh
# pragma: testrun full-build
# pragma: render hidden
# snippet: pixi-tasks
cat >> pixi.toml <<'TOML'

[tasks.fetch]
cmd = "test -f raw/gaia_nearby.csv || datalad run --explicit -m 'Fetch Gaia parallaxes' -i code/fetch_data.py -i pixi.toml -o raw/gaia_nearby.csv -- python code/fetch_data.py raw/gaia_nearby.csv"

[tasks.compute]
cmd = "datalad run --explicit -m 'Compute stellar distances' -i raw/gaia_nearby.csv -i code/compute_distances.py -i pixi.toml -o output/distances.csv -- python code/compute_distances.py raw/gaia_nearby.csv output/distances.csv"
depends-on = ["fetch"]
inputs = ["raw/gaia_nearby.csv", "code/compute_distances.py"]
outputs = ["output/distances.csv"]

[tasks.all]
depends-on = ["compute"]

[tasks.clean]
cmd = "rm -f output/distances.csv"
TOML
# /snippet

# Update README: replace manual commands with 'pixi run all'.
python3 - <<'PYEOF'
from pathlib import Path
path = Path("README.md")
text = path.read_text()
text = text.replace(
    "    python3 code/fetch_data.py raw/gaia_nearby.csv\n"
    "    python3 code/compute_distances.py raw/gaia_nearby.csv output/distances.csv",
    "    pixi run all",
)
path.write_text(text)
PYEOF

git add pixi.toml README.md
git commit -m "add Pixi tasks encoding the full pipeline"
```

Add these task definitions to `pixi.toml` to encode the pipeline and its dependencies:

{{< snippet id="pixi-tasks" lang="toml" >}}

{{< step-link step="6" >}}

The README *says* how to run the pipeline.
The Pixi tasks *do* it.
This is the jump from documented to executable: the Actionability spectrum in action (A.2).
The `depends-on` entries put the steps in order.
The fetch task keeps the existing raw data when present.
The compute task declares its inputs and output so Pixi can skip unchanged work.
When it runs, DataLad records the explicit Python command; the scripts themselves remain independent of DataLad.
The same manifest now describes both our tools and how to use them.

Many readers will recognize a pattern similar to a Makefile.
Pixi’s task definitions are more verbose, but their explicit fields can be easier to follow.
They also connect each step to its software environment; different tasks can use different environments, although this example needs only one.

Now `pixi run all` is the single command to reproduce everything.
We update the README accordingly.

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

ids=$(tail -n +2 output/distances.csv | cut -d, -f1 | paste -sd, -)

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

# Add reference acquisition and verification tasks.
cat >> pixi.toml <<'TOML'

[tasks.reference]
cmd = "test -f test/reference_distances.csv || datalad run --explicit -m 'Fetch Gaia reference distances' -i output/distances.csv -i test/fetch_reference_distances.sh -i pixi.toml -o test/reference_distances.csv -- sh test/fetch_reference_distances.sh"
depends-on = ["all"]

[tasks.test]
cmd = "python test/verify_distances.py"
depends-on = ["reference"]
TOML

# Append Verify section to README
cat >> README.md <<'README'

## Verify

    pixi run test
README

git add test/ pixi.toml .gitignore README.md
git commit -m "Add verification test against Gaia GSP-Phot reference distances"

pixi run test
```

We fetch independent reference distances from Gaia's GSP-Phot pipeline and write a verification script that compares them to our computed values.

{{< snippet id="verify-distances" lang="python" lines="1-2,8,19,26-31,34-35,43" >}}

We add a `test` task depending on reference acquisition, so `pixi run test` runs the comparison.
The reference task keeps its downloaded CSV; removing that file explicitly requests a fresh acquisition.
On the first run:

```
$ pixi run test
Fetched 48 reference distances
Compared 48 stars
Max error: 0.27%
PASSED: all within 0.5%
```

{{< step-link step="7" >}}

Without verification, a research object asks others to trust the results.
A test makes the claim falsifiable: anyone can run `pixi run test` and see for themselves.

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
├── pixi.toml
└── README.md
```

**Advances**: A (verifiable results, not just "trust me")

### 8. Retain a dependency selection

So far, `pixi.toml` has declared the Python, Git, curl, and DataLad dependencies our project needs.
Those requirements can allow several versions; tighter constraints narrow the choice but do not identify every transitive dependency.
For a result we want to share and recover, we now retain the generated `pixi.lock`.
It records the resolved package versions and hashes for each declared platform, including platform-specific conda-forge binaries.
This lets collaborators install the selected packages appropriate to their platform.

{{< detail title="Tracking a previously ignored lockfile" >}} We initially excluded `pixi.lock` from Git.
`git add -f` overrides that exclusion; once tracked, subsequent changes are handled normally by Git. {{< /detail >}}

```sh
# pragma: testrun full-build
git add -f pixi.lock
```

```sh
# pragma: testrun full-build
# pragma: render hidden
# Append Requirements section to README
cat >> README.md <<'README'

## Requirements

- Pixi, Git, and a POSIX shell
- Dependencies declared in `pixi.toml` and pinned in `pixi.lock`;
  install with `pixi install --locked`
README

git add pixi.toml README.md
git commit -m "build: pin the project environment"
```

Commit both files so a collaborator can install the recorded environment with `pixi install --locked`.
`--locked` rejects a manifest/lock mismatch instead of updating the lock automatically.
Ordinary Pixi execution reuses a suitable lock but can update it when requirements change.

Retaining a resolved environment strengthens rigor by making a particular result easier to recover, but maintaining it can cost convenience and efficiency during exploration.
Lock changes can produce noisy diffs and interrupt otherwise useful dependency updates.
One compromise is to preserve the manifest and lock on a result branch or tagged checkpoint while continuing development separately.
Keeping a built container image offers another way to retain the environment, with storage and distribution costs: the image becomes a durable artifact even though the containers launched from it can remain disposable.
The appropriate balance depends on what we need to recover, and how often.
See the [Pixi lockfile documentation](https://pixi.prefix.dev/latest/workspace/lock_file/) for execution options.

{{< step-link step="8" >}}

**Advances**: P (host assumptions documented, reproducible environment), T (pinned versions are content-addressed)

### 9. Reproduce from scratch

In a fresh clone of the repository, reproduce and verify the analysis with:

```sh
pixi run --locked test
```

Pixi prepares the recorded environment and runs the task dependencies, recomputing distances and checking them against the retained reference data.
On subsequent runs in the same workspace, Pixi may reuse cached computation.
The `.pixi/` directory is disposable: we preserve its specification and recreate the installed tools when needed.

This brings several STAMPED properties together: the project supplies its inputs and instructions (S), its tasks make the analysis executable (A), and its environment can be recreated (P, E).
For a more careful treatment of isolated reproduction, see the [ephemeral shell reproducer]({{< ref "examples/ephemeral-shell-reproducer" >}}).

**Advances**: E (replaceable working environment), A (reproduction is a single command), S (inputs and instructions travel with the project)

### 10. Push to GitHub

We push to a public repository.
Now anyone can `git clone`, `pixi run --locked all`, and reproduce the result.

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
│   └── verify_distances.py
├── .gitignore
├── pixi.toml
├── pixi.lock
└── README.md
```

**Advances**: D (persistently retrievable by others)

## STAMPED scorecard

| Property | Where we ended up |
|---|---|
| **S** Self-contained | All code, data, and instructions under one root. README describes the project. Versioned local copy of fetched data. |
| **T** Tracked | Git tracks all changes. `datalad run` records provenance for both fetch and analysis. Dependencies hash-pinned. |
| **A** Actionable | `pixi run all` reproduces results. `pixi run test` verifies. `datalad rerun` replays provenance. README documents the workflow. |
| **M** Modular | `code/`, `raw/`, `output/`, `test/` are logically separated. |
| **P** Portable | Dependencies declared in pixi.toml, pinned in pixi.lock with hashes. No hardcoded paths. |
| **E** Ephemeral | A fresh clone recreates the environment and recomputes from retained inputs. |
| **D** Distributable | Repository on GitHub. Anyone can clone and reproduce. |

## Where to go from here

Each STAMPED property is a spectrum.
We've built something solid, but there are natural next steps depending on what the project needs.

### Replay and adapt with datalad rerun

Because we recorded an explicit computation with `datalad run`, we can apply that command again after changing its code or inputs.
For example, expand the sample to 200 stars by editing and saving the query in `code/fetch_data.py`, then record a new acquisition:

```sh
datalad run \
  --message "Fetch 200 nearest stars from Gaia DR3" \
  --input code/fetch_data.py \
  --output raw/gaia_nearby.csv \
  -- python code/fetch_data.py raw/gaia_nearby.csv
```

Select the analysis run's commit from `git log` and replay it on the current state:

```sh
pixi run --locked -- datalad rerun ANALYSIS_RUN_REV
```

The recorded command uses the revised input to recompute distances.
The comparison also needs reference distances for the expanded sample; remove `test/reference_distances.csv` before running `pixi run test` to refresh them.
This is where modularity and provenance reinforce each other: we can update one step while retaining the history of the others.

Recovering a historical result asks a different question from applying a procedure to changed inputs.
[Choosing what stays fixed during replay]({{< ref "guides/choosing-what-changes" >}}) explores that distinction, including `datalad rerun --onto` and selecting the intended Pixi environment.

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

Our `pixi.lock` pins Python and its environment packages, but the host operating system is still external.
A Dockerfile (pinned by image digest) freezes the OS and Python version.
Running the pipeline inside a disposable container validates that the specifications are complete.
If it works in a fresh container, it's not relying on anything from our machine.
See [Container venv overlay for Python development]({{< ref "examples/container-venv-overlay-development" >}}) for a detailed treatment of this pattern.

Pixi also supports separate environments for different tasks and dependency specifications embedded in standalone scripts, useful when exploration needs tools beyond the main analysis.

### CI for ephemeral validation

Step 9's reproduction test proves the pipeline works from scratch, but only when we remember to run it.
A GitHub Actions workflow that clones and runs `pixi run --locked test` on every push catches environment drift automatically: the same ephemeral test from step 9, run by someone else's machine on every change.

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
        Packages[("conda-forge / PyPI<br/>(dependencies)")]
    end
    subgraph local machine
        direction LR
        P["research project<br/>(origin of work)"]
        E["ephemeral clone<br/>(verify reproducibility)"]
        style E stroke-dasharray: 5 5
        E2["ephemeral clone<br/>(verify reproducibility)"]
        style E2 stroke-dasharray: 5 5
        P -- "fresh clone; pixi run --locked test" --> E
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
    Packages -- "pixi install<br/>--locked" --> E
    Packages -- "pixi install<br/>--locked" --> E2
    P -- "git push" --> G
    D -. "resolves to" .-> Z
    G -- "git clone;<br/>pixi run --locked all" --> E2
{{< /mermaid >}}

## Conclusion

We started with a script that worked on one machine and ended with a research object that anyone can clone, run, verify, and cite.
None of the individual steps were large: split some files, add Pixi tasks, write a test, pin dependencies.
Each one addressed a specific failure mode: "I can't remember how to run this," "it doesn't work on your machine," "how do I know the numbers are right?"

The STAMPED properties gave us a vocabulary for those failure modes and a way to check our progress.
Not every project needs every step, but knowing the spectrum makes it easier to decide what's worth doing next.
