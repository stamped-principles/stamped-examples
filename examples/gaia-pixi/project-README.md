# Gaia distances: a STAMPED research object

This project extends the original Gaia parallax analysis with uncertainty intervals and a figure comparing the estimates with Gaia DR3 GSP-Phot.
The original project, including its code, observations, results, and history, is pinned at `inputs/gaia/`.
Our Pixi configuration runs that original calculation and the extension in recorded environments.

Install Pixi and initialize the input dataset if your clone did not include submodules:

```sh
pixi exec --spec git -- git submodule update --init --recursive
```

Reproduce the original distances and the extension using the saved measurements:

```sh
pixi run baseline
pixi run estimate
pixi run verify
pixi run figure
```

Pixi prepares the environment for each step from `pyproject.toml` and `pixi.lock`.
The `baseline`, `estimate`, and `figure` tasks record their explicit Python commands and file dependencies with DataLad.
Configure your Git name and email before recording new work.
The small tables and figures are tracked directly in Git; this example uses DataLad's no-annex mode.

To query Gaia DR3 again for the original source IDs and record the response:

```sh
pixi run acquire
```

Run this acquisition before estimation when using the prepared checkpoint, which predates the saved response.
The completed project includes the recorded response in `raw/gaia_uncertainties.csv`.
Requerying the archive is a new acquisition; reproducing the reported analysis uses the saved response.

## Methods and artifacts

The original estimate is `1000 / parallax` parsecs for parallax in milliarcseconds.
`code/estimate_distances.py` transforms a central 68% Gaussian parallax confidence interval into distance bounds.
The interval includes random measurement error; the model retains uncorrected parallaxes and omits zero-point systematics and distance priors.
GSP-Phot also uses parallax, so the comparison describes agreement between related estimates rather than validation against independent ground truth.

- `output/distances.csv`: original calculation, rerun using the pinned source code.
- `output/distance_intervals.csv`: propagated intervals and Gaia comparison fields.
- `output/distance_summary.json`: sample counts and largest reference differences.
- `figures/distance_comparison.{png,svg}`: reported figure from the interval table.
- `.datalad/runinfo/` and Git history: execution records linking artifacts to inputs, scripts, and environment specifications.
- `source.json`: preparation provenance and exact original Gaia revision.

Use `pixi run git log` to locate run commits and `pixi run datalad --output-format json_pp rerun --report COMMIT` to inspect a record.
Use `pixi run datalad rerun COMMIT` to replay its explicit command with the current checkout.
For a historical computation, first restore the desired project revision and initialize its pinned subdatasets in a separate clone.
Report the project commit together with the table or figure used in your scientific report.

The manifest targets Linux x86-64 (glibc 2.34+) and macOS ARM64 (macOS 14+).
Pixi and access to package registries are required to create environments.
