---
title: "Git Submodules for Modular Dataset Composition"
date: 2026-02-19
description: "Using git submodules to compose independent datasets into modular research objects"
summary: "Demonstrates how git submodules enable independent versioning and composition of dataset components."
tags: ["git", "submodules", "dataset-organization"]
stamped_principles: ["M", "T"]
fair_principles: ["I", "R"]
instrumentation_levels: ["tool"]
aspirations: ["reproducibility", "rigor"]
params:
  tools: ["git"]
  difficulty: "beginner"
  verified: false
state: uncurated-ai
---

## The problem: monolithic datasets resist reuse

Research projects rarely work with a single, self-contained blob of data.
A typical neuroimaging study might use a standard brain atlas maintained by
one group, a set of stimuli curated by another, and raw scanner output that
is unique to the study.  When all of this is dumped into a single
repository, several problems emerge:

1. **No independent versioning.** The atlas is at version 2.3, but there is
   no record of that inside the monolithic repo -- just a snapshot of files.
   When the atlas releases version 2.4 you cannot cleanly upgrade.
2. **No reuse across projects.** A colleague running a different study that
   needs the same atlas cannot pull it from your project without manually
   copying files.  Two copies now drift independently.
3. **Bloated history.**  Every project that embeds the atlas carries a full
   copy of its history (or, worse, no history at all).  Cloning becomes
   slow and storage costs multiply.

The root cause is that a flat directory tree conflates *composition*
(assembling components into a project) with *ownership* (maintaining
each component).

## The solution: git submodules separate composition from ownership

Git submodules let you nest one Git repository inside another.  The parent
repository records *which* child repository to include and *at which
commit*, but the child retains its own `.git` directory, its own history,
and its own remote.  This is exactly the separation we need:

- The **parent** (your research project) controls the composition.
- Each **child** (atlas, stimuli, raw data) controls its own content and
  version history.

This maps directly to the YODA principle that the `inputs/` directory of a
dataset should contain independently versioned subdatasets rather than loose
copies of external data.

## Step-by-step walkthrough

### 1. Create the parent project

Start with a fresh repository that will serve as the top-level research
project:

```bash
mkdir my-study && cd my-study
git init
```

Create the YODA-style directory skeleton:

```bash
mkdir -p code inputs outputs
```

Add a minimal README and commit:

```bash
cat > README.md << 'EOF'
# My Study

Research project following YODA conventions.

- `code/`    -- analysis scripts (tracked directly)
- `inputs/`  -- input datasets (git submodules)
- `outputs/` -- results (ephemeral, regenerable)
EOF

git add README.md code inputs outputs
git commit -m "Initialize project skeleton"
```

### 2. Add an external dataset as a submodule

Suppose the brain atlas lives in its own repository on GitHub.  Add it
as a submodule under `inputs/`:

```bash
git submodule add https://github.com/example-org/brain-atlas.git inputs/brain-atlas
```

Git does three things here:

1. Clones `brain-atlas` into `inputs/brain-atlas/`.
2. Creates (or updates) a `.gitmodules` file at the project root recording
   the URL and local path.
3. Stages a special "gitlink" entry that records the exact commit SHA of
   the submodule.

Inspect what changed:

```bash
git status
# On branch main
# Changes to be committed:
#   new file:   .gitmodules
#   new file:   inputs/brain-atlas
```

The `.gitmodules` file looks like this:

```ini
[submodule "inputs/brain-atlas"]
    path = inputs/brain-atlas
    url = https://github.com/example-org/brain-atlas.git
```

Commit the addition:

```bash
git commit -m "Add brain-atlas v2.3 as input submodule"
```

### 3. Add a second submodule

Add a stimulus set the same way:

```bash
git submodule add https://github.com/example-org/visual-stimuli.git inputs/visual-stimuli
git commit -m "Add visual-stimuli as input submodule"
```

### 4. Resulting directory structure

After these steps, the project looks like this:

