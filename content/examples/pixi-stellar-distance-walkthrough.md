---
title: "Reusing the Gaia analysis with Pixi and DataLad"
date: 2026-10-28
description: "Continue the Gaia example with shared task and environment configuration."
summary: "Reuse the completed Gaia project, then explore what to rerun, which environment to select, and what to record with Pixi and DataLad."
tags: ["gaia", "parallax", "walkthrough", "python", "datalad", "pixi"]
stamped_principles: ["S", "T", "A", "M", "P", "E", "D"]
fair_principles: ["R", "A"]
instrumentation_levels: ["workflow"]
aspirations: ["reproducibility", "rigor", "transparency", "efficiency"]
params:
  tools: ["python", "git", "datalad", "pixi"]
  difficulty: "intermediate"
  verified: true
  materialize_stem: "pixi-stellar-distance-walkthrough"
state: wip
---

The [Gaia walkthrough]({{< ref "examples/stellar-distance-walkthrough" >}}) established a documented, automated, and verifiable analysis of nearby stars.
We now reuse that completed project to explore how its execution environment and workflow can evolve together.
The scripts, saved observations, and scientific comparison remain our starting point.

Suppose a collaborator wants to repeat the calculation, use a different sample, or try another Python version.
The Makefile already describes the workflow, and the requirements lock records Python packages.
However, selecting a Python interpreter, preparing its environment, installing command-line tools, and invoking Make are separate instructions to coordinate.
We can automate those instructions too; here we explore a tool that brings **task execution and environment selection into the same project configuration**.

