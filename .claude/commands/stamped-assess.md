---
description: Assess a study, tool, or example against STAMPED and FAIR properties
argument-hint: "<URL, file path, or description of target to assess>"
---

# STAMPED / FAIR Assessment

You are a systematic assessor of research objects against the STAMPED and FAIR
frameworks. Given a target (URL, file path, or description), you perform a
two-phase assessment: first a document-based analysis producing per-property
ratings with justifications, then an offer to perform hands-on validation if
feasible. Your goal is to produce an honest, evidence-based assessment — not to
inflate ratings. Absence of evidence for a property is rated `absent`, not
`partial`.

---

## Phase 1 — Document-based assessment

### Step 1: Identify and retrieve the target

- If the argument is a URL: clone or fetch it (use `gh` for GitHub repos,
  `git clone` for git URLs, `WebFetch` for web pages).
- If the argument is a local path: read it directly.
- If the argument is a description: search for relevant materials, ask the user
  for clarification if needed.

Read README, documentation, pyproject.toml, Makefile, Dockerfile,
environment specs, CI configs, and any metadata files. Understand the
project structure before rating anything.

### Step 2: Assess each STAMPED property

For each property below, walk the checklist, cite specific evidence from the
target, and assign a rating.

#### S — Self-contained

> All essential modules and components reside within a single top-level boundary.

**Requirements:**
- S.1: All components essential to replicate computational execution MUST be
  contained within (or reachable from) a single top-level boundary.

**Checklist:**
- Is there a single top-level directory/repository that gathers everything?
- Are all data files, code, and environment specifications present or
  explicitly referenced (submodules, registered URLs)?
- Does the project depend on implicit external state ("don't look up" rule)?
- Can a user obtain all essential materials starting from one entry point
  (e.g., `git clone --recurse-submodules`)?

**Spectrum:** Minimum — essential files present but some dependencies
undocumented. Ideal — every dependency is either committed or referenced via
content-addressed identifiers; `git clone --recurse-submodules` fetches
everything needed.

---

#### T — Tracked

> Version information and provenance recorded for all components via
> content-addressed version control.

**Requirements:**
- T.1: Version information MUST be recorded for all components.
- T.2: Content-addressed version control SHOULD be used (identical content
  hashes prove identity).
- T.3: Provenance (what actions produced/modified each component, what inputs
  were consumed, what versions of code/environment were involved) SHOULD be
  captured.
- T.4: For code-driven modifications, provenance SHOULD be captured
  programmatically (e.g., `datalad run`), not by manual annotation.

**Checklist:**
- Is the project under version control (git)?
- Are data files versioned (git, git-annex, DVC, etc.)?
- Is provenance recorded for derived outputs (run records, Makefile
  dependency graphs, workflow logs)?
- Are external dependencies pinned to specific versions (commit hashes,
  digests, locked versions)?
- Is provenance machine-readable or only prose?

**Spectrum:** Minimum — git tracks code; data versions are implicit.
Ideal — all components (code, data, environment, containers) are
content-addressed; every derived output has machine-readable provenance
linking it to specific input versions and commands.

---

#### A — Actionable

> Procedures are executable specifications, not just documentation.

**Requirements:**
- A.1: Procedures MUST be executable, not just documented.
- A.2: Actionability is cross-cutting — it applies to every other STAMPED
  dimension (tracking becomes more actionable when recorded commands can be
  re-executed; portability becomes more actionable when environments can be
  instantiated from a specification).

**Checklist:**
- Can a user reproduce results by running commands, not just reading prose?
- Is there a build/run command (`make`, `datalad run`, `snakemake`, etc.)?
- Are instructions executable specifications (Makefile, workflow file) or
  prose README steps?
- Can recorded provenance be re-executed (`datalad rerun`, `make`, etc.)?
- Are setup steps automated or manual?

**Spectrum:** Minimum — README lists commands to run manually. Ideal —
`make` / `datalad run` / workflow engine re-derives all outputs from source;
provenance is re-executable.

---

#### M — Modular

> Components organized as independently versioned modules that can be composed
> and reused.

**Requirements:**
- M.1: Components SHOULD be organized as independently versioned modules.
- M.2: An idiomatic layout SHOULD delineate components into structured
  directories (`code/`, `inputs/`, `envs/`, `results/`).

**Checklist:**
- Is there a clear directory structure separating code, data, environment,
  and outputs?
- Are input datasets independently versioned (submodules, subdatasets)?
- Can individual components be reused in other projects without copying?
- Are there clear boundaries between components (each with its own
  versioning, documentation)?
- Does the layout follow domain conventions (YODA, BIDS, etc.)?

**Spectrum:** Minimum — logical directory separation. Ideal — each component
is an independently versioned unit (git submodule / subdataset) that can be
composed into multiple projects.

---

#### P — Portable

> Procedures do not depend on undocumented host state; environments are
> explicitly specified.

**Requirements:**
- P.1: Procedures MUST be executable on different hosts given documented
  system requirements.
- P.2: Computational environments MUST be explicitly defined, not implicitly
  assumed.
- P.3: Environments SHOULD be machine-reproducible and version controlled
  alongside code and data.

**Checklist:**
- Are system requirements documented?
- Are there hardcoded paths, user-specific assumptions, or OS-specific
  commands?
- Is the computational environment specified (container, lock file,
  environment.yml, requirements.txt)?
- Is the environment specification version-controlled?
- Can the project run on a different machine without undocumented manual
  setup?
- Are environment-sensitive settings (locale, timezone) explicitly set?

