---
title: "Choosing what stays fixed during an analysis"
description: "Use Pixi and DataLad to vary code, data, or dependencies while retaining a clear basis for comparison."
date: 2026-10-07
state: wip
---

The [Gaia example]({{< ref "examples/pixi-stellar-distance-walkthrough" >}}) ends with a figure, the numerical results behind it, and records of how both were produced.
That research object gives us a starting point for asking new questions.
Would a different implementation change the result?
Would new measurements change our interpretation?
Does using a different numerical library version affect the calculation?

Each question calls for a different comparison.
We can make those comparisons easier to interpret by changing one part of the analysis while holding the others constant.
DataLad retains the commands and connects results to versioned inputs; Pixi prepares the software environment specified by the project revision we choose.
Together, they let us reuse the parts of the work that still apply and record the changes we want to investigate.

| Question | Change | Keep fixed | Repeat |
| --- | --- | --- | --- |
| How should we present these results? | Plotting code | Interval table and plotting dependencies | Figure |
| How sensitive are the intervals to measurement error? | One input uncertainty | Analysis code, dependencies, and other measurements | Estimates, then figure |
| Does a library version affect the result? | Dependency selection | Measurements and analysis code | Estimates, then compare |
| Can we recover an earlier result? | Newly installed environment | Saved inputs, code, and dependency selection | Recorded computation |

Before running, decide what you will compare.
For a layout change, inspect the figure and check that the numerical table is unchanged.
For a dependency change, compare numerical results using a tolerance appropriate to the scientific question.
A command completing successfully tells us that it ran; assessing its output tells us whether the change matters.

## Start from the completed Gaia analysis

Continue in the completed project from the walkthrough, with any edits saved.
If you need a fresh copy, clone the completed analysis branch:

```sh
pixi exec --spec git -- git clone --recurse-submodules \
  --branch examples/pixi-stellar-distance-walkthrough/full-build/analysis \
  https://github.com/stamped-principles/stamped-examples.git gaia-comparisons
cd gaia-comparisons
```

Keep a local reference to this starting point:

```sh
pixi run git branch comparison-base
pixi run git log --oneline
```

In the log, find the commits for estimating the distance intervals and plotting the figure.
In the commands below, replace `ESTIMATE_RUN` and `FIGURE_RUN` with those commit hashes.
They identify the procedures we will reuse; `comparison-base` identifies the project state against which we will compare results.
Each experiment below starts a separate branch from that same state, so a change from one experiment does not carry into the next.

## Change the code, reuse the results

The walkthrough showed how to revise a figure with `pixi run figure`.
We can also select its recorded command explicitly, which is useful when we want to repeat a particular procedure from the history.

```sh
pixi run git switch -c compare-plot comparison-base
```

Edit the labels or layout in `code/plot_distances.py`, then save the edit and replay the figure command:

```sh
pixi run datalad save -m "style: revise the Gaia figure layout" code/plot_distances.py
pixi run datalad rerun FIGURE_RUN
pixi run git diff comparison-base -- output/distance_intervals.csv
```

An empty diff confirms that the saved interval table has not changed.
The new figure uses that table and the revised plotting code, with the same dependency selection.
We only need the plotting environment and the saved numerical results to do this work.

**Selecting a run commit selects its command; by default, replay uses the current project state.** Here that is exactly what we want: the earlier plotting procedure applied to our revised code.
The new run record connects the resulting figure to that revision.

## Change the inputs, reuse the method

Suppose we want to check how sensitive a distance interval is to the reported parallax error.
Start another experiment from the original comparison point:

```sh
pixi run git switch -c compare-data comparison-base
```

In `raw/gaia_uncertainties.csv`, increase `parallax_error` for one source by 10%, leaving its other fields and all other rows unchanged.
This is a deliberately altered input for a sensitivity check, not a new Gaia measurement.
Save it with a message that makes that distinction explicit, then apply the original calculation:

```sh
pixi run datalad save -m "data: increase one parallax error by 10% for sensitivity analysis" raw/gaia_uncertainties.csv
pixi run datalad rerun ESTIMATE_RUN
pixi run verify
pixi run git diff comparison-base -- output/distance_intervals.csv
pixi run datalad rerun FIGURE_RUN
```

The code and dependency selection remain fixed.
We expect the chosen star's distance bounds to widen while its point estimate and the other stars' estimates remain unchanged.
The output diff lets us check that expectation, and the figure shows the result in context.
The original observations and baseline distances are reused.

