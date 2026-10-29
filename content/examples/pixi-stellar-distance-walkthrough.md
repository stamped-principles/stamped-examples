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

We have adapted the workflow to [Pixi](https://pixi.prefix.dev/latest/), which keeps the interpreter, command-line tools, libraries, and executable tasks in one project configuration.
Pixi prepares the software environment for the task we choose to run.
DataLad records the actual scientific command and connects its outputs to the data, code, and environment specifications used to produce them.
Together, these tools help us extend the earlier STAMPED research object into one that supports reporting, inspection, and further reuse.

## Reuse the original analysis

Install [Pixi](https://pixi.prefix.dev/latest/installation/) and clone the prepared project:

```sh
pixi exec --spec git -- git clone --recurse-submodules \
  --branch examples/pixi-stellar-distance-walkthrough/full-build/analysis \
  https://github.com/stamped-principles/stamped-examples.git gaia-extension
cd gaia-extension
```

The completed project includes its scripts, locked software specification, acquired measurements, tables, and figure.
Configure your Git name and email before recording your own runs.
The manifest targets Linux x86-64 and macOS ARM64; see the project README for system requirements.
The complete workflow and fresh-clone checks were run on macOS ARM64; the Linux environment has been resolved in the lockfile.

The earlier Gaia research object lives at `inputs/gaia/` as a Git submodule.
It carries the original code, observations, results, and history, and our project records the exact revision used.
Our additional measurements and results belong to the surrounding extension dataset, so another researcher can reuse either the original analysis or this extension.
This follows the [YODA pattern of composing analyses from reusable datasets](https://handbook.datalad.org/en/latest/basics/101-127-yoda.html).

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
```

```sh
# pragma: testrun full-build
pixi run --locked baseline
```

The task executes the original `inputs/gaia/code/compute_distances.py` against its saved observations and writes `output/distances.csv` in our project.
Our verification step checks that the reproduced table agrees exactly with the earlier result.
This is direct reuse of the original code and data, with the execution environment now specified by Pixi.

{{< detail title="The baseline task and the adaptation to Pixi" >}} {{< file-code path="examples/gaia-pixi/pyproject.toml" section="tool.pixi.tasks.baseline" lang="toml" >}}

The original Make targets become named Pixi tasks, and the software specification now includes Python, Git, and DataLad alongside the scientific libraries.
The original computation accepts input and output paths, so we can run it directly from its pinned dataset.
The extension's verification script checks the reproduced table and new intervals; the original reference-comparison procedure remains available in `inputs/gaia/test/`.
The [maintainer preparation recipe](https://github.com/stamped-principles/stamped-examples/tree/main/examples/gaia-pixi) describes how the ready-to-run project is assembled. {{< /detail >}}

{{< step-link step="2" text="Research object after reproducing the baseline" >}}

## Acquire the uncertainty measurements

Gaia reports a standard error for each parallax measurement.
We will use those errors to construct parallax intervals and transform their endpoints into distance bounds, showing the precision of the original estimates under a stated measurement model.
We also retrieve GSP-Phot's reported distance intervals for comparison.

The acquisition script selects the same stars using the original source IDs and queries Gaia DR3 for these additional fields.
Its Pixi task exposes the complete DataLad command:

{{< file-code path="examples/gaia-pixi/pyproject.toml" section="tool.pixi.tasks.acquire" lang="toml" >}}

```sh
# pragma: testrun full-build
pixi run --locked acquire
```

This queries the archive and records its response in `raw/gaia_uncertainties.csv`.
The run record identifies the original sample, fetch script, manifest, and lockfile as inputs, and the response CSV as the output.
Opening the record shows the Python command and its arguments, including the selected Pixi environment.

The completed project already contains the response used for the reported results.
Run `acquire` to make a new acquisition; to reproduce the reported analysis, continue with that saved response.
Recording and sharing the acquired measurements lets collaborators inspect the data underlying a result and choose explicitly when to request a new snapshot.

{{< step-link step="3" text="Research object with the recorded Gaia response" >}}

## Estimate distance uncertainty

We reuse NumPy's numerical operations and SciPy's normal-distribution quantile function to calculate the intervals.
The `analysis` environment declares those libraries, while our short analysis script implements the transformation and verifies that the source IDs and parallaxes match the original observations.

{{< file-code path="examples/gaia-pixi/pyproject.toml" section="tool.pixi.feature.analysis.dependencies" lang="toml" >}}

{{< detail title="The estimate task: explicit command, inputs, and outputs" >}} {{< file-code path="examples/gaia-pixi/pyproject.toml" section="tool.pixi.feature.analysis.tasks.estimate" lang="toml" >}} {{< /detail >}}

```sh
# pragma: testrun full-build
pixi run --environment analysis --locked estimate
pixi run --environment analysis --locked verify
```

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
pixi run --environment plotting --locked figure
```

![Comparison of original inverse-parallax distances, propagated uncertainty intervals, and Gaia GSP-Phot estimates.](/images/examples/gaia-pixi-distance-comparison.png)

Gaia supplies GSP-Phot comparisons for 48 of the 100 stars in this sample.
The largest absolute difference from the inverse-parallax estimate is about 0.27%.
The top-left panel shows these differences; the uncertainty intervals below put their size in context.
The top-right panel shows how interval asymmetry increases with fractional parallax error.
The lower panel places the largest reference differences alongside both methods' intervals, retaining full source IDs so each comparison can be traced back to its measurements.

The figure is saved as PNG and SVG in `figures/`.
Its DataLad record links it to the interval table, plotting script, and environment specifications.
That connection makes the reported figure an inspectable product of the research object.

{{< detail title="Shared tools and selective environments in Pixi" >}} The environments share the common project tools and belong to an explicit solve group.
Pixi resolves shared packages to compatible common versions while installing each environment's selected dependencies.
Cached packages can be reused when preparing another environment.
This combines selective installation with shared infrastructure; see [Pixi's environment configuration](https://pixi.prefix.dev/latest/reference/pixi_manifest/#the-environments-table).

{{< file-code path="examples/gaia-pixi/pyproject.toml" section="tool.pixi.environments" lang="toml" >}}

Changes to shared dependencies can affect more than one environment, so inspect the lockfile diff when updating packages.
For a figure-only revision, keeping the saved interval table fixed makes the scientific input to that revision explicit. {{< /detail >}}

{{< step-link step="5" text="Completed research object with the reported figure" >}}

## Reuse and report the work

Suppose a collaborator wants to change the figure's labels or layout.
They edit `code/plot_distances.py`, save that change, and run the figure task against the existing interval table:

```sh
pixi run datalad save -m "style: clarify figure labels" code/plot_distances.py
pixi run --environment plotting --locked figure
```

The new figure record identifies both the revised plotting code and the saved scientific results it consumes.
This supports efficient figure revision while keeping its relationship to the numerical analysis visible.
The scripts remain ordinary Python files that collaborators can read and adapt.

To inspect the most recent figure record:

```sh
# pragma: testrun full-build
pixi run datalad --output-format json_pp rerun --report HEAD
```

The recorded command names `python code/plot_distances.py`, its input table and destination, and the locked `plotting` environment.
Pixi task names provide convenient entry points; the DataLad history retains the concrete commands and file relationships needed to understand a result.
[Choosing what stays fixed during replay]({{< ref "guides/choosing-what-changes" >}}) explains replay with current inputs and recovery of historical computations.

For a scientific report, share the completed project revision together with the figure or numerical table used.
The project includes the baseline reference, acquired measurements, executable methods, software specification, and recorded results.
A collaborator can check numerical reproduction in a fresh clone and then build the figure from those results.

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
source_repo="$PWD"
clone_dir=$(mktemp -d "${TMPDIR:-/tmp}/gaia-extension-reproduce-XXXXXX")
git clone --recurse-submodules "$source_repo" "$clone_dir/project"
(
    cd "$clone_dir/project"
    git config user.name "Demo User"
    git config user.email "demo@example.com"
    rm output/distances.csv output/distance_intervals.csv output/distance_summary.json
    pixi run --locked baseline
    pixi run --environment analysis --locked estimate
    pixi run --environment analysis --locked verify
    test ! -d .pixi/envs/plotting
    cmp "$source_repo/output/distance_intervals.csv" output/distance_intervals.csv
    pixi run --environment plotting --locked figure
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
    pixi run --environment plotting --locked figure
    test ! -d .pixi/envs/analysis
    test ! -d .pixi/envs/default
    cmp "$source_repo/output/distance_intervals.csv" output/distance_intervals.csv
    if cmp -s "$source_repo/figures/distance_comparison.png" figures/distance_comparison.png; then
        exit 1
    fi
)
rm -rf "$clone_dir"
```
