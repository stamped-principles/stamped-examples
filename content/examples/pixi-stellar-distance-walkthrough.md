---
title: "Extending the Gaia analysis with Pixi and DataLad"
date: 2026-10-29
description: "Reuse a Gaia research object, propagate measurement uncertainty, and record the analysis and figure with Pixi and DataLad."
summary: "Build on the original Gaia distances to produce an uncertainty-aware comparison and a reusable STAMPED research object."
tags: ["gaia", "parallax", "python", "datalad", "pixi"]
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

The [previous Gaia analysis]({{< ref "examples/stellar-distance-walkthrough" >}}) calculated distances for 100 nearby stars from their parallaxes and compared them with Gaia DR3's GSP-Phot estimates.
Those point estimates raise a scientific question: **how much precision do the distances imply, and how large are the differences between the estimates relative to their uncertainty?** Here we extend that work with measurement uncertainties and a figure that makes the comparison visible.

Extending an analysis also means extending its software environment: we need new numerical libraries for the uncertainty calculation and plotting tools for the figure.
The previous example specified Python packages and used Make to organize commands, while setting up the interpreter and command-line tools remained separate steps.
[Pixi](https://pixi.prefix.dev/latest/) brings these pieces together: it manages environments containing Python, libraries, and tools such as Git and DataLad, and associates executable tasks with those environments.
Running a task prepares its environment and executes the command, making the same workflow convenient to use on another machine or after returning to an earlier project revision.

This fits naturally with the DataLad workflow we already have.
A recorded command can select its Pixi environment, with the environment specification and lockfile tracked alongside its code and data.
We can then repeat a calculation, revise a figure, or explore a change in dependencies while keeping those choices connected to the results.
Here we use that combination to build on the original research object's STAMPED properties, making a scientific extension easier to run, examine, and reuse.

## Reuse the original analysis

Install [Pixi](https://pixi.prefix.dev/latest/installation/) and clone the analysis repository:

{{< gaia-clone >}}

The log shows how the analysis we will work through is built, from project preparation through data acquisition, calculation, and plotting.
We check out a fresh local branch, `my-analysis`, to start prior to the execution of those computations.
The scripts and software configuration are ready; our task executions will now create the results and their records.
The completed analysis remains in the original branch, and the checkpoint links below show its successive stages.

The earlier Gaia research object lives at `inputs/gaia/` as a Git submodule.
It carries the original code, observations, results, and history, and our project records the exact revision used.
We record our additional measurements and results in the extension dataset, alongside the original research object.
Another researcher can reuse either the original analysis or this extension, with the history needed to understand each.
This is STAMPED Modularity: we build a new analysis from an existing research object while preserving its provenance.

```text
inputs/gaia/       original Gaia research object, pinned to a commit
code/             acquisition, uncertainty analysis, plotting, validation
raw/              acquired uncertainty measurements
output/           reproduced distances, interval table, summary
figures/          reported figure
pyproject.toml    tasks and environment declarations
pixi.lock         resolved software versions
```

The adaptation to Pixi is already included.
We can immediately repeat the original calculation:

```sh
# pragma: testrun full-build
# pragma: render hidden
#!/bin/sh
# pragma: requires sh git pixi python3
# pragma: timeout 900
# pragma: materialize analysis
# pragma: source examples/gaia-pixi/prepare-project.py
# pragma: source examples/gaia-pixi/pyproject.toml
# pragma: source examples/gaia-pixi/pixi.lock
# pragma: source examples/gaia-pixi/project-README.md
# pragma: source examples/gaia-pixi/extension/estimate_distances.py
# pragma: source examples/gaia-pixi/extension/fetch_uncertainties.py
# pragma: source examples/gaia-pixi/extension/plot_distances.py
# pragma: source examples/gaia-pixi/extension/validate.py
# pragma: submodule examples/gaia-pixi/gaia
set -eu
source_bundle="$PWD/examples/gaia-pixi"
test -e "$source_bundle/gaia/.git" || git submodule update --init -- examples/gaia-pixi/gaia
cd "$(mktemp -d "${TMPDIR:-/tmp}/stellar-pixi-XXXXXX")"
python3 "$source_bundle/prepare-project.py"
cd analysis
pixi run git config user.name "Demo User"
pixi run git config user.email "demo@example.com"
pixi run datalad create --force --no-annex .
pixi run git add .
pixi run git commit -m "build: prepare Gaia extension"
test ! -e raw/gaia_uncertainties.csv
test ! -e output/distances.csv
test ! -e figures/distance_comparison.png
test -z "$(git log --format=%s --grep='DATALAD RUNCMD')"
```

```sh
# pragma: testrun full-build
pixi run baseline
```

{{< detail title="Using the lockfile when reproducing a result" >}} Pixi normally uses `pixi.lock` to prepare the environment; if the dependency declarations have changed, it may update the lockfile.
Adding `--locked`, as in `pixi run --locked baseline`, requires the existing lockfile to agree with the manifest and fails if it needs updating.
This is useful for reproduction checks and automated runs.
The DataLad commands in our task definitions retain `--locked` so replay uses a consistent environment specification.
When intentionally changing dependencies, update and save the manifest and lockfile before recording the new analysis.
See the [Pixi run options](https://pixi.prefix.dev/latest/reference/cli/pixi/run/). {{< /detail >}}

The task executes the original `inputs/gaia/code/compute_distances.py` against its saved observations and writes `output/distances.csv` in our project.
Our verification step checks that the reproduced table agrees exactly with the earlier result.
This is direct reuse of the original code and data, with the execution environment now specified by Pixi.

{{< detail title="The baseline task and the adaptation to Pixi" >}} {{< file-code path="examples/gaia-pixi/pyproject.toml" section="tool.pixi.tasks.baseline" lang="toml" >}}

The original Make targets become named Pixi tasks, and the software specification now includes Python, Git, and DataLad alongside the scientific libraries.
The original computation accepts input and output paths, so we can run it directly from its pinned dataset.
The extension's verification script checks the reproduced table and new intervals; the original reference-comparison procedure remains available in `inputs/gaia/test/`.
[How we prepared this project](https://github.com/stamped-principles/stamped-examples/blob/main/examples/gaia-pixi/prepare-project.py): the preparation script adds the original analysis as a submodule and copies in the extension scripts, Pixi configuration, and README. {{< /detail >}}

{{< step-link step="2" text="Research object after reproducing the baseline" >}}

## Acquire the uncertainty measurements

Gaia reports a standard error for each parallax measurement.
We will use those errors to construct parallax intervals and transform their endpoints into distance bounds, showing the precision of the original estimates under a stated measurement model.
We also retrieve GSP-Phot's reported distance intervals for comparison.

The acquisition script uses the original source IDs to query Gaia DR3 for these additional measurements for the same stars.
The Pixi task shows the command that DataLad will record, together with its inputs and outputs:

{{< file-code path="examples/gaia-pixi/pyproject.toml" section="tool.pixi.tasks.acquire" lang="toml" >}}

```sh
# pragma: testrun full-build
pixi run acquire
```

This queries the archive and records its response in `raw/gaia_uncertainties.csv`.

We now have a saved response to use in the remaining steps.
A collaborator starting from our completed analysis can reuse this response, or run `acquire` to record a new query.
Recording and sharing the acquired measurements lets collaborators inspect the data underlying a result and choose explicitly when to request a new snapshot.

{{< step-link step="3" text="Research object with the recorded Gaia response" >}}

## Estimate distance uncertainty

We reuse NumPy's numerical operations and SciPy's normal-distribution quantile function to calculate the intervals.
The `analysis` environment declares those libraries, while our short analysis script implements the transformation and verifies that the source IDs and parallaxes match the original observations.

{{< file-code path="examples/gaia-pixi/pyproject.toml" section="tool.pixi.feature.analysis.dependencies" lang="toml" >}}

{{< detail title="The estimate task: explicit command, inputs, and outputs" >}} {{< file-code path="examples/gaia-pixi/pyproject.toml" section="tool.pixi.feature.analysis.tasks.estimate" lang="toml" >}} {{< /detail >}}

```sh
# pragma: testrun full-build
pixi run estimate
pixi run verify
```

The `estimate` and `verify` tasks belong to the `analysis` environment, so Pixi selects it from the task name.
We can run either task without selecting the environment ourselves.

`output/distance_intervals.csv` contains the original point estimates, propagated distance bounds, and available GSP-Phot estimates and intervals.
`output/distance_summary.json` records sample coverage and identifies the largest reference differences by source ID.
The `verify` task checks agreement with the original distance table, tests the interval calculation, and recomputes the saved numerical results for comparison.

{{< detail title="Scientific method and interpretation of the intervals" >}} For parallax `p` and standard error `s`, both in milliarcseconds, we assume Gaussian measurement errors and invert a central 68% parallax confidence interval:

```text
z = normal_quantile(0.84)
distance_pc = 1000 / p
lower_pc = 1000 / (p + z*s)
upper_pc = 1000 / (p - z*s)
```

Taking a reciprocal makes the distance interval asymmetric.
The script requires a positive lower parallax bound, and validation covers known endpoints, the small-error limit, invalid measurements, and simulated coverage under the Gaussian model.

These intervals describe random measurement error using the original uncorrected parallaxes.
They omit zero-point systematics and distance priors; see [Bailer-Jones's discussion of Gaia distance inference](https://bailer-jones.www3.mpia.de/gedr3_distances/FAQ.html) for the broader inference problem.
GSP-Phot's limits are its 16th and 84th percentiles, and its estimates use parallax alongside photometry and spectra.
The comparison therefore describes agreement between related estimates rather than an independent test against ground truth.
See the [Gaia DR3 field descriptions](https://gaia.aip.de/metadata/gaiadr3/gaia_source/). {{< /detail >}}

{{< step-link step="4" text="Research object with the numerical results and methods" >}}

## Create a figure in a separate environment

Let's now plot these results.
We use a separate plotting environment so the dependencies for the numerical analysis and figure can be managed separately.
Collaborators recreate the environments for the steps they want to run.
Matplotlib produces the figure from the saved interval table:

{{< file-code path="examples/gaia-pixi/pyproject.toml" section="tool.pixi.feature.plotting.dependencies" lang="toml" >}}

{{< detail title="The figure task" >}} {{< file-code path="examples/gaia-pixi/pyproject.toml" section="tool.pixi.feature.plotting.tasks.figure" lang="toml" >}} {{< /detail >}}

```sh
# pragma: testrun full-build
pixi run figure
```

![Comparison of original inverse-parallax distances, propagated uncertainty intervals, and Gaia GSP-Phot estimates.](/images/examples/gaia-pixi-distance-comparison.png)

{{< detail title="Reading the stellar-distance comparison" >}} Gaia supplies GSP-Phot comparisons for 48 of the 100 stars in this sample.
The largest absolute difference from the inverse-parallax estimate is about 0.27%.
The top-left panel shows these differences; the uncertainty intervals below put their size in context.
The top-right panel shows how interval asymmetry increases with fractional parallax error.
The lower panel places the largest reference differences alongside both methods' intervals, retaining full source IDs so each comparison can be traced back to its measurements.

For this nearby-star sample, the point estimates are close in relative terms, but the intervals reveal how that agreement compares with each estimate's precision.
The GSP-Phot intervals can be substantially wider than the propagated parallax intervals because the methods use different assumptions and information.
Their shared use of parallax also matters when interpreting agreement: neither set of estimates provides independent ground truth for the other. {{< /detail >}}

The figure is saved as PNG and SVG in `figures/`.
Alongside these files, DataLad saves a run record in the Git commit: the command that was executed, the declared inputs, and the outputs it produced.
For this figure, the inputs include the interval table, plotting script, and Pixi environment specifications.
The record and Git history together let us identify which versions were used and how they produced the figure.
A collaborator can inspect that evidence to understand a reported result, or use the record to repeat the computation.

{{< detail title="What the environments share" >}} All three environments include Python, Requests, Git, DataLad, and git-annex from the project's base declarations.
These are the shared tools used to acquire data and record computations.
Here are those declarations:

{{< file-code path="examples/gaia-pixi/pyproject.toml" section="project" lang="toml" >}} {{< file-code path="examples/gaia-pixi/pyproject.toml" section="tool.pixi.dependencies" lang="toml" >}} {{< file-code path="examples/gaia-pixi/pyproject.toml" section="tool.pixi.pypi-dependencies" lang="toml" >}}

The `analysis` environment adds NumPy and SciPy; `plotting` adds NumPy and Matplotlib.
The empty `features = []` list for `default` means it adds no named features to that shared base.
Pixi includes the default feature in each of these environments implicitly.

{{< file-code path="examples/gaia-pixi/pyproject.toml" section="tool.pixi.environments" lang="toml" >}}

Their common solve group aligns shared package versions, and cached packages can be reused when preparing another environment.
This lets us share the tools used throughout the project while installing the additional libraries needed for each step.
Changes to shared packages can affect multiple environments, so review the lockfile when updating dependencies.
See [Pixi's environment configuration](https://pixi.prefix.dev/latest/reference/pixi_manifest/#the-environments-table). {{< /detail >}}

{{< step-link step="5" text="Completed research object with the reported figure" >}}

## Reuse and report the work

Let’s inspect the record for the figure we just created.
The latest Git commit contains both a descriptive message and the execution details:

```sh
# pragma: testrun full-build
pixi run git log -1
```

The recorded command names `python code/plot_distances.py`, its input table and destination, and the locked `plotting` environment.
Pixi task names provide convenient entry points; the DataLad history retains the concrete commands and file relationships needed to understand a result. {{< detail title="Embedded records and sidecar files" >}} Our tasks explicitly set `--sidecar no`, so DataLad embeds the full execution record in the commit message alongside its descriptive message and required `[DATALAD RUNCMD]` prefix.
You can also inspect it with `pixi run git show --no-patch HEAD`.
For larger records, `--sidecar yes` stores the structured record in a separate tracked file and leaves a reference in the commit message, which can make the history easier to read. {{< /detail >}}

## Adapt the analysis to a new objective

Suppose a collaborator wants to change the figure's labels or layout.
They edit `code/plot_distances.py`, save that change, and run the figure task against the existing interval table:

```sh
pixi run datalad save -m "style: clarify figure labels" code/plot_distances.py
pixi run figure
```

The new figure record identifies both the revised plotting code and the saved numerical results used to create the figure.
We can revise the presentation without repeating the numerical analysis, and trace each figure to the results it shows.
The scripts remain ordinary Python files that collaborators can read and adapt.

`figure` belongs to the plotting environment, so the task name is enough to select it.
We can also run a command directly when exploring a different output or adapting a step to a new question:

```sh
pixi run --environment plotting python code/plot_distances.py \
  output/distance_intervals.csv figures/exploratory_comparison
```

Here we choose the environment explicitly and pass the script a different output name.
The task gives us a short command for a routine procedure; running the script directly lets us adapt that procedure while using the same environment.
To retain an exploratory run as part of the research object's provenance, wrap its concrete command in `datalad run`, following the input and output declarations shown in the figure task.

Using Pixi and DataLad together gives us flexibility to explore an analysis with different environments, code, or data while retaining a record of what changed.
For example, we could test a newer numerical library against the same observations, or apply the same method to an updated Gaia sample.
[This guide]({{< ref "guides/choosing-what-changes" >}}) explores how to choose what stays fixed during these experiments and how to return to a historical computation.

We can now see the value of working with a STAMPED research object: the original analysis supported this extension, and the work we have produced can itself be reused or extended.
Pixi makes the software and procedures convenient to run; DataLad keeps the resulting computations connected to their inputs and methods.
We want scientific work to be rigorous, transparent, reproducible, and efficient—and easier for others to build on.
STAMPED provides a lens for examining how our tools and practices support these aspirations.

| STAMPED property | Evidence in this research object |
| --- | --- |
| Self-contained | Original analysis, acquired measurements, code, and environment specifications within the project boundary |
| Tracked | Pinned Gaia revision and run records connecting results to versioned inputs and methods |
| Actionable | Pixi tasks for execution and explicit DataLad records for inspection and replay |
| Modular | Reusable original dataset, separate analysis stages, and purpose-specific environments |
| Portable | Locked software specifications for the declared platforms |
| Ephemeral | Reproduction checked in a fresh clone with newly created environments |
| Distributable | Git-tracked tables, scripts, figures, and a public reference to the original dataset |

```sh
# pragma: testrun full-build
# pragma: render hidden
pixi run --environment analysis --locked python -c "import importlib.util; assert importlib.util.find_spec('matplotlib') is None"
pixi run --environment plotting --locked python -c "import importlib.util; assert importlib.util.find_spec('scipy') is None"
pixi run python -c "import subprocess; messages = subprocess.check_output(['git', 'log', '--format=%B', '--grep=DATALAD RUNCMD'], text=True); assert messages.count('\"cmd\":') == 4; assert not __import__('pathlib').Path('.datalad/runinfo').exists()"
source_repo="$PWD"
clone_dir=$(mktemp -d "${TMPDIR:-/tmp}/gaia-extension-reproduce-XXXXXX")
git clone --recurse-submodules "$source_repo" "$clone_dir/project"
(
    cd "$clone_dir/project"
    git config user.name "Demo User"
    git config user.email "demo@example.com"
    completed_revision=$(git rev-parse HEAD)
    preparation=$(git log --format=%H --grep='^build: prepare Gaia extension$' -1)
    pixi run git log --oneline
    pixi run git checkout -b my-analysis "$preparation"
    pixi run git submodule update --init --recursive
    test ! -e raw/gaia_uncertainties.csv
    test ! -e output/distances.csv
    test ! -e figures/distance_comparison.png
    test -z "$(git log --format=%s --grep='DATALAD RUNCMD')"
    # Reuse the recorded response for this offline reproduction check.
    git restore --source="$completed_revision" -- raw/gaia_uncertainties.csv
    pixi run datalad save -m "data: reuse recorded Gaia response" raw/gaia_uncertainties.csv
    pixi run baseline
    pixi run estimate
    pixi run verify
    test ! -d .pixi/envs/plotting
    cmp "$source_repo/output/distance_intervals.csv" output/distance_intervals.csv
    pixi run figure
    cmp "$source_repo/figures/distance_comparison.png" figures/distance_comparison.png
    cmp "$source_repo/figures/distance_comparison.svg" figures/distance_comparison.svg
    pixi run datalad rerun HEAD
    cmp "$source_repo/figures/distance_comparison.svg" figures/distance_comparison.svg
    test -z "$(git -C inputs/gaia status --porcelain)"
)
git clone --recurse-submodules "$source_repo" "$clone_dir/plotting-only"
(
    cd "$clone_dir/plotting-only"
    git config user.name "Demo User"
    git config user.email "demo@example.com"
    pixi run --environment plotting --locked python -c "from pathlib import Path; p = Path('code/plot_distances.py'); p.write_text(p.read_text().replace('From a point estimate to an uncertainty-aware comparison', 'Gaia distances with measurement uncertainty'))"
    pixi run --environment plotting --locked datalad save -m "style: clarify figure title" code/plot_distances.py
    pixi run figure
    test ! -d .pixi/envs/analysis
    test ! -d .pixi/envs/default
    cmp "$source_repo/output/distance_intervals.csv" output/distance_intervals.csv
    if cmp -s "$source_repo/figures/distance_comparison.png" figures/distance_comparison.png; then
        exit 1
    fi
)
rm -rf "$clone_dir"
```
