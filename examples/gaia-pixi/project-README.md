# Gaia distances: a STAMPED research object

This project extends the original Gaia parallax analysis with uncertainty intervals and a figure comparing the estimates with Gaia DR3 GSP-Phot.
The original project, including its code, observations, results, and history, is pinned at `inputs/gaia/`.
Our Pixi configuration runs that original calculation and the extension in recorded environments.

Install Pixi and initialize the input dataset if your clone did not include submodules:

```sh
pixi exec --spec git -- git submodule update --init --recursive
```

The `starter` branch contains the prepared project before any extension tasks have run.
Run the original calculation, acquire the additional measurements, and produce the new results:

```sh
pixi run baseline
pixi run acquire
pixi run estimate
pixi run verify
pixi run figure
```

Pixi prepares the environment for each step from `pyproject.toml` and `pixi.lock`.
The `baseline`, `estimate`, and `figure` tasks record their explicit Python commands and file dependencies with DataLad.
Configure your Git name and email before recording new work.
The small tables and figures are tracked directly in Git; this example uses DataLad's no-annex mode.

The completed `analysis` branch includes the recorded response in `raw/gaia_uncertainties.csv` and the resulting tables and figure.
When reproducing those saved results, omit `acquire` and use the included response.
Running `acquire` again queries Gaia DR3 and records a new response for the original source IDs.

DataLad embeds each execution record in its commit message (`--sidecar no`).
Use `--sidecar yes` if you prefer a separate tracked record file and a shorter commit message.

## Methods and artifacts

The original estimate is `1000 / parallax` parsecs for parallax in milliarcseconds.
`code/estimate_distances.py` transforms a central 68% Gaussian parallax confidence interval into distance bounds.
The interval includes random measurement error; the model retains uncorrected parallaxes and omits zero-point systematics and distance priors.
GSP-Phot also uses parallax, so the comparison describes agreement between related estimates rather than validation against independent ground truth.

- `output/distances.csv`: original calculation, rerun using the pinned source code.
- `output/distance_intervals.csv`: propagated intervals and Gaia comparison fields.
- `output/distance_summary.json`: sample counts and largest reference differences.
- `figures/distance_comparison.{png,svg}`: reported figure from the interval table.
- Git commit messages: full execution records linking artifacts to inputs, scripts, and environment specifications.
- `source.json`: preparation provenance and exact original Gaia revision.

Use `pixi run git log` to locate run commits and `pixi run datalad --output-format json_pp rerun --report COMMIT` to inspect a record.
Use `pixi run datalad rerun COMMIT` to replay its explicit command with the current checkout.
For a historical computation, first restore the desired project revision and initialize its pinned subdatasets in a separate clone.
Report the project commit together with the table or figure used in your scientific report.

The manifest targets Linux x86-64 (glibc 2.34+) and macOS ARM64 (macOS 14+).
Pixi and access to package registries are required to create environments.