**Spectrum:** Minimum — requirements listed in README, no hardcoded paths.
Ideal — container image (pinned by digest) or declarative env manager (Nix,
Guix) captures the full environment; `LC_ALL=C` or equivalent pins
locale-dependent behavior.

---

#### E — Ephemeral

> Results produced in temporary, disposable environments validate that other
> STAMPED properties hold.

**Requirements:**
- E.1: A research object SHOULD be able to produce its results from a fresh
  clone on a system meeting stated requirements.

**Checklist:**
- Can results be produced from a fresh clone (no pre-existing state)?
- Are derived outputs clearly separated from source inputs?
- Can derived files be deleted and regenerated?
- Does CI run the analysis from scratch?
- Are temporary/scratch files properly isolated?

**Spectrum:** Minimum — results reproducible from a fresh clone with manual
steps. Ideal — every computation runs in a disposable environment created
and destroyed per execution; CI validates this automatically.

---

#### D — Distributable

> The research object and all its components are persistently retrievable by
> others.

**Requirements:**
- D.1: The research object and its components MUST be retrievable by others.
- D.2: Components SHOULD be available through persistent, archival
  infrastructure.

**Checklist:**
- Is the project publicly accessible (GitHub, GitLab, institutional repo)?
- Are large data files available through persistent hosting (Zenodo, DANDI,
  Figshare, institutional archive)?
- Are there DOIs or persistent identifiers?
- Is there a clear license?
- Can a third party obtain all components without special access?
- Are container images available from a public registry?

**Spectrum:** Minimum — publicly accessible repository with retrieval
instructions. Ideal — all components archived on persistent infrastructure
with DOIs; container images on public registries; fully self-contained
archive (e.g., zipped RO-Crate) available.

---

### Step 3: Assess each FAIR property

#### F — Findable

- Does the target have a persistent identifier (DOI, handle)?
- Is it registered in searchable resources (data catalogs, registries)?
- Is there rich, structured metadata?

#### A — Accessible

- Is the target retrievable via standard protocols (HTTP, SSH, git)?
- Is authentication/authorization documented if required?
- Is metadata accessible even if data is restricted?

#### I — Interoperable

- Does the target use standard file formats and vocabularies?
- Are there qualified references to other datasets?
- Is metadata in a machine-readable, community-standard format?

#### R — Reusable

- Is there a clear license?
- Is provenance information available?
- Does the data meet domain-relevant community standards?
- Is there enough documentation for a new user to understand and reuse?

### Step 4: Classify instrumentation levels and aspirations

Assign from the project taxonomy:
- `instrumentation_levels`: `data-organization` | `tool` | `workflow` | `pattern`
- `aspirations`: `reproducibility` | `rigor` | `transparency` | `efficiency`

### Step 5: Feasibility assessment for Phase 2

Note what hands-on validation would involve:
- Estimated disk space and download size
- Required tools and container runtimes
- Network access requirements
- Blockers: huge datasets, proprietary tools, HPC requirements, missing
  public access
- Is hands-on validation feasible in this environment?

---

## Phase 2 — Hands-on validation (offered, not automatic)

After completing Phase 1, present:

1. **Resource summary**: disk space, tools needed, estimated time
2. **Blockers**: anything preventing hands-on validation
3. **Offer**: If feasible, ask the user whether to proceed

If the user confirms:
- Clone/fetch the target
- Attempt to build/run following the project's instructions
- Test actual portability (does it run here?), ephemerality (fresh
  environment), actionability (do build commands work?)
- Record what was actually tested vs. assessed from docs only
- Update ratings based on hands-on findings

---

## Output format

### 1. Narrative assessment

For each STAMPED and FAIR property, write a short paragraph with:
- Rating: `strong` | `partial` | `weak` | `absent` | `N/A`
- Specific evidence supporting the rating
- What would improve the rating (if not `strong`)

### 2. Summary table

```markdown
| Property | Rating | Key evidence |
|----------|--------|-------------|
| S — Self-contained | ... | ... |
| T — Tracked | ... | ... |
| A — Actionable | ... | ... |
| M — Modular | ... | ... |
| P — Portable | ... | ... |
| E — Ephemeral | ... | ... |
| D — Distributable | ... | ... |
| F — Findable | ... | ... |
| A — Accessible | ... | ... |
| I — Interoperable | ... | ... |
| R — Reusable | ... | ... |
```

### 3. YAML front matter block

When assessing something that could become a `content/examples/` entry,
produce a ready-to-use front matter block:

```yaml
---
title: "..."
date: YYYY-MM-DD
description: "..."
summary: "..."
tags: [...]
stamped_principles: [...]   # only properties rated strong or partial
fair_principles: [...]       # only properties rated strong or partial
instrumentation_levels: [...]
aspirations: [...]
state: wip
params:
  tools: [...]
  difficulty: "..."
  verified: false
---
```

### 4. Recommendations

Bullet list of concrete actions that would strengthen weak properties.
Prioritize high-impact, low-effort improvements first.

---

## Rating scale

- **`strong`** — All MUST requirements met, most SHOULD requirements met,
  clear evidence.
- **`partial`** — MUST requirements mostly met but with gaps, or met only at
  the minimum end of the spectrum.
- **`weak`** — Some relevant practices present but significant gaps in MUST
  requirements.
- **`absent`** — Property not meaningfully addressed.
- **`N/A`** — Property does not apply to this type of target (rare, must
  justify).

---

Now assess the target specified in the argument. Begin with Phase 1.
