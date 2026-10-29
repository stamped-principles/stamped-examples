# Gaia extension with Pixi and DataLad

This source bundle builds a prepared STAMPED research object extending the original Gaia parallax analysis.
Readers clone the materialized project and run its scientific tasks; preparation is a maintainer operation.
The [walkthrough](../../content/examples/pixi-stellar-distance-walkthrough.md) follows baseline reproduction, acquisition of uncertainty measurements, estimation, plotting, and reuse.

## Project boundary and reuse

`gaia/` pins the completed original analysis at an exact commit of the published Gaia output branch.
`prepare-project.py` creates a new parent dataset and includes that original research object at `inputs/gaia/` as a Git submodule.
The original history stays with that input component; new code, acquired measurements, results, and environment specifications belong to the parent.
The generated `.gitmodules` records the public upstream URL, so collaborators can retrieve the input outside the build workspace.

The baseline task runs the original `compute_distances.py` directly against its original observations.
It writes a new table in the parent project, and verification compares that table byte-for-byte with the pinned original result.
The extension matches the same source IDs and parallaxes, propagates random parallax errors, and plots the resulting intervals against Gaia GSP-Phot.

This composition has precedent in the [DataLad Handbook's YODA guidance](https://handbook.datalad.org/en/latest/basics/101-127-yoda.html).
The earlier local Gaia example proposes reusable input subdatasets, and the AWK example includes a raw-data submodule.
The parent extension makes that pattern concrete for a completed analysis.
The review that motivated this design is preserved in commit `2a85067`.

## Prepare and run locally

From this directory, with the Gaia submodule initialized:

```sh
python3 prepare-project.py --output analysis
cd analysis
pixi run datalad create --force --no-annex .
pixi run git add .
pixi run git commit -m "build: prepare Gaia extension"
pixi run --locked baseline
pixi run --locked acquire
pixi run --environment analysis --locked estimate
pixi run --environment analysis --locked verify
pixi run --environment plotting --locked figure
```

Configure Git author identity before committing.
The script refuses to overwrite an existing output; choose another `--output` for a fresh build.
`source.json` records the source revision, dirty-state flag, hashes of the preparation inputs, and exact Gaia revision.
Commit source changes before preparing a release so this record points to retrievable committed source.

The canonical `pyproject.toml` and `pixi.lock` are copied unchanged into the prepared project.
The scientific scripts in `extension/` become `code/` there.
No acquisition output is injected during preparation: `acquire` queries Gaia and records its CSV response with DataLad.
The completed materialized project retains that response for subsequent reproduction.
Tables and figures are small and tracked directly in Git; the dataset uses no-annex mode.

The old Make workflow has been adapted into Pixi tasks around the reusable input component.
The baseline computation is unchanged; the parent verification script checks exact baseline agreement and uncertainty-method validation.
The original reference-comparison scripts remain inspectable in the pinned input dataset.

## Task and provenance contract

| Task | Environment | Recorded computation |
| --- | --- | --- |
| `baseline` | `default` | Original Python script, input observations, output distance table |
| `acquire` | `default` | Fetch script, original source IDs, output Gaia response |
| `estimate` | `analysis` | Estimation script, observations, uncertainties, baseline table, output intervals and summary |
| `figure` | `plotting` | Plotting script, interval table, output PNG and SVG |
| `verify` | `analysis` | Validation only; creates no research artifacts |

Pixi tasks expose their complete `datalad run` commands in the manifest.
Each record names the concrete Python script and arguments, with `pixi run --environment ENV --locked -- python SCRIPT ...` selecting its software environment.
DataLad records scripts, data, manifest, and lockfile as inputs.
Every run explicitly uses `--sidecar no`; DataLad embeds its native record in the commit message.
Descriptive messages retain DataLad's required prefix, with no additional command-copying code.
No run record invokes a named Pixi task or a recording dispatcher.
The walkthrough renders task excerpts from the canonical manifest using the `file-code` shortcode's `section` parameter.

The default tools are shared, with explicit `analysis` and `plotting` features and a shared solve group.
Package updates may change shared resolved dependencies; inspect the lockfile diff.
The platform targets are Linux x86-64 and macOS ARM64.
Fresh-clone tests on the current host validate execution there; resolving the other platform is not an execution test on it.

## Materialization and checks

The executable walkthrough prepares the project, runs each stage, and verifies saved-input reproduction in a fresh clone.
That clone retrieves the original input from its public URL.
The test compares the numerical table and both figure formats and checks that the analysis environment has no Matplotlib and the plotting environment has no SciPy.
Figure SVG metadata uses a fixed hash salt and omits the creation date to make same-environment reproduction comparable.

The materializer publishes the analysis history as one branch:

```text
examples/pixi-stellar-distance-walkthrough/full-build/analysis
```

Readers clone this branch, inspect its history, and explicitly check out the preparation commit on a new local branch before running the tasks.
The same published history contains the starting point and all completed results.
The `gaia-clone` shortcode reads the preparation hash from the existing step map, keeping the checkout instruction synchronized with the published history.
The step map identifies preparation, baseline, acquisition, estimation, and figure commits.
The completed branch includes saved measurements and outputs; earlier checkpoints show their creation.
Publish that branch and its step-map notes with the source when releasing the walkthrough, using the repository's existing materialization workflow.
Until published, new checkpoint links and the revised prepared project are local build artifacts.
For local previews, set `HUGO_PARAMS_GAIAANALYSISURL` to a local clone of the completed analysis.
The `gaia-clone` shortcode then displays a working local clone command; published builds use the public `analysis` branch by default.

Relevant checks from the repository root:

```sh
python -m pytest tests/test_pixi_stellar_verification.py tests/test_materialize.py
python -m pytest content/examples/pixi-stellar-distance-walkthrough.md -p no:datalad
hugo --gc --minify
```

The walkthrough test includes a live Gaia acquisition.
Run saved-input verification separately when diagnosing archive availability versus numerical reproduction.
For a prepared completed project, the saved-input path is `baseline`, `estimate`, `verify`, then `figure`.

## Update the original Gaia component

From the documentation repository root:

```sh
git -C examples/gaia-pixi/gaia fetch origin examples/stellar-distance-walkthrough/full-build/stellar-distance
git -C examples/gaia-pixi/gaia checkout --detach FETCH_HEAD
```

Review the upstream change, rerun the extension checks, and commit the new submodule pointer with any necessary adaptations.
Each release pins an exact revision; checking for newer upstream work is a maintainer action.
Ordinary `git submodule update --init` restores the committed pin.
