---
title: "Recomputing Gaia results with Pixi and DataLad"
date: 2026-11-02
description: "Inspect recorded computations, compare deliberate changes, and recover a result using DataLad and Pixi."
summary: "Continue the Gaia examples by choosing which code, data, and software to reuse when recomputing an analysis."
tags: ["gaia", "datalad", "pixi", "recomputation"]
stamped_principles: ["S", "T", "A", "M", "P", "E", "D"]
params:
  tools: ["python", "git", "datalad", "pixi"]
  difficulty: "intermediate"
  verified: true
aliases: ["/guides/choosing-what-changes/"]
---

The [original Gaia example]({{< ref "examples/stellar-distance-walkthrough" >}}) recorded a distance calculation, and the [Pixi extension]({{< ref "examples/pixi-stellar-distance-walkthrough" >}}) added uncertainty estimates and a figure.
We now have both the results and a history of how they were produced.
That history can guide the next computation: we can inspect an earlier procedure, apply it to a deliberate change, or recover the state that produced a reported result.

DataLad's command-line tools make this history useful beyond reading commit messages.
They can describe a recorded run before executing it, repeat its command, and show which files changed.
Pixi prepares the software environment specified by the selected project state.
Together, they let us choose what to reuse while keeping a clear record of what we changed.

| Question | Change | Keep fixed | Recompute |
| --- | --- | --- | --- |
| How should we present these results? | Plotting code | Numerical table and dependencies | Figure |
| How sensitive is an interval to measurement error? | One input uncertainty | Calculation, dependencies, other measurements | Estimates, then figure |
| Does a dependency update affect the result? | Selected packages | Code and measurements | Estimates |
| Can we recover the reported figure? | Freshly installed environment | Recorded inputs, code, and dependency selection | Historical figure run |

For each comparison, choose what you expect to learn before executing it.
A successful command tells us that the procedure completed; comparing its output tells us whether the change matters.

## Start from the completed research object

The commands below start from a fresh copy of the completed Pixi example.
If you are continuing from that example, you can instead use your completed project with all changes saved, and begin at `comparison-base` below.

```sh
# pragma: testrun comparisons
# pragma: render hidden
#!/bin/sh
# pragma: requires sh git pixi python3
# pragma: timeout 900
set -eu
demo_workspace=$(mktemp -d "${TMPDIR:-/tmp}/gaia-recompute-XXXXXX")
cd "$demo_workspace"
```

```sh
# pragma: testrun comparisons
pixi exec --spec git -- git clone --recurse-submodules \
  --branch examples/pixi-stellar-distance-walkthrough/full-build/analysis \
  https://github.com/stamped-principles/stamped-examples.git gaia-comparisons
cd gaia-comparisons
```

The clone command obtains Git through Pixi before a project environment exists.
From here on, commands use the project's own tools through `pixi run`.

```sh
# pragma: testrun comparisons
# pragma: render hidden
git config user.name "Demo User"
git config user.email "demo@example.com"
```

Keep a local branch pointing to this completed state and identify the two computations we will reuse:

```sh
# pragma: testrun comparisons
pixi run git branch comparison-base
pixi run git log --oneline
estimate_run=$(pixi run git log -1 --format=%H --grep='DATALAD RUNCMD.*feat: estimate Gaia distance intervals')
figure_run=$(pixi run git log -1 --format=%H --grep='DATALAD RUNCMD.*feat: plot Gaia distance intervals')
```

`comparison-base` names the state we will compare against.
The two shell variables hold the commit IDs for estimation and plotting.
Each experiment starts a new branch from the same base, keeping changes from one comparison out of the next.

## Inspect before recomputing

DataLad can show the proposed replay without executing it:

```sh
# pragma: testrun comparisons
pixi run datalad status
pixi run datalad --output-format json_pp rerun --report "$estimate_run"
```

The status command identifies unsaved changes that might affect the comparison.
The report identifies the selected run, its command, declared inputs and outputs, and the action DataLad would take.
Here the command launches the numerical script through Pixi's `analysis` environment.
We can check that this is the procedure we intend to reuse before spending time on it.

For a shell script showing the selected commands, DataLad can also write to the terminal:

```sh
# pragma: testrun comparisons
pixi run datalad rerun --script - "$estimate_run"
```

