# Pixi, environment history, and replay in a STAMPED analysis

Discussion draft, October 7, 2026.
This document records the direction for the [Pixi stellar-distance walkthrough](../content/examples/pixi-stellar-distance-walkthrough.md) and develops questions for discussion before revising its presentation.
The replay patterns below were exercised in a small disposable calculation; the validation section records the results and scope.

## Purpose and scope

The stellar-distance example supplies a well-crafted analysis and an established explanation of STAMPED.
We use that foundation to show how Pixi makes STAMPED practices convenient and approachable.
The scientific calculation, sample selection, reference comparison, and acceptance threshold remain those of the original example.
We expect comparable results and do not reopen its analytical choices.

The story follows a researcher who needs tools, executable procedures, and an environment they can use again or replace.
Pixi's value emerges through those activities: providing Python and command-line dependencies, associating tasks with an environment, and retaining a resolved package selection when that matters.
The original walkthrough is the source of the analysis and teaching material, rather than a competitor against which to score the adaptation.

## Agreed direction for the example

- Introduce basic environment management alongside Git and DataLad early in the walkthrough
- Install git-annex through its Python wheel and declare glibc 2.34 as the minimum for the Linux environment
- Track the manifest first; introduce tracking the lockfile in section 8 when discussing levels of environment reproducibility
- Use task dependencies and input/output declarations for incremental execution, retaining downloaded data across ordinary runs
- Put DataLad recording at the task or invocation layer; keep analytical scripts independent of DataLad
- Use `.pixi/` as the concrete disposable environment, analogous to `.venv/` in the original
- Keep `pixi exec` available where it simplifies a real bootstrap step, without making it a required feature demonstration
- Mention multiple environments, embedded script environments, and containers as directions for further work

The lockfile will still be generated and used locally before section 8.
Omitting it initially means omitting it from the tracked research object and postponing its explanation.
Manifest constraints may be broad, bounded, or exact; we should show the constraints actually written by the chosen commands.
We should not describe all manifest declarations as unpinned if some contain version bounds.

## Three principles answer different questions

**Actionability (A): What procedure can we execute?** The scripts define analytical operations, Pixi tasks organize their invocation, and a DataLad run record retains an executable command.
These support useful work even when the environment is described with broad dependency constraints.

**Tracking (T): What choices and executions can we identify later?** Code revisions, retained data, commands, and environment specifications provide different parts of the answer.
A tracked manifest records dependency requirements.
A retained lock adds the resolved selection for the declared environments and platforms.
The useful amount of history depends on whether we are exploring, sharing a result, or trying to reconstruct a particular past computation.

**Ephemerality (E): What can we discard and recreate?** The `.pixi/` directory is a working environment that can be replaced from a specification.
That is a useful separation between the durable research object and the installed tools used to work on it.
The fresh-clone exercise provides a natural occasion to demonstrate replacement, just as rebuilding `.venv/` does in the original example.

These principles support different goals without imposing one universal workflow.
Recreating an environment from a broad specification is useful for continued development and testing compatibility.
Recreating a retained package selection is useful when recovering a published result.
Both can use disposable environments and executable procedures, while retaining different amounts of environment history.

## Choose what is fixed before interpreting a rerun

Data, code, and environment can each remain fixed or change.
The following cases give those choices a practical purpose:

| Purpose | Data | Code | Environment | Value of the run |
|---|---|---|---|---|
| Continue local exploration | Retained inputs | Current working version | Existing local environment | Short feedback cycle |
| Rebuild the working environment | Retained inputs | Same saved code | Fresh environment from current requirements | Check that setup remains executable |
| Recover a recorded result | Recorded input snapshot | Recorded code | Retained lock, selected platform, and stated host requirements | Reconstruct a particular computation |
| Assess an environment change | Same retained inputs | Same saved code | Deliberately changed dependency selection | Identify consequences of an environment change |
| Develop the analysis | Same retained inputs | Deliberately changed code | Hold the dependency selection fixed where useful | Attribute differences to code changes |
| Analyze another data snapshot | Deliberately changed inputs | Same saved code | Hold the dependency selection fixed where useful | Apply an established procedure to another input |

The latter cases are contexts for interpreting the tools, not extra exercises we must add to the stellar-distance walkthrough.
In particular, a dependency-upgrade exercise is unnecessary for teaching this analysis.

Repeating acquisition is another distinct operation.
A stored Gaia response gives an identified input to the computation.
Repeating its query asks an external service for a response again.
Ordinary analysis and verification tasks should reuse their selected local data, including reference data once obtained.
Refreshing either source should be an explicit choice.
This changes acquisition organization while preserving the scientific calculation and comparison.

## Where the provenance boundary belongs

The preferred main pattern is:

```text
Pixi task
  -> datalad run [declared inputs and outputs] -- python code/compute_distances.py ...
```

