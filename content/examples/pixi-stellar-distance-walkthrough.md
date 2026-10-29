---
title: "Reusing the Gaia analysis with Pixi and DataLad"
date: 2026-10-28
description: "Continue the Gaia example with shared task and environment configuration."
summary: "Reuse the completed Gaia project, then explore what to rerun, which environment to select, and what to record with Pixi and DataLad."
tags: ["gaia", "parallax", "walkthrough", "python", "datalad", "pixi"]
stamped_principles: ["S", "T", "A", "M", "P", "E", "D"]
fair_principles: ["R", "A"]
instrumentation_levels: ["workflow"]
aspirations: ["reproducibility", "rigor", "transparency", "efficiency"]
params:
  tools: ["python", "git", "datalad", "pixi"]
  difficulty: "intermediate"
  verified: true
  materialize_stem: "pixi-stellar-distance-walkthrough"
---

The [Gaia walkthrough]({{< ref "examples/stellar-distance-walkthrough" >}}) showed how small, practical changes turn a working analysis into a research object that embodies the STAMPED principles: its data and code are organized and tracked, its workflow is executable, and its results can be verified and shared.
We now build on that foundation to explore how those properties support reuse as the data, tasks, and execution environment change.

Suppose a collaborator wants to repeat the calculation, use a different sample, or revisit an earlier result.
The existing setup supports these goals, but leaves several things to coordinate:

- Learning the workflow: `Make` and it's associated Makefile introduces its own syntax and conventions alongside Python, shell commands, and dependency files.
- Installing all the tools: The requirements lock records Python packages, but leaves the Python interpreter and tools such as Git and curl outside that specification.
- Working across platforms: The Makefile and shell commands assume a Unix-like environment; Windows users need additional setup.
- Revisiting earlier work: Checking out an older commit restores its code and dependency specification, but updating the active environment remains a separate, manual step.