These inspection commands work from the execution records already in the project.
We can use them even when the original task name has changed or we want to review the command independently of the task definition.

## Change the presentation, reuse the numerical results

Start a branch for revising the figure:

```sh
# pragma: testrun comparisons
pixi run git switch -c compare-plot comparison-base
```

Edit a title or label in `code/plot_distances.py`.
The executable version of this example changes the figure title to “Gaia distances with measurement uncertainty”.
Save the edit, then ask DataLad to repeat the earlier plotting command:

```sh
# pragma: testrun comparisons
# pragma: render hidden
pixi run --environment plotting python - <<'PY'
from pathlib import Path
p = Path('code/plot_distances.py')
p.write_text(p.read_text().replace('From a point estimate to an uncertainty-aware comparison',
                                  'Gaia distances with measurement uncertainty'))
PY
```

```sh
# pragma: testrun comparisons
pixi run datalad save -m "style: clarify the Gaia figure title" code/plot_distances.py
pixi run datalad rerun "$figure_run"
pixi run datalad diff --from comparison-base --to HEAD
```

The diff summarizes the changed script and figure files.
The numerical table and the environment specifications remain unchanged.
Only the plotting step needs to run: its saved input table already contains the scientific results.

**Selecting a run commit selects its command; by default, replay applies that command to the current project state.** Here that means using the revised plotting script.
The resulting run record connects the new figure to that revision.

```sh
# pragma: testrun comparisons
# pragma: render hidden
test -z "$(git diff comparison-base -- output/ pixi.lock pyproject.toml)"
test -n "$(git diff comparison-base -- figures/)"
```

## Change one input, reuse the method

Now consider a sensitivity question: what happens to a star's distance interval if its parallax error is 10% larger?
Start again from the completed analysis:

```sh
# pragma: testrun comparisons
pixi run git switch -c compare-data comparison-base
```

In `raw/gaia_uncertainties.csv`, increase `parallax_error` for one source by 10%, leaving all other fields and rows unchanged.
This is a deliberately altered input for a sensitivity check, not a revised Gaia measurement.
The original response remains available at `comparison-base`.

```sh
# pragma: testrun comparisons
# pragma: render hidden
pixi run python - <<'PY'
import csv
from pathlib import Path
p = Path('raw/gaia_uncertainties.csv')
with p.open() as stream:
    reader = csv.DictReader(stream)
    fields, rows = reader.fieldnames, list(reader)
rows[0]['parallax_error'] = str(float(rows[0]['parallax_error']) * 1.1)
with p.open('w', newline='') as stream:
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)
PY
```

Record the purpose of the change and repeat the numerical calculation:

```sh
# pragma: testrun comparisons
pixi run datalad save -m "data: increase one parallax error by 10% for sensitivity analysis" raw/gaia_uncertainties.csv
pixi run datalad rerun "$estimate_run"
pixi run verify
pixi run datalad diff --from comparison-base --to HEAD
```

We expect the chosen star's bounds to widen, while its point estimate and the other stars' results remain unchanged.
DataLad's diff identifies the affected files; inspect the values within the interval table to assess that expectation:

```sh
# pragma: testrun comparisons
pixi run git diff comparison-base -- output/distance_intervals.csv
pixi run datalad rerun "$figure_run"
```

The calculation and dependency selection remain fixed, and the original observations and baseline distances are reused.
The figure now presents the changed intervals using the original plotting code.
The same approach applies to a collaborator's revised input dataset: save it with its source and purpose, then repeat the affected computations.

```sh
# pragma: testrun comparisons
# pragma: render hidden
pixi run --environment analysis python - <<'PY'
import csv
import io
import subprocess
from pathlib import Path
old = {r['source_id']: r for r in csv.DictReader(io.StringIO(subprocess.check_output(
    ['git', 'show', 'comparison-base:output/distance_intervals.csv'], text=True)))}
with Path('output/distance_intervals.csv').open() as stream:
    new = {r['source_id']: r for r in csv.DictReader(stream)}
changed = [sid for sid in old if old[sid] != new[sid]]
assert len(changed) == 1
sid = changed[0]
assert new[sid]['distance_pc'] == old[sid]['distance_pc']
assert float(new[sid]['lower_pc']) < float(old[sid]['lower_pc'])
assert float(new[sid]['upper_pc']) > float(old[sid]['upper_pc'])
PY
test -z "$(git diff comparison-base -- code/ pixi.lock pyproject.toml output/distances.csv)"
```

