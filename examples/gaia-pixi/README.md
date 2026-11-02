# Preparing the Gaia extension

This directory contains the source for the [Gaia/Pixi walkthrough](../../content/examples/pixi-stellar-distance-walkthrough.md).
`prepare-project.py` assembles a parent dataset with the original Gaia research object at `inputs/gaia/`.
It copies the canonical `pyproject.toml`, `pixi.lock`, scientific scripts, and project README into that dataset.
The baseline task uses the original calculation and observations directly from the pinned submodule.

## Build and check

Commit source changes before preparing a release: the generated `source.json` records the source revision, input hashes, and original Gaia revision.
The preparation script refuses to overwrite its output directory.
For a standalone preparation, initialize `gaia/` and run:

```sh
python3 prepare-project.py --output analysis
```

The resulting project's README describes its tasks and scientific methods.
Preparation supplies code and software specifications; the recorded acquisition task obtains the uncertainty measurements.
The small outputs are tracked in Git using DataLad's no-annex mode, so this project does not need git-annex.

From the documentation repository root, use the shared test entry points:

```sh
tox -e snippets -- content/examples/pixi-stellar-distance-walkthrough.md tests/test_pixi_stellar_verification.py
tox -e hugo
```

The walkthrough test includes live Gaia acquisition, with bounded retries for transient connection and server failures.
Its fresh-clone checks reuse the saved response and test numerical reproduction, plotting, and replay.
Numerical validation allows relative differences up to `1e-9`; the original four-decimal baseline table remains byte-exact.
The lock targets Linux x86-64 and macOS ARM64; resolving a platform's dependencies does not substitute for running tests there.

## Publish checkpoints

The materializer executes the walkthrough and publishes one complete analysis history:

```text
examples/pixi-stellar-distance-walkthrough/full-build/analysis
```

The step map identifies preparation, baseline, acquisition, estimation, and figure commits.
Publish this branch and its `materialize-step-map` notes together.
Readers clone the history and explicitly check out its preparation commit before creating their own results.

Both the GitHub Pages workflow and Netlify's preview build call `scripts/load_example_data` to fetch published checkpoints and export the Hugo data files.
The loader falls back to the upstream repository when a fork lacks those branches or notes.
The clone shortcode fails the build if the preparation checkpoint is still missing.

## Retain and update the original input

`gaia/` pins the original analysis at `3e89ae8df2ecfcab7b1d6effd5405c5f9d189d24`.
The tag `gaia-baseline-3e89ae8` retains this commit even if its materialized branch is regenerated.
Keep such retention tags when publishing a new input pin; a Git submodule records a commit ID but does not ensure that the remote keeps the object reachable.
The submodule requests a shallow clone to reduce download cost.

To review a newer original analysis:

```sh
git -C examples/gaia-pixi/gaia fetch origin examples/stellar-distance-walkthrough/full-build/stellar-distance
git -C examples/gaia-pixi/gaia checkout --detach FETCH_HEAD
```

Test the extension against the updated input, retain the new input commit under a tag, and commit the submodule pointer with any needed adaptations.
Ordinary `git submodule update --init` restores the existing pin.