[Pixi](https://pixi.prefix.dev/latest/) brings task execution and environment selection into the same project configuration.
It builds on conda-forge’s language-agnostic, cross-platform package ecosystem to manage Python interpreters, libraries, and command-line tools together.
The equivalent of targets in the previous Makefile are "tasks".
Tasks are specified in the existing Python metadata format (TOML), and invoking a task prepares the environment specified by the checked-out project.
Collaborators can run the analysis without assembling the environment themselves, and changes to the tasks and dependencies are recorded together.

Combining Pixi with DataLad's execution records, we can express both how to run the analysis and which inputs, outputs, and environment specifications belong to a run.
STAMPED gives us a vocabulary for deciding how much of that context to retain.

## 1. Migrate to Pixi

Install [Pixi](https://pixi.prefix.dev/latest/installation/) and clone the example sources:

```sh
pixi exec --spec git -- git clone --recurse-submodules \
  https://github.com/stamped-principles/stamped-examples.git
cd stamped-examples/examples/gaia-pixi
```

This directory contains the migration script and `gaia/`, a git submodule recording an exact commit of the completed Gaia analysis (from the previous example).

```sh
# pragma: testrun full-build
# pragma: render hidden
#!/bin/sh
# pragma: requires sh git pixi
# pragma: timeout 900
# pragma: materialize analysis
# pragma: source examples/gaia-pixi/migrate-gaia-to-pixi.py
# pragma: source examples/gaia-pixi/pyproject.expected.toml
# pragma: source examples/gaia-pixi/extension/estimate_distances.py
# pragma: source examples/gaia-pixi/extension/fetch_uncertainties.py
# pragma: source examples/gaia-pixi/extension/plot_distances.py
# pragma: source examples/gaia-pixi/extension/record.py
# pragma: source examples/gaia-pixi/extension/validate.py
# pragma: submodule examples/gaia-pixi/gaia
set -eu
source_bundle="$PWD/examples/gaia-pixi"
test -e "$source_bundle/gaia/.git" || git submodule update --init -- examples/gaia-pixi/gaia
cd "$(mktemp -d "${TMPDIR:-/tmp}/stellar-pixi-XXXXXX")"
pixi exec --spec git --spec python --spec tomlkit -- python "$source_bundle/migrate-gaia-to-pixi.py"
cd analysis
```

Create and migrate a separate analysis repository:

```sh
pixi exec --spec git --spec python --spec tomlkit -- python migrate-gaia-to-pixi.py
cd analysis
```

The script leaves `gaia/` untouched and creates `analysis/` with its Git history intact.
The subsequent commits and DataLad records belong to this derived repository.
We also record the source revision, Gaia revision, and migration-script hash used to create it in `pixi-source.json`.

While keeping the existing Python requirements and analysis scripts, this script makes the following changes:

- Adds the workflow's command-line tools and DataLad to `pyproject.toml`
- Replaces Make targets with Pixi tasks, including their dependencies and the computation's inputs and outputs
- Updates the reproduction instructions (to use our pixi setup)

{{< detail title="The complete pyproject.toml" >}} {{< file-code path="examples/gaia-pixi/pyproject.expected.toml" lang="toml" >}} {{< /detail >}}

Run the equivalent workflow:

```sh
# pragma: testrun full-build
pixi run all
pixi run clean
pixi run test
```

- `pixi run all` runs the calculation using the saved observations, as `make` did.
- `pixi run clean` removes the calculated output, as `make clean` did.
- `pixi run test` recomputes the missing output, fetches reference distances, and verifies the result, as `make test` did.

`pixi run` prepares the environment automatically and, in addition to these tasks, it can be used to run any of the software in the environment.
Save the changes and generated `pixi.lock` with the project.

```sh
# pragma: testrun full-build
# pragma: render hidden
pixi run git config user.name "Demo User"
pixi run git config user.email "demo@example.com"
pixi run git add pyproject.toml pixi.lock .gitignore Makefile requirements.txt README.md test/ code/extension migrate-gaia-to-pixi.py pixi-source.json
pixi run git commit -m "build: express the Gaia workflow with Pixi"
```

{{< step-link step="1" >}}

## 2. Extend the calculation with uncertainty

The original calculation gives one distance per star.
How much precision does that number imply, and do the small differences from Gaia's estimates matter at that scale?
We will propagate the reported parallax errors and then plot a comparison, using separate environments for the numerical analysis and figure.

The source bundle includes ordinary [analysis and plotting scripts](https://github.com/stamped-principles/stamped-examples/tree/main/examples/gaia-pixi/extension), copied into `code/extension/` by the migration.
We first query DR3 for the same source IDs to add parallax errors and GSP-Phot distance intervals.
As in the previous example, DataLad records the acquisition command and its output, and subsequent runs reuse the saved data.
The numerical task checks the IDs and parallaxes against our baseline before using them.

Add the scientific dependencies and register the analysis tasks:

```sh
# pragma: testrun full-build
pixi task add uncertainties "test -f raw/gaia_uncertainties.csv || python code/extension/record.py acquisition"
pixi workspace environment add analysis
pixi add --environment analysis numpy scipy
pixi task add --environment analysis validate "python code/extension/validate.py"
pixi task add --environment analysis estimate "python code/extension/record.py analysis"
```

The `analysis` environment inherits the project's existing dependencies and adds NumPy and SciPy.
The `estimate` task uses a small inspectable DataLad wrapper: it records the saved observations, original distances, uncertainty snapshot, script, manifest, and lock as inputs, and the interval table and summary as outputs.
Its recorded command explicitly selects the `analysis` environment.

```sh
# pragma: testrun full-build
pixi run datalad create --force --no-annex .
pixi run git add pyproject.toml pixi.lock code/extension
pixi run git commit -m "feat: add the uncertainty analysis environment"
pixi run --locked uncertainties
pixi run --environment analysis validate
pixi run --environment analysis --locked estimate
```

```sh
# pragma: testrun full-build
# pragma: render hidden
acquisition_head=$(git rev-parse HEAD)
pixi run --locked uncertainties
test "$(git rev-parse HEAD)" = "$acquisition_head"
```

`output/distance_intervals.csv` now includes a distance interval for every star, along with the reference values where available.
`output/distance_summary.json` identifies the largest differences by source ID.
The central estimate remains `1000 / parallax`; the extension supplies uncertainty rather than inventing a different point estimate.

{{< detail title="What the uncertainty calculation means" >}} For parallax `p` with standard error `s`, the script constructs a central 68% Gaussian confidence interval and transforms its endpoints to distance:

```text
z = normal_quantile(0.84)
distance = 1000 / p
lower = 1000 / (p + z*s)
upper = 1000 / (p - z*s)
```

The interval is asymmetric because taking a reciprocal is nonlinear.
The script rejects cases whose lower parallax bound is nonpositive.
Validation checks known endpoints, the small-error limit, invalid inputs, and simulated coverage under the assumed Gaussian measurement model.
For this precise nearby-star sample the asymmetry is small; the figure shows its size rather than exaggerating it.

These intervals propagate random parallax errors only, retaining the original example's uncorrected parallaxes.
They do not include zero-point systematics or model a distance prior, so they are not a general-purpose replacement for Gaia distance inference.
See [Bailer-Jones on distance estimation and zero-point effects](https://bailer-jones.www3.mpia.de/gedr3_distances/FAQ.html).
GSP-Phot's reported limits are its 16th and 84th percentiles; it also uses parallax alongside photometry and spectra, so this comparison is not an independent validation against ground truth.
See the [Gaia DR3 field descriptions](https://gaia.aip.de/metadata/gaiadr3/gaia_source/). {{< /detail >}}

{{< step-link step="2" >}}

## 3. Make a figure in a separate environment

A collaborator can now reproduce the numerical results without installing a plotting stack.
For the figure, add a separate environment and task:

```sh
# pragma: testrun full-build
pixi workspace environment add plotting
pixi add --environment plotting matplotlib
pixi task add --environment plotting figure "python code/extension/record.py plotting"
pixi run git add pyproject.toml pixi.lock
pixi run git commit -m "feat: add a separate plotting environment"
pixi run --environment plotting --locked figure
```

The plotting environment inherits the common project tools, but not the analysis environment’s additional dependencies.
The figure reads the saved interval table; it does not rerun the calculation or query Gaia.
DataLad records the figure's relationship to that table, the plotting script, and its selected environment.

The PNG and SVG in `figures/` show:

- The reference differences for every matched source, relative to the original calculation.
- How the nonlinear transformation makes the distance intervals asymmetric.
- The eight largest absolute reference differences, with full source IDs, original point estimates, propagated intervals, and Gaia's published intervals.

![Comparison of original inverse-parallax distances, propagated uncertainty intervals, and Gaia GSP-Phot estimates.](/images/examples/gaia-pixi-distance-comparison.png)

The distinction between the two environments now has a purpose: change the plot's labels, layout, or plotting dependencies without changing the analysis dependency declarations, then rerun `pixi run --environment plotting figure` against the same saved results.
Conversely, numerical reproduction needs only the `analysis` environment.

```sh
# pragma: testrun full-build
# pragma: render hidden
pixi run --environment analysis python -c "import importlib.util; assert importlib.util.find_spec('matplotlib') is None"
pixi run --environment plotting python -c "import importlib.util; assert importlib.util.find_spec('scipy') is None"
pixi run --environment plotting python -c "from pathlib import Path; assert Path('figures/distance_comparison.png').stat().st_size > 10000; assert Path('figures/distance_comparison.svg').is_file()"
```

{{< step-link step="3" >}}

## Reuse the recorded work

Commit and share the derived analysis repository.
A collaborator can recreate either part from its saved inputs:

```sh
pixi run --environment analysis --locked estimate
pixi run --environment plotting --locked figure
```

The first command records the numerical outputs; the second records the figure made from them.
Neither requires a live Gaia query because the input snapshot travels with the project.
`pixi run uncertainties` reuses the saved CSV, or fetches and records it if missing.
To deliberately query Gaia again and record an updated snapshot, run:

```sh
pixi run --locked python code/extension/record.py acquisition
```

The acquisition record names the baseline source IDs, fetch script, manifest, and lock as inputs.
It can also be replayed with `datalad rerun`, as in the previous example; the pinned Gaia baseline remains unchanged.

[Choosing what stays fixed during replay]({{< ref "guides/choosing-what-changes" >}}) explains how to apply a recorded command to changed inputs or recover a historical computation.
Here, the source submodule identifies the starting analysis, Pixi selects the tools for each extension, and DataLad connects the resulting tables and figures to their inputs.

```sh
# pragma: testrun full-build
# pragma: render hidden
(
    source_repo="$PWD"
    clone_dir=$(mktemp -d "${TMPDIR:-/tmp}/gaia-extension-reproduce-XXXXXX")
    trap 'rm -rf "$clone_dir"' EXIT
    git clone "$source_repo" "$clone_dir/project"
    cd "$clone_dir/project"
    rm output/distance_intervals.csv output/distance_summary.json
    pixi run --environment analysis --locked estimate
    test ! -d .pixi/envs/plotting
    cmp "$source_repo/output/distance_intervals.csv" output/distance_intervals.csv
    pixi run --environment plotting --locked figure
)
```
