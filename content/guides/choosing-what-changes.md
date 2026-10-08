---
title: "Choosing what stays fixed during replay"
description: "Use Pixi and DataLad to explore changes to data, code, and environments."
date: 2026-10-07
state: wip
---

Repeating a computation can serve several purposes: continuing an exploration, testing a change, or recovering a published result.
The useful first question is what should stay fixed.
Data, code, and the execution environment are separate choices.

| Purpose | Data | Code | Environment | STAMPED emphasis and practical priority |
|---|---|---|---|---|
| Continue exploring | Selected inputs | Working version | Current environment | Actionability: quick feedback |
| Explore a data change | New snapshot | Fixed | Fixed | Tracking and Modularity: interpret the effect of changed inputs |
| Explore a code change | Fixed | Revised | Fixed | Tracking and Actionability: inspect the effect of a revised procedure |
| Explore dependencies | Fixed | Fixed | Revised selection | Tracking and Portability: assess compatibility or changed behavior |
| Rebuild the environment | Fixed | Fixed | Recreated from requirements | Ephemerality: replace installed tools conveniently |
| Recover a recorded result | Recorded snapshot | Recorded revision | Retained package selection | Tracking and Actionability: reconstruct an identified computation |

These are emphases, not compliance scores.
STAMPED provides a vocabulary for choosing an appropriate position on each principle's spectrum.
A short exploratory cycle and a carefully retained result can justify different amounts of tracking.

## Apply a recorded command to a changed project

Suppose a Pixi task records a calculation using this pattern:

```text
Pixi task → datalad run [inputs and outputs] -- python code/analyze.py ...
```

The script performs the analysis; the task supplies its environment and provenance recording.
Save the scripts, data, and environment specification before recording the run.
Declare them as DataLad inputs and identify the resulting run commit as `RUN_REV`.

After saving a change to the code or data, replay that command on the current project state:

```bash
pixi run --locked -- datalad rerun RUN_REV
```

Selecting a past command does not automatically select its past inputs or environment.
This invocation uses the current checkout.
To explore dependencies instead, deliberately update the manifest and lock, save them, and replay with the same code and data.
Changing one component at a time helps interpret differences in the result.

## Recover a historical computation

For a single recorded run with a retained lock, work in a separate clone and select the saved revision before launching Pixi:

```bash
git switch --detach RUN_REV
pixi run --locked -- datalad rerun --onto= --branch historical-replay RUN_REV
```

The empty `--onto=` starts at the parent of the first selected run commit; `--branch` gives the replay a new branch.
This assumes the required code, data, manifest, and lock were saved before that run.
An explicit `--onto BASE_REV` instead applies the command starting from a chosen saved state, such as a revised data snapshot.
These examples select one run; replaying a range requires choosing the range with `--since`.
See the [DataLad rerun reference](https://docs.datalad.org/en/stable/generated/man/datalad-rerun.html).

There is one environment tradeoff worth understanding.
The outer Pixi invocation selects its environment before DataLad changes the checkout.
Restoring an older lock during replay does not itself change the active Python environment.
Selecting the historical checkout first makes the direct-command pattern convenient for this single-run case.

Alternatively, a task can record the environment launcher with the explicit calculation:

```text
Pixi task → datalad run [inputs and outputs] -- pixi run --locked -- python code/analyze.py ...
```

Here Pixi selects the environment after DataLad restores the project state.
That makes environment selection part of the replayable command, at the cost of requiring Pixi during replay.
Keep the analytical command explicit; recording a named task can hide changing behavior or invoke provenance recording again.
