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

Continue with the Pixi walkthrough to add a numerical-analysis environment (NumPy and SciPy) and a separate plotting environment (Matplotlib).
The extension propagates random parallax errors into asymmetric distance intervals and plots them against the original estimates and Gaia GSP-Phot.
The acquisition, scientific, and plotting scripts are in `extension/`.
The migration copies them into the derived project, where DataLad records the Gaia query, numerical results, and figure as separate tasks.
The query task reuses its saved CSV when present; the recorded acquisition command can be rerun to refresh it.
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

## Proposed redesign (2026-10-29)

This is a review and implementation plan, not a description of implemented changes.
The instructions above describe the current source bundle.
The intended audience is a researcher running, interpreting, and extending an existing analysis.
The main outcome is a shareable STAMPED research object whose results are connected to data, code, and executable environment specifications.

### What the review found

The walkthrough currently makes project construction its organizing story: migrate a repository, add dependencies, register tasks, and introduce a recording wrapper.
The scientific question arrives after that setup, while the migration has already copied the scientific extension into place.
Readers therefore encounter new code before they know its purpose, and the relationship between the original and extended analyses is difficult to see.
Rewording individual paragraphs will help, but the entry point and sequence need to change.

There are useful foundations to retain:

- The original Gaia analysis is already pinned as a Git submodule.
  Its commit, `3e89ae8df2ecfcab7b1d6effd5405c5f9d189d24`, matched the published baseline branch when checked on 2026-10-29.
- The numerical extension matches the original source IDs and parallaxes and checks the original distance estimates.
- Acquisition, estimation, and plotting already have separate DataLad records.
- Analysis and plotting use separate Pixi environments.
- Existing validation covers the interval calculation and reproduction in a fresh clone.

Some quoted comments refer to an older state: the current version already fetches the extra Gaia measurements through `record.py acquisition`, which invokes `datalad run` around the fetch script.
The migration copies scripts, not a predownloaded uncertainty CSV.
The redesign should preserve recorded acquisition and explain it at the point where the scientific question requires those measurements.

### Precedent and the repository boundary

The existing examples support composition, with different levels of evidence:

- [The original Gaia walkthrough](../../content/examples/stellar-distance-walkthrough.md), under “Modularity via subdatasets,” proposes an independent input dataset shared by multiple analyses.
  It does not implement an extension of a completed analysis as a new parent dataset.
- [The AWK evolution example](../../content/examples/stamped-awk-evolution.md) includes raw data as a submodule and discusses reusable processing environments.
- [The Git submodule example](../../content/examples/git-submodules-modularity.md) describes independently versioned inputs.
  It is marked uncurated and unverified, so it is supporting exposition rather than execution evidence.