## Change the software, reuse the code and measurements

Start a third comparison and ask Pixi for a compatible SciPy update:

```sh
# pragma: testrun comparisons
pixi run git switch -c compare-dependencies comparison-base
pixi update scipy
pixi run git diff -- pixi.lock
```

Inspect the selection before interpreting this as a software experiment.
An update may leave package versions and builds unchanged, or alter only lockfile metadata.
If packages do change, SciPy's requirements and the shared solve group may affect other libraries too.
The comparison tests that resulting selection; attributing a numerical difference to one library requires checking what else changed.

Save the environment specification and replay the same numerical command:

```sh
# pragma: testrun comparisons
pixi run datalad save -m "build: record dependency selection for comparison" pixi.lock
pixi run datalad rerun "$estimate_run"
pixi run verify
pixi run datalad diff --from comparison-base --to HEAD
pixi run git diff comparison-base -- output/distance_intervals.csv output/distance_summary.json
```

Pixi prepares the environment from this branch's specification when the recorded command starts.
The observations and numerical script are unchanged.
The verification task checks the method and recomputes the newly saved results; comparing with `comparison-base` answers whether the dependency selection affected the original results.
For a numerical difference, choose a tolerance appropriate to the scientific question before judging its importance.

DataLad may have no new output commit to save when a replay produces identical files.
The saved change to the environment still identifies the proposed comparison, but unchanged output alone does not establish that different packages were installed: check the lockfile selection too.
Pixi can reuse cached packages, and the recorded calculation uses saved measurements, so this experiment needs neither another archive query nor a figure rebuild.

```sh
# pragma: testrun comparisons
# pragma: render hidden
test -z "$(git diff comparison-base -- code/ raw/ inputs/gaia output/distances.csv)"
```

## Recover the reported figure

So far we have applied earlier commands to a changed project.
Recovering a reported result means selecting the saved inputs, code, and environment specification together.
Use a separate clone so this reconstruction has its own environments and leaves the comparison branches available:

```sh
# pragma: testrun comparisons
pixi run git clone --recurse-submodules . ../gaia-recovery
cd ../gaia-recovery
pixi run git switch --detach "$figure_run"
pixi run git submodule update --init --recursive
```

```sh
# pragma: testrun comparisons
# pragma: render hidden
git config user.name "Demo User"
git config user.email "demo@example.com"
```

Ask DataLad to start from the state just before the original figure run, and replay it on a new branch:

```sh
# pragma: testrun comparisons
pixi run datalad rerun --onto= --branch recover-figure "$figure_run"
pixi run datalad diff --from "$figure_run" --to HEAD
```

For this single computation, `--onto=` selects the parent of the figure commit, where its interval table, script, and environment specifications were already saved.
The new branch retains the recovered computation without replacing the original history.
An empty diff confirms that the recovered files match the recorded state.
The executable example checks the figure files byte for byte on the same platform; cross-platform comparisons may require a different criterion.

{{< detail title="How replay selects the environment" >}} The recorded command contains `pixi run --environment plotting --locked -- python code/plot_distances.py ...`.
DataLad selects the project state first; that inner Pixi invocation then reads the selected manifest and lockfile before launching Python.
`--locked` requires those specifications to agree.
A running Python process would not change its installed dependencies merely because Git checked out another revision.

This example replays one figure run whose inputs were already saved.
A range of runs can include intermediate code changes and different subdatasets; `--onto` does not itself restore subdataset checkouts.
See the [DataLad rerun reference](https://docs.datalad.org/en/stable/generated/man/datalad-rerun.html) for selecting ranges and alternative starting points.
Recreating an environment requires a compatible host and access to the selected packages. {{< /detail >}}

```sh
# pragma: testrun comparisons
# pragma: render hidden
test -z "$(git diff "$figure_run" -- figures/)"
test -z "$(git status --porcelain)"
```

The research object's history now supports more than recovery: it provides procedures and comparison points for further analysis.
DataLad makes those procedures inspectable and executable; Pixi makes their software selections practical to recreate.
Keeping the choices together helps a collaborator understand what changed, check the result, and build on the comparison.