The task provides the environment and records the explicit analytical command.
The script performs the calculation without knowing that DataLad exists.
This keeps the same script useful for direct execution, development, and other workflows.

The alternative under consideration is:

```text
DataLad run
  -> pixi run --locked -- python code/compute_distances.py ...
```

Here, the recorded command includes the environment launcher and an explicit executable with its arguments.
It does not invoke a named Pixi task.

The pattern we will avoid is:

```text
datalad run ... pixi run compute
```

Recording a task name hides the analytical command behind a task definition that can change.
If that task also records provenance, replay can introduce nested recording.
Keeping the analytical command explicit makes the record easier to inspect and reuse.

| Pattern | What the record carries | What replay must arrange |
|---|---|---|
| Task contains DataLad and an explicit analytical command | Executable, arguments, declared inputs and outputs | Select and activate the intended environment before replay |
| DataLad records Pixi launching an explicit analytical command | Those details plus the environment-launch instruction | Restore the intended manifest and lock before that instruction runs |

The first pattern is the clearest default for the walkthrough.
The second may be helpful when the environment-launch step needs to travel with each individual run record, or when a sequence uses different environments.
Even the second pattern needs an identified historical specification: `--locked` refers to the lock available to the invocation, not automatically to an earlier lock.

For retained results, save the selected code and environment specification before recording the computation.
Declare the relevant manifest and, when retained, lock as inputs alongside the script and data.
That ties the result to a versioned specification without putting environment reconstruction logic inside the analytical script.

## Using the intended environment during DataLad replay