- The [DataLad Handbook's YODA guidance](https://handbook.datalad.org/en/latest/basics/101-127-yoda.html) explicitly describes analysis datasets incorporating prior processed datasets, and completed analyses becoming components of a paper.
  Its [worked iris example](https://handbook.datalad.org/en/latest/basics/101-130-yodaproject.html) demonstrates a separate analysis dataset with a pinned input dataset and recorded outputs.

There is therefore precedent for the composition pattern, but no implemented local example found that exactly matches extending a completed Gaia analysis this way.
Also, the current `analysis/` is an independent clone of `gaia/`; it is not registered as a submodule or subdataset of the documentation repository.
Preserving Git ancestry and composing datasets are distinct mechanisms.

**Recommended design:** distribute a ready-to-run extension dataset with the completed Gaia research object included at `inputs/gaia/` as a pinned subdataset.
Keep the original history within that component; record new code, environment specifications, acquisitions, and results in the parent extension dataset.
The source bundle can continue tracking the published baseline for maintainers, but the distributed research object must itself retain the baseline reference.

```text
gaia-extension/
  inputs/gaia/          original research object, pinned Git submodule
  code/                extension, acquisition, plotting, and validation
  raw/                 newly acquired uncertainty measurements
  output/              reproduced baseline and new interval tables
  figures/             reported figures
  pyproject.toml       Pixi tasks and environment declarations
  pixi.lock            resolved software versions
  .datalad/            dataset configuration and run records
```

Suggested explanation for readers:

> We build on the completed Gaia analysis by including it in this project as an input dataset.
> It carries the earlier code, observations, results, and history, and this project records the exact version used.
> Our additional measurements, analysis, and figures are recorded in the surrounding project, so another researcher can reuse either the original analysis or this extension.

The alternative is to retain the current derived clone, prepare it ahead of time, and explain its shared ancestry in two sentences.
That is a smaller implementation change and best fits a literal in-place migration story.
The recommended parent/subdataset design makes the reusable component visible inside the delivered research object, at the cost of adapting paths and the publication process.
This architecture choice remains a proposal for discussion.

“Most recent Gaia example” should mean that maintainers check the published baseline, update its pin deliberately, and validate the extension.
Each released extension must identify an exact baseline revision.

### Proposed reader journey

1. **Start with the scientific question and existing result.** The earlier example estimated distances for 100 nearby stars from their parallaxes.
   Ask how measurement uncertainty changes the precision implied by those estimates, and how the resulting intervals compare with Gaia GSP-Phot estimates.
   Show the original result and preview the figure this extension will produce.

2. **Obtain the prepared research object and repeat the earlier calculation.** Provide one real clone command and one named Pixi task to reproduce the baseline.
   Explain that the workflow has already been adapted to Pixi: the project declares the interpreter, tools, dependencies, and commands together.
   Execute the original `compute_distances.py` against the original observations, writing a new output in the parent dataset and comparing it with the pinned original table.
   This script already accepts input and output paths, making direct code reuse practical.
   The original reference-check script has fixed relative paths; preserve its scientific comparison through an explicit adapter and document that adaptation.
   Put the migration diff and maintainer preparation recipe in an optional detail section.

3. **Acquire the measurements needed for the extension.** Introduce the need for `parallax_error` and the GSP-Phot interval fields before showing the fetch task.
   Select the same stars using the saved source IDs, and show a `datalad run` task that wraps the fetch with declared inputs and output.
   Explain that the resulting CSV and acquisition record become part of the research object.
   The prepared starting checkpoint should allow readers to perform this acquisition; the completed reporting checkpoint should also contain the recorded response for subsequent reuse.
   Identify both checkpoints explicitly so the walkthrough never depends on silently switching repository states.

4. **Estimate uncertainty using established numerical libraries.** Explain: “Gaia reports a standard error for each parallax measurement. We use those errors to construct a parallax interval and transform its endpoints into distance, showing the precision of the original estimate under the stated measurement model.”
   Introduce NumPy and SciPy by their role in the calculation, show the relevant preconfigured dependency/task excerpt, and run the named analysis task.
   Link the analysis code beside its inputs and outputs.
   The current implementation uses SciPy's normal quantile and NumPy operations; our script supplies the scientific transformation and checks.
   Describe that division honestly rather than implying a packaged general distance-inference algorithm.
   Keep the Gaussian model, interval meaning, reciprocal asymmetry, systematics limitation, and GSP-Phot's shared parallax information in a compact methods note.

5. **Create and interpret the figure.** Lead with: “Let's now plot these results. We use a separate plotting environment so that the dependencies for the calculation and figure can be managed separately. Collaborators recreate the environments for the steps they want to run.”
   Show the plotting task and its invocation, followed immediately by the figure and an interpretation grounded in the generated table.
   State positively that the figure consumes the saved interval table.
   Explain shared tools and package reuse in a short optional Pixi note.

6. **Reuse and report the recorded analysis.** Demonstrate a concrete reuse action: revise the figure labels or layout and record a new figure from the same interval table.
   Inspect one real run record linking the reported figure to its table, script, manifest, lock, and selected environment.
   Show reproduction from a fresh clone of the completed research object and a link to the relevant historical replay guidance.
   Close with the exact repository revision and retrievable artifacts that a scientific report would cite.

Use approximately one execution block per scientific stage.
Show the relevant task definition directly beside the command that invokes it; source it from the actual manifest to prevent drift.
Keep environment construction, Git bookkeeping, wrapper internals, and exhaustive validation in linked code or maintainer documentation.

### Execution and provenance contract

Proposed public task names are `baseline`, `acquire`, `estimate`, `figure`, and `verify`.
These names are design targets, not currently executable instructions.
The selected environment should be explicit in each displayed invocation and in each recorded scientific command.
Prefer manifest task definitions exposing `datalad run` over a generic stage dispatcher when the definitions remain readable.
If a small wrapper is retained, show the actual recorded command and inputs in the optional provenance detail.
Avoid nested recording: the DataLad record should invoke a computation task or script, not the task that creates the record.

| Stage | Reused inputs | New artifact and evidence |
| --- | --- | --- |
| Baseline | Original script, observations, and expected distances from the pinned Gaia component | Recomputed table, equality check, and run record |
| Acquisition | Original source IDs, query script, manifest, lock | Gaia response CSV and recorded query execution |
| Estimation | Baseline table, observations, acquired errors, method code, manifest, lock | Interval table, summary, and run record |
| Figure | Interval table, plotting code, manifest, lock | PNG/SVG and run record |
| Reuse | Same saved table, changed plotting code | Revised figure with traceable input identity |

Acquisition should be an explicit operation that queries Gaia and records the response.
Ordinary analysis and figure tasks should consume saved inputs; a missing acquisition should produce a clear instruction or use a separately named preparation task.
Distinguish repeating a query against a live service from reproducing an analysis of the saved response.
This gives saved data a visible scientific origin and a useful lifecycle.

Separate environment declarations permit selective installation and clearer dependency ownership.
Shared default features alone do not guarantee a joint solve or identical resolved versions.
The [Pixi manifest documentation](https://pixi.prefix.dev/latest/reference/pixi_manifest/#the-environments-table) describes explicit solve groups for aligning shared versions.
Evaluate a shared solve group and package-cache reuse in implementation before making claims about reduced solving or downloading.
Also check whether a plotting dependency update changes shared analysis packages: distinct environments do not guarantee independent lockfile evolution.
Declare and test supported platforms; the current manifest covers Linux x86-64 and macOS ARM64, so Windows portability is not yet demonstrated.

### What this demonstrates about STAMPED

| Property | Evidence the reader should encounter |
| --- | --- |
| Self-contained | Baseline component, acquired measurements, code, and environment specifications under the extension's boundary |
| Tracked | Exact upstream revision and DataLad records connecting results to versioned inputs and methods |
| Actionable | Named tasks executing the analysis, plus a concrete replayable record |
| Modular | Reused Gaia component, separate scientific stages, and purpose-specific environments |
| Portable | Locked software specifications and verified execution on declared platforms |
| Ephemeral | Successful reproduction from a fresh clone and newly created environments |
| Distributable | Published parent and subdataset revisions, accessible data, and instructions that work for a collaborator |

Connect these properties to concrete benefits where they arise: reuse of prior scientific work, efficiency when revising a figure, rigor through validation, and transparency through inspectable records.
Treat fresh-environment reproduction as evidence for Ephemerality, consistent with the paper and this site's principle definition.
Use the final table as a concise recap after those benefits have been demonstrated.

### Implementation sequence and acceptance criteria

1. Settle the repository boundary and prepare a baseline-only Pixi checkpoint.
   Retain the exact upstream reference and compare reproduced distances with its saved results.
2. Separate migration/preparation from scientific extension delivery. Adapt scripts to the parent/input layout and provide inspectable tasks with a committed lockfile.
3. Record acquisition, estimation, and plotting as distinct stages.
   Retain the current source-ID/parallax consistency checks and interval validation.
4. Rewrite the walkthrough around the reader journey above.
   Derive configuration excerpts from real files and replace setup-heavy prose with scientific interpretation and artifact links.
5. Adapt executable walkthrough tests and materialization together.
   Ensure published checkpoint links and submodule URLs resolve outside the build workspace; avoid local clone origins in the delivered project.
6. Verify the actual distribution from a fresh clone.
   Check baseline agreement, saved-input numerical reproduction, plotting-only reuse, environment selection in run records, and accessible subdataset commits.
   Exercise live acquisition separately so archive availability is distinguishable from numerical reproducibility.
   Run existing documentation/materialization checks and the declared platform checks before marking the redesigned example verified.

No workflow execution, scientific results, or published page has been changed by this planning review.
Numerical conclusions for the revised narrative must come from the implementation run, rather than being inferred from the existing illustration.