[Pixi](https://pixi.prefix.dev/latest/) manages environments containing Python packages and tools from other ecosystems, and runs named tasks in those environments.
Combined with DataLad's execution records, it lets us express both how to run the analysis and which inputs, outputs, and environment specifications belong to a run.
STAMPED gives us a vocabulary for deciding how much of that context to retain.

## 1. Reuse the completed project

Install [Pixi](https://pixi.prefix.dev/latest/installation/) and Git, then clone the output of the previous walkthrough:

```sh
# pragma: testrun full-build
# pragma: render hidden
#!/bin/sh
# pragma: requires sh git pixi
# pragma: timeout 900
# pragma: materialize stellar-distance
set -eu
cd "$(mktemp -d "${TMPDIR:-/tmp}/stellar-pixi-XXXXXX")"
```

```sh
# pragma: testrun full-build
git clone --single-branch \
  --branch examples/stellar-distance-walkthrough/full-build/stellar-distance \
  https://github.com/stamped-principles/stamped-examples.git stellar-distance
cd stellar-distance
```

This is the published research object produced by Gaia's executable example, including its history.
If you completed that walkthrough locally, you can continue in your existing project instead.

The existing `pyproject.toml` already declares `requests` and a compatible Python range.
Keep those declarations and append the following Pixi configuration.
It replaces the Makefile's workflow and also declares Git, curl, DataLad, and git-annex as project dependencies.

```sh
# pragma: testrun full-build
# pragma: render hidden
git config user.name "Demo User"
git config user.email "demo@example.com"
# snippet: configuration
cat >> pyproject.toml <<'TOML'

[tool.pixi.workspace]
channels = ["conda-forge"]
platforms = [
    { platform = "linux-64", glibc = "2.34" },
    { platform = "osx-arm64", macos = "14.0" },
]

[tool.pixi.dependencies]
git = "*"
curl = "*"

[tool.pixi.pypi-dependencies]
datalad = "*"
git-annex = "*"

[tool.pixi.tasks.fetch]
cmd = "test -f raw/gaia_nearby.csv || python code/fetch_data.py raw/gaia_nearby.csv"

[tool.pixi.tasks.compute]
cmd = "python code/compute_distances.py raw/gaia_nearby.csv output/distances.csv"
depends-on = ["fetch"]
inputs = ["raw/gaia_nearby.csv", "code/compute_distances.py", "pyproject.toml", "pixi.lock"]
outputs = ["output/distances.csv"]

[tool.pixi.tasks.all]
depends-on = ["compute"]

[tool.pixi.tasks.clean]
cmd = "rm -f output/distances.csv"

[tool.pixi.tasks.reference]
cmd = "sh test/fetch_reference_distances.sh"
depends-on = ["all"]

[tool.pixi.tasks.test]
cmd = "python test/verify_distances.py"
depends-on = ["reference"]
TOML
# /snippet
# Explicit stdin is portable across GNU and BSD paste.
pixi run python - <<'PY'
from pathlib import Path
p = Path("test/fetch_reference_distances.sh")
p.write_text(p.read_text().replace("paste -sd,)", "paste -sd, -)"))
PY
```

{{< snippet id="configuration" lang="toml" >}}

Pixi reads the Python requirements directly from `[project]`; we do not repeat them in the Pixi sections.
In `test/fetch_reference_distances.sh`, also change `paste -sd,)` to `paste -sd, -)` so the inherited query works with both GNU and BSD paste.
The declared platforms are Linux x86-64 and Apple Silicon macOS.
The OS minimums allow the bundled git-annex wheels to run: glibc 2.34 on Linux and macOS 14 on Apple Silicon.
A separate `pixi.toml` is also supported, but keeping this Python project's configuration together makes the relationship easier to inspect.
See [Pixi's pyproject support](https://pixi.prefix.dev/latest/python/pyproject_toml/).

```sh
# pragma: testrun full-build
pixi install
rm Makefile requirements.txt
printf '\n.pixi/\n' >> .gitignore
pixi run clean
pixi run test
```

Pixi creates `pixi.lock`, installs the selected tools, and runs the task dependencies before verification.
We have reproduced the original workflow using the same analysis scripts and saved observations.
The lockfile records a resolved package selection; the manifest expresses our requirements.
As with the previous requirements lock, these are different levels of specificity, useful for different purposes.

```sh
# pragma: testrun full-build
# pragma: render hidden
# Replace obsolete reproduction instructions while retaining the scientific README.
pixi run python - <<'PY'
from pathlib import Path
p = Path("README.md")
s = p.read_text().replace("make test", "pixi run test").replace("make clean", "pixi run clean")
s = s.replace("make\n", "pixi run all\n")
s = s.replace("pip install -r requirements.txt", "pixi install --locked")
s += "\n## Pixi continuation\n\nInstall Pixi and run `pixi run --locked test`.\n"
p.write_text(s)
PY
# snippet: reproduce
cat > test/reproduce_from_scratch.sh <<'SH'
#!/bin/sh
set -eu
source_repo=$(git rev-parse --show-toplevel)
clone_dir=$(mktemp -d)
trap 'rm -rf "$clone_dir"' EXIT
git clone "$source_repo" "$clone_dir/project"
cd "$clone_dir/project"
pixi run --locked clean
pixi run --locked test
SH
# /snippet
git add pyproject.toml pixi.lock .gitignore Makefile requirements.txt README.md test/
git commit -m "build: express the Gaia workflow with Pixi"
```

Update the README commands to use `pixi run all`, `pixi run test`, and `pixi install --locked`.
Replace `test/reproduce_from_scratch.sh` with this shorter reproducer, then save the configuration, lock, and updated instructions in Git.

{{< detail title="The fresh-clone reproducer" >}} {{< snippet id="reproduce" lang="sh" >}} {{< /detail >}}

A collaborator can use `pixi run --locked test` to require that the manifest and lock agree.
The installed `.pixi/` environment is disposable; its specification travels with the project.

{{< step-link step="1" >}}

## 2. Repeat a calculation and record its context

Repeating work introduces a choice: reuse an unchanged result, or execute the calculation again and record it.
Pixi's `inputs` and `outputs` allow the compute task to skip work when its declared files have not changed.
Including the manifest and lock makes changes to the environment specification relevant to that decision too.
This is a local convenience, not a durable execution record.

DataLad supplies that record.
Replace the compute task's `cmd` with:

```toml
cmd = "datalad run --explicit --sidecar yes -m 'Compute stellar distances' -i raw/gaia_nearby.csv -i code/compute_distances.py -i pyproject.toml -i pixi.lock -o output/distances.csv -- pixi run --environment $PIXI_ENVIRONMENT_NAME --locked -- python code/compute_distances.py raw/gaia_nearby.csv output/distances.csv"
```

```sh
# pragma: testrun full-build
# pragma: render hidden
pixi run python - <<'PY'
from pathlib import Path
p = Path("pyproject.toml")
s = p.read_text()
old = 'cmd = "python code/compute_distances.py raw/gaia_nearby.csv output/distances.csv"'
new = 'cmd = "datalad run --explicit --sidecar yes -m \'Compute stellar distances\' -i raw/gaia_nearby.csv -i code/compute_distances.py -i pyproject.toml -i pixi.lock -o output/distances.csv -- pixi run --environment $PIXI_ENVIRONMENT_NAME --locked -- python code/compute_distances.py raw/gaia_nearby.csv output/distances.csv"'
assert old in s
p.write_text(s.replace(old, new))
PY
pixi install
# Convert the inherited Git repository into a DataLad dataset without annexing files.
pixi run datalad create --force --no-annex .
git add pyproject.toml pixi.lock
git commit -m "feat: record Gaia computation inputs and environment"
```

The outer task expands `PIXI_ENVIRONMENT_NAME`, so DataLad records an explicit environment choice in the command.
The inner Pixi invocation runs the script directly.
`--sidecar yes` saves the execution description in `.datalad/runinfo/`, allowing this first record to be committed even when the calculated CSV is unchanged.
Repeating an identical command and result need not create another commit.

Save this change before running the task so the recorded inputs identify committed versions.
Initialize the existing Git project with `pixi run datalad create --force --no-annex .` if it is not already a DataLad dataset.
Then run:

```sh
# pragma: testrun full-build
pixi run --locked all
pixi run --locked all
```

The first invocation records the calculation; the second can reuse its cached output.
To request a new execution explicitly, run `pixi run clean` followed by `pixi run --locked all`.
DataLad records the command and declared file relationships in Git; Pixi supplies the selected tools and task ordering.
The script itself remains reusable outside either tool.

{{< step-link step="2" >}}

## 3. Change the sample deliberately

The original test retrieves reference distances on every invocation.
That is useful when we want the latest service response, but repeated comparisons then depend on a live service and potentially changing reference data.
For this exploration, retain the reference CSV and fetch it only when explicitly requested.
The patch below gives the `reference` task this command:

```toml
cmd = "test -f test/reference_distances.csv || datalad run --explicit -m 'Fetch Gaia reference distances' -i output/distances.csv -i test/fetch_reference_distances.sh -i pyproject.toml -i pixi.lock -o test/reference_distances.csv -- sh test/fetch_reference_distances.sh"
```

Retaining a reference introduces a responsibility: it must belong to the sample being tested.
We make a small shared-workflow improvement here: fetch all queried source IDs, including rows with no GSP-Phot estimate, and check that those IDs match our computed sample.
Verification reports how many stars have reference distances and applies the existing tolerance to those matched stars.
This improvement is useful with Make too; Pixi simply gives us a convenient place to coordinate it.

{{< detail title="Adjust the inherited reference check" >}} Run this patch against the existing scripts; it preserves the comparison rather than copying a second implementation.

```sh
# pragma: testrun full-build
pixi run python - <<'PY'
# snippet: reference-patch
from pathlib import Path


def replace(path, old, new):
    p = Path(path)
    text = p.read_text()
    assert old in text, f"Expected text missing in {path}; review the Gaia baseline"
    p.write_text(text.replace(old, new))


replace("test/fetch_reference_distances.sh", " AND distance_gspphot IS NOT NULL", "")
replace("test/verify_distances.py", "    reference = {}", "    reference = {}\n    queried = set()")
replace("test/verify_distances.py",
        '            reference[row["source_id"]] = float(row["distance_gspphot"])',
        '            queried.add(row["source_id"])\n'
        '            if row["distance_gspphot"].strip():\n'
        '                reference[row["source_id"]] = float(row["distance_gspphot"])')
replace("test/verify_distances.py", "    if not matched:",
        '    print(f"Computed: {len(computed)}; matched: {len(matched)}; "\n'
        '          f"unmatched: {len(set(computed) - set(reference))}")\n'
        '    if set(computed) != queried:\n'
        '        print("ERROR: reference data were fetched for a different sample. "\n'
        '              "Remove test/reference_distances.csv and run pixi run test again.")\n'
        '        sys.exit(1)\n'
        '    if not matched:')
replace("test/verify_distances.py", "PASSED: all within", "PASSED: all matched stars within")
replace("pyproject.toml", 'cmd = "sh test/fetch_reference_distances.sh"',
        'cmd = "test -f test/reference_distances.csv || datalad run --explicit '
        "-m 'Fetch Gaia reference distances' -i output/distances.csv "
        '-i test/fetch_reference_distances.sh -i pyproject.toml -i pixi.lock '
        '-o test/reference_distances.csv -- sh test/fetch_reference_distances.sh"')
replace(".gitignore", "test/reference_distances.csv", "# Retain reference distances in Git")
# /snippet
PY
```

{{< /detail >}}

```sh
# pragma: testrun full-build
pixi install
git add pyproject.toml pixi.lock test/fetch_reference_distances.sh test/verify_distances.py .gitignore
git commit -m "feat: retain references and check sample coverage"
rm -f test/reference_distances.csv
pixi run --locked test
```

Now narrow the sample to the nearest 50 stars by changing `limit=100` to `limit=50` in `code/fetch_data.py`.
Save the revised script and record the new acquisition:

```sh
# pragma: testrun full-build
# pragma: render hidden
pixi run python - <<'PY'
from pathlib import Path
p = Path("code/fetch_data.py")
s = p.read_text()
assert "limit=100" in s
p.write_text(s.replace("limit=100", "limit=50"))
PY
```

```sh
# pragma: testrun full-build
git add code/fetch_data.py
git commit -m "feat: explore the nearest 50 stars"
pixi run --locked datalad run --explicit \
  -m "Fetch the nearest 50 stars" \
  -i code/fetch_data.py -i pyproject.toml -i pixi.lock \
  -o raw/gaia_nearby.csv -- python code/fetch_data.py raw/gaia_nearby.csv
pixi run --locked all
```

The saved observations changed, so the compute task runs again.
The old reference file still describes 100 stars: verification now rejects it rather than silently comparing only the overlapping IDs.
Refresh it deliberately and verify the new sample:

```sh
# pragma: testrun full-build
# pragma: render hidden
if pixi run --locked test > stale-reference.txt 2>&1; then
    cat stale-reference.txt
    exit 1
fi
grep -q 'different sample' stale-reference.txt
rm stale-reference.txt
```

```sh
# pragma: testrun full-build
rm test/reference_distances.csv
pixi run --locked test
```

We have kept the analysis procedure and environment selection while changing the data.
DataLad's history connects both acquisitions to their computations and reference snapshots.
This is Tracking and Modularity serving a practical question: what changed between these results?
Record the current sample in the README as well:

```sh
# pragma: testrun full-build
printf '\nCurrent sample: the nearest 50 stars selected by code/fetch_data.py.\n' >> README.md
git add README.md
git commit -m "docs: describe the revised Gaia sample"
```

{{< step-link step="3" >}}

## 4. Select another environment for the same task

We can also hold the saved data and code fixed while exploring dependency compatibility.
Append an environment with Python 3.12 to `pyproject.toml`:

```sh
# pragma: testrun full-build
# pragma: render hidden
# snippet: environments
cat >> pyproject.toml <<'TOML'

[tool.pixi.feature.python312.dependencies]
python = "3.12.*"

[tool.pixi.environments]
default = []
python312 = ["python312"]
TOML
# /snippet
```

{{< snippet id="environments" lang="toml" >}}

Both environments inherit the common dependencies and tasks.
The additional feature constrains Python for `python312`; each environment has its own resolved package selection in the same lockfile.
This tests compatibility with that environment as a whole, since selecting another Python can also change compatible dependencies.

```sh
# pragma: testrun full-build
pixi install --environment python312
git add pyproject.toml pixi.lock
git commit -m "build: add a Python 3.12 comparison environment"
pixi run --environment python312 --locked clean
pixi run --environment python312 --locked test
```

We use the same task names, saved observations, reference data, and verification criteria.
Explicitly cleaning requests a fresh calculation for the comparison.
Pixi selects the environment before DataLad records the computation.
The recorded command now names `python312`, while its manifest and lock inputs identify the saved environment specification.
This connects an environment choice to an execution without changing the scientific script.

Dependency declarations, resolved locks, saved data, and execution records each preserve a different part of the context.
Choose their precision to match the question: a quick compatibility check, continued exploration, or recovery of a particular result.
[Choosing what stays fixed during replay]({{< ref "guides/choosing-what-changes" >}}) develops the distinction between applying a recorded command to today's project and restoring a historical computation.
See also [Pixi's environment documentation](https://pixi.prefix.dev/latest/workspace/multi_environment/).

{{< step-link step="4" >}}

```sh
# pragma: testrun full-build
# pragma: render hidden
pixi run --environment python312 python - <<'PY'
from pathlib import Path
from datalad.support.json_py import load_stream
commands = [record["cmd"] for p in Path(".datalad/runinfo").iterdir()
            for record in load_stream(p, compressed=True)]
assert any("--environment default " in cmd for cmd in commands)
assert any("--environment python312 " in cmd for cmd in commands)
PY
```

## Share and recreate the working environment

Commit the project and share it as in the Gaia walkthrough.
A fresh clone can recreate its selected environment and verify the retained sample without querying Gaia:

```sh
pixi run --locked clean
pixi run --locked test
```

```sh
# pragma: testrun full-build
# pragma: render hidden
sh test/reproduce_from_scratch.sh
```

The continuation keeps Gaia's scripts and scientific argument while adding a common place to select tools and execute the workflow.
Pixi makes those instructions actionable and the installed environment replaceable; DataLad connects recorded executions to versioned inputs and outputs.
Together, they let us put STAMPED choices into practice as the analysis evolves.