DataLad selects recorded commands from a revision or range.
By default it executes on the current HEAD; selecting an old run does not by itself restore that run's historical project state.
Its `--onto` option selects a different starting state, and a plain `datalad rerun` does not replay all history.
These distinctions should inform the eventual replay instructions.
See the [DataLad rerun reference](https://docs.datalad.org/en/stable/generated/man/datalad-rerun.html).

For continued work, save the changed data, code, or dependency specification and replay the recorded command on the current state:

```bash
pixi run --locked -- datalad rerun RUN_REV
```

`RUN_REV` identifies the recorded computation.
In the fixture, changing data changed the answer from 6 to 15; changing code changed it from 6 to 8; changing the dependency selection used the newly selected package version.
These were separate changes, each starting from the same baseline.

For historical replay of a single run using the preferred direct-command pattern, use a separate checkout and select its environment before starting DataLad:

```bash
git switch --detach RUN_REV
pixi run --locked -- datalad rerun --onto= --branch historical-replay RUN_REV
```

Here `RUN_REV` is a saved run whose code, data, manifest, and lock were committed before execution.
The empty value in `--onto=` starts replay at the parent of the first selected run commit.
`--branch` puts the replay on a new branch.
Selecting the saved revision before launching Pixi ensures the initial environment agrees with that historical specification.
This worked both in an existing checkout and in a fresh clone with no `.pixi/` directory.

An explicit base supports applying a recorded procedure to another saved state:

```bash
pixi run --locked -- datalad rerun --onto DATA_REV --branch revised-data RUN_REV
```

In the tested case, `DATA_REV` changed only the input data and retained the baseline code and environment specification.
The replay used the changed input and produced 15.
If the base also changes dependencies, select that specification before launching the direct-command replay.

The ordering matters.
`pixi run --locked -- datalad rerun ...` chooses its environment before DataLad performs its checkout.
Our historical replay from a newer environment restored the old manifest and lock but the directly recorded Python command still imported the newer package.
`--onto` selects the starting project state; it does not activate an environment.

The alternative recording pattern can address this within each recorded invocation:

```text
Pixi task
  -> datalad run [inputs and outputs] -- pixi run --locked -- python code/compute_distances.py ...
```

In the same experiment, the inner Pixi invocation read the restored historical specification and selected the old package version successfully.
This remains an explicit analytical command, with no named task or nested DataLad recording inside it.
It is a useful option when automatic environment selection after checkout matters.
The direct-command pattern remains a convenient default when we select the checkout and environment together.

These recipes select one recorded run.
A history crossing several environment revisions needs a separate exercise with the intended `--since` range and replay ordering before we promise the same behavior throughout that sequence.

## What we actually exercised

The retained [validation script](../scripts/check_pixi_datalad_replay.py) creates a disposable Git project, installs dependencies through Pixi, records a small calculation through DataLad, and checks the output of each replay.
The calculation multiplies an input number by a constant in the source and reports the installed `packaging` version alongside the answer.
Reporting that version makes an environment change visible even when the numerical answer stays the same.

All 15 checks passed on macOS ARM with Pixi 0.81.0, DataLad 1.7.1, and Python 3.12.15.
The baseline uses input 2, multiplier 3, and `packaging` 24.2.

| Case | Direct Python record | Explicit Pixi launcher record |
|---|---|---|
| Baseline | 6; package 24.2 | 6; package 24.2 |
| Changed data at HEAD | 15; package 24.2 | 15; package 24.2 |
| Changed code at HEAD | 8; package 24.2 | 8; package 24.2 |
| Changed dependencies at HEAD | 6; package 25.0 | 6; package 25.0 |
| Historical `--onto=` launched from newer environment | 6; package **25.0** | 6; package **24.2** |
| Historical `--onto=` after selecting saved checkout/environment | 6; package 24.2 | 6; package 24.2 |
| Explicit `--onto DATA_REV` | 15; package 24.2 | 15; package 24.2 |
| Fresh clone, saved checkout, historical `--onto=` | 6; package 24.2 | Not exercised |

The historical direct-command case deliberately checks the observed environment mismatch; passing that check does not mean it recovered the old environment.
The script writes a local JSON summary containing expected and actual results, manifest and lock hashes, revisions, and tool versions.
Execution logs and disposable repositories are retained outside the example repository.

This validates replay mechanics with local Git-tracked inputs and a retained lock.
It does not exercise Gaia acquisition, the stellar calculation, annex retrieval, Linux provisioning, task caching, or replay across a range of environment revisions.
The walkthrough's scientific choices remain unchanged.

“Exact environment” should mean the recorded package selection for a specified platform within the declared host requirements.
It does not imply that macOS and Linux use identical binaries.
Pixi's multi-platform support is valuable precisely because one specification can describe appropriate package selections for each supported platform.

## How much environment history is worth keeping?

Section 8 should present a choice with costs and benefits.

| Retained information | Useful for | Tradeoff |
|---|---|---|
| Manifest with broad constraints | Early work and continued development | Future solves can select different versions |
| Manifest with tighter direct dependency constraints | Bounding important software choices | Transitive dependencies can still vary |
| Manifest and lock at a meaningful checkpoint | Sharing or recovering a particular result | Lock changes add review noise and require deliberate maintenance |
| Manifest and lock through ongoing development | Projects needing continuous environment history | More frequent environment diffs and review work |

For this example, the proposed choice is to retain a lock at the point where we want to share or reproduce a result with a particular dependency selection.
We should not recommend tracking every exploratory lock change as the default for every project.
Nor should we imply that a manifest alone records the complete environment that produced an earlier result.

Pixi normally reuses a satisfactory local lock.
It can update that lock when the manifest and lock no longer agree; it does not necessarily resolve afresh on every ordinary run.
`--locked` makes such disagreement an error instead of allowing an automatic lock update.
The practical burden is preserving and selecting the intended specification and using locked execution when stability matters.
See the [Pixi lockfile documentation](https://pixi.prefix.dev/latest/workspace/lock_file/).

Lockfiles can contain noisy changes across transitive dependencies, environments, and platforms.
That cost should sit beside the benefit of retaining a concrete selection.
The multi-platform entries also provide a natural point to explain conda-forge's platform-specific packages and binaries.

There is a Git detail worth making explicit in our discussion: after a lockfile becomes tracked, adding it to `.gitignore` does not hide subsequent changes.
Selective retention therefore needs a concrete convention.
For the walkthrough, one saved checkpoint followed by locked execution is enough.
For a longer exploratory project, immutable result snapshots or a dedicated checkpoint workflow may be more convenient than maintaining a changing tracked lock in every working revision.
That is a project choice to explain, rather than a new tool we need to build here.

## Consequences for tasks and the walkthrough

Task ordering, incremental execution, and provenance can coexist.
Declare the dependencies needed to compute an output, reuse retained data, and record the explicit command when computation actually occurs.
A cached task is useful for routine work but creates no new computational execution to record.
When demonstrating regeneration or replay, deliberately recompute the selected result rather than accepting a cached output as a new run.

These points suggest the following editorial changes after this discussion:

- Early setup: explain the manifest, environment, and operational dependencies, including the git-annex wheel and Linux glibc requirement
- Task section: show dependencies and reuse of data, with recording around explicit commands
- Section 8: explain increasingly specific dependency descriptions, multi-platform solves, selective lock retention, and locked execution
- Reconstruction section: use the disposable `.pixi/` environment to illustrate a chosen reconstruction goal
- Further directions: distinguish continuing work with changed inputs or code from recovering a historical result

The original analysis remains the vehicle throughout.
We can draw briefly on this document wherever the distinction matters without turning the walkthrough into a general treatise on reproducibility.

## Questions to hone before integrating

1. Is the preferred pattern plus a separate checkout of the intended revision sufficient for the historical replay we want to teach?
2. Should section 8 end with one retained environment checkpoint, with continuous lock tracking described as an optional policy?
3. How much of the data/code/environment table belongs in the example itself, and how much should remain supporting discussion?