```
my-study/
  .git/
  .gitmodules
  README.md
  code/
    analyze.py          # tracked directly in the parent
  inputs/
    brain-atlas/        # submodule -> github.com/example-org/brain-atlas @ abc1234
      atlas.nii.gz
      labels.tsv
      README.md
    visual-stimuli/     # submodule -> github.com/example-org/visual-stimuli @ def5678
      stim_001.png
      stim_002.png
      metadata.json
  outputs/
    (empty, will hold results)
```

The key insight: `inputs/brain-atlas/` is a complete Git repository with
its own history.  You can `cd inputs/brain-atlas && git log` to see the
atlas's full commit history, completely independent of the parent project.

### 5. Cloning a project that uses submodules

When a collaborator clones your project, submodule directories will exist
but will be empty by default.  They need one extra step:

```bash
git clone https://github.com/you/my-study.git
cd my-study
git submodule update --init
```

Or, to do both in one command:

```bash
git clone --recurse-submodules https://github.com/you/my-study.git
```

This fetches the parent and then checks out each submodule at the exact
commit recorded by the parent.

### 6. Updating a submodule to a newer version

When the atlas releases version 2.4, you can update the submodule pointer:

```bash
cd inputs/brain-atlas
git fetch
git checkout v2.4       # or: git pull origin main
cd ../..

git add inputs/brain-atlas
git commit -m "Update brain-atlas to v2.4"
```

The parent now records the new commit SHA.  Anyone who runs
`git submodule update` will get the updated atlas.  The old version is
still accessible via the parent's history -- just check out the previous
parent commit and run `git submodule update` again.

## Connection to YODA principles

The YODA layout convention places input data under `inputs/` and analysis
code under `code/`.  Git submodules implement the **Modularity** principle
for the `inputs/` directory:

| YODA directory | Tracked how?                    | Why?                                            |
|----------------|---------------------------------|-------------------------------------------------|
| `code/`        | Directly in the parent repo     | Code is authored by the project team             |
| `inputs/`      | As submodules (or subdatasets)  | Input data is maintained by external parties     |
| `outputs/`     | Ignored or ephemeral            | Results are regenerable from code + inputs       |

This separation means you can:

- **Pin** your analysis to a specific version of each input.
- **Upgrade** an input independently without touching code or other inputs.
- **Share** an input dataset across projects without copying it.
- **Credit** the maintainers of each input by pointing to their repository.

## Limitations and when to prefer DataLad subdatasets

Git submodules are a built-in Git feature and require no additional tools,
which makes them a good starting point.  However, they have limitations
that become significant at scale:

1. **No large-file support.** Git submodules do not change how Git handles
   file content.  If your atlas contains large binary files, each clone
   downloads the full history of those files.  Git-annex or Git LFS is
   needed to manage large data efficiently.

2. **Manual management.** Adding, updating, and removing submodules
   requires several commands and careful attention to `.gitmodules` and
   `.git/config`.  It is easy to leave a project in an inconsistent state.

3. **No partial fetch.**  You cannot easily fetch only a subset of a
   submodule's files.  For large datasets where you only need a slice,
   this is wasteful.

4. **No recursive save/push.**  Each submodule must be committed and
   pushed independently, bottom-up.  In a deeply nested hierarchy this
   becomes tedious.

DataLad subdatasets build on Git submodules but solve these problems by
integrating git-annex for large-file management and providing commands
like `datalad save` (recursive commit across all nesting levels),
`datalad get` (on-demand file retrieval), and `datalad push` (recursive
push).  If your project involves large files or deep nesting, DataLad
subdatasets are the natural next step from plain Git submodules.

## Summary

| Aspect                | Plain Git submodule          | DataLad subdataset          |
|-----------------------|------------------------------|-----------------------------|
| Tooling required      | Git only                     | Git + DataLad (+ git-annex) |
| Large file handling   | None (full clone)            | git-annex (on-demand fetch) |
| Recursive operations  | Manual per submodule         | `datalad save`, `datalad push` |
| Metadata integration  | `.gitmodules` only           | `.datalad/config`, structured metadata |
| Best for              | Small/medium text-heavy repos | Any size, especially large data |

Start with Git submodules if your data is small and your nesting is
shallow.  Graduate to DataLad subdatasets when scale or convenience
demands it.  Either way, the underlying principle is the same: **compose
your project from independently versioned, reusable components**.