The same approach applies to a revised dataset from a collaborator: save the new inputs, identify where they came from, and repeat the affected calculation.
The Gaia extension checks that its uncertainty table covers the original sample and agrees with its parallaxes.
A different sample or revised parallaxes would require extending the earlier stages too; that would be a broader experiment.

Acquiring a new archive response is a separate choice, available through `pixi run acquire`.
Reusing a saved response lets us investigate the calculation without changing the measurements at the same time or repeating the query.

## Change the dependencies, reuse the code and data

To investigate a software change, return to the same starting point and select a different SciPy release.
The published Gaia project uses SciPy 1.18.1; here we compare its results with 1.17.1:

```sh
pixi run git switch -c compare-dependencies comparison-base
pixi add --feature analysis "scipy==1.17.1"
pixi run git diff -- pyproject.toml pixi.lock
```

Pixi saves the requested version in the manifest and resolves the packages needed to use it.
Inspect the changes before proceeding: SciPy's requirements and the shared solve group may lead to changes in other packages too.
The experiment tests the resulting dependency selection, so attributing a difference to SciPy alone requires checking what else changed.
To investigate the newest compatible release instead, use [`pixi update scipy`](https://pixi.prefix.dev/latest/reference/cli/pixi/update/).
Check that package versions or builds actually changed: a metadata-only lockfile diff does not establish a different software environment.

Save the chosen environment specification and repeat the numerical calculation:

```sh
pixi run datalad save -m "build: compare numerical results with SciPy 1.17.1" pyproject.toml pixi.lock
pixi run datalad rerun ESTIMATE_RUN
pixi run verify
pixi run git diff comparison-base -- output/distance_intervals.csv output/distance_summary.json
```

The recorded command launches Pixi with the `analysis` environment, so it uses the dependency selection now saved on this branch.
The observations and calculation script are unchanged.
The verification task checks the method and reproduces the newly saved results; the final diff compares those results with the original analysis.
Agreement is useful evidence that this dependency change preserves the tested calculation, while a difference gives us something specific to investigate.

Pixi can reuse downloaded packages when preparing environments, and DataLad lets us repeat the numerical step using the saved measurements.
We can therefore explore a software change without reacquiring data or rebuilding the figure at every iteration.

## Return to an earlier result

The preceding experiments apply a recorded procedure to a changed project.
Recovering an earlier result means selecting its saved inputs, code, and environment specification together.
Use a separate clone so that this reconstruction has its own installed environments and leaves your experimental branches available.

In that clone, select the original figure run and initialize its pinned input dataset before launching the replay:

```sh
pixi exec --spec git -- git switch --detach FIGURE_RUN
pixi exec --spec git -- git submodule update --init --recursive
pixi run datalad rerun --onto= --branch recover-figure FIGURE_RUN
pixi run git diff FIGURE_RUN -- figures/
```

For this single run, `--onto=` starts from the parent of the figure commit, where its input table, code, and environment specifications were already saved.
DataLad repeats the plotting command on a new branch.
An empty diff means that the regenerated figure files match the recorded files byte for byte.
The Gaia walkthrough checks this on the same platform; comparisons across platforms may need a different criterion.

{{< detail title="Why the environment is selected inside the recorded command" >}} The Gaia records include `pixi run --environment plotting --locked -- python code/plot_distances.py ...` rather than relying only on the environment that launched DataLad.
When DataLad selects the state to replay, that inner Pixi invocation reads the manifest and lockfile from the selected state before running the script.
`--locked` requires those two files to agree.
A Python process that was already running would not change its installed dependencies just because Git checked out another revision.

This recipe recovers one figure run whose inputs were saved beforehand.
Replaying a sequence can also involve intermediate code changes and subdatasets; DataLad's `--onto` option does not itself restore subdataset checkouts.
See the [DataLad rerun reference](https://docs.datalad.org/en/stable/generated/man/datalad-rerun.html) for selecting ranges and alternative starting points.
Recreating an environment also requires a compatible host and access to the selected packages. {{< /detail >}}

The useful outcome is a comparison we can explain: what changed, what stayed fixed, and what happened to the result.
With those choices retained in the research object, a collaborator can examine our reasoning, repeat the comparison, or use one of its branches as the starting point for further work.
