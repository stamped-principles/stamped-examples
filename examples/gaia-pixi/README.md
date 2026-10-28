# Gaia with Pixi

This source bundle pairs a migration script with a pinned Gaia analysis.
The `gaia/` submodule records an exact commit from the published Gaia output branch.
It is the input, not the repository in which the Pixi work happens.

From this directory:

```sh
pixi exec --spec git --spec python --spec tomlkit -- python migrate-gaia-to-pixi.py
cd analysis
pixi run test
```

Continue with the Pixi walkthrough.
`analysis/` has its own Git history, beginning at the pinned Gaia commit.
The script refuses to overwrite an existing output; use `--output another-analysis` for a fresh run.
The baseline submodule is never reset or migrated.

The executable walkthrough generates this derived repository in a temporary directory.
The materializer publishes its commits and step links under `examples/pixi-stellar-distance-walkthrough/full-build/analysis`.
`pixi-source.json` records the source commit, baseline commit, script hash, and whether the source bundle or walkthrough had uncommitted changes.

## Update the tracked Gaia version

From the documentation repository root, deliberately select a new baseline:

```sh
git -C examples/gaia-pixi/gaia fetch origin examples/stellar-distance-walkthrough/full-build/stellar-distance
git -C examples/gaia-pixi/gaia checkout --detach FETCH_HEAD
```

Run the full Pixi walkthrough tests and materialization before committing.
Adjust the migration and expected manifest if needed, then commit them with the new submodule pointer.
Updating upstream alone does not change this example.
Ordinary `git submodule update --init` restores the committed pin; `--remote` is not part of normal execution.
