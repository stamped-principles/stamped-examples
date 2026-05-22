---
title: "Tracking AI Agent Contributions with Entire"
date: 2026-02-20
description: "How Entire uses git orphan branches and session hooks to record AI agent provenance alongside code, demonstrating the Tracked, Actionable, and Distributable principles."
summary: "When AI agents write code, the reasoning behind their decisions disappears when the terminal closes. Entire captures session-level provenance in a git orphan branch that travels with the repository, making AI contributions as trackable and distributable as the code itself."
tags: ["ai-agents", "provenance", "git", "claude-code", "attribution"]
stamped_principles: ["T", "A", "D"]
fair_principles: ["R", "A"]
instrumentation_levels: ["tool"]
aspirations: ["reproducibility", "transparency"]
state: wip
params:
  tools: ["entire", "git", "claude-code"]
  difficulty: "intermediate"
  verified: false
---

## The problem

When an AI agent like Claude Code helps write a data analysis script, the resulting
git commit captures *what* changed — the diff, the files, the commit message. What
it cannot capture is *why*: which alternatives the researcher considered, what
constraints they gave the agent, or why a particular algorithm or parameter value
was chosen over another.

This is a provenance gap. Close the terminal, reboot the laptop, or come back to
a repository six months later, and the conversation that produced the code is no
longer part of the repository — the JSONL transcript may still sit in a local
agent cache, but nothing travels with the code. A collaborator reading the
commit history sees only the output of the reasoning process, not the
reasoning itself.

For computational research, this matters. A preprocessing pipeline with a particular
smoothing kernel or motion threshold may be entirely correct — but if nobody can
trace back *why* those values were chosen, the research object is not fully
[Tracked]({{< ref "stamped_principles/t" >}}). 
Reproducing the results is possible in principle; understanding them is not.

## What Entire does

[Entire](https://entire.io) ([source](https://github.com/entireio/cli),
[docs](https://docs.entire.io/)) is a CLI tool that integrates with Claude Code
via its hook system to capture session-level provenance automatically and
store it in git's own infrastructure. It adds three layers on top of a normal
git workflow:

**1. Transcript mining.** Entire treats Claude Code's local JSONL session transcript
as the authoritative record of what the agent did. Rather than relying on external
APIs, it reads this file to extract modified files, user prompts, token usage, and
the agent's summary of its own work.

**2. Shadow branches.** During a session, Entire builds in-memory git tree
snapshots under temporary branches named `entire/<commit-hash>-<worktree-hash>`,
where `<commit-hash>` is a short prefix of the pre-session HEAD. These
branches capture the working-tree state at key points during the session and
serve as the baseline against which Entire computes attribution — without
touching the developer's working branch. The pre-session tree itself is just
the parent commit; no separate snapshot file is stored.

**3. Orphan metadata branch.** When a session ends, Entire consolidates the
session transcript and metadata into a permanent orphan branch called
`entire/checkpoints/v1`. Checkpoint IDs are 12 random hex characters, sharded
into subdirectory paths under the orphan branch — the first two characters
become the top-level directory and the remaining ten the next level (e.g.
`a3/b2c4d5e6f7/`) — making the branch merge as a simple tree union with no
conflicts possible.

**Bidirectional linking.** Trailer insertion is handled by *git-side* hooks
that `entire enable` installs alongside the Claude Code hooks. The
`prepare-commit-msg` hook injects an `Entire-Checkpoint` trailer into the
in-progress commit message, and `post-commit` finalizes the link by amending
the commit:

```
Entire-Checkpoint: a3b2c4d5e6f7
```

This creates a two-way link: given any commit, `git log` exposes the checkpoint ID;
given any checkpoint ID, a `git log --grep` search locates the commit. The
behavior is idempotent — if a follow-up session amends a commit that already
carries an `Entire-Checkpoint` trailer, the new session is appended to the
existing checkpoint rather than producing a new one.

**Attribution measurement.** By snapshotting the working tree at the moment a prompt
is submitted (before the agent responds), Entire can measure which lines existed
before the agent touched the file. A LIFO heuristic then attributes subsequent
human edits: the assumption is that a developer who removes lines removes their own
additions first, avoiding unfair penalization of agent-written code.

## Setup

Entire integrates with Claude Code via its hooks mechanism. After installing the CLI,
running `entire enable` in a repository writes hook registrations into
`.claude/settings.json` and creates an `.entire/settings.json` for Entire's own
configuration:

```sh
# Install Entire (Homebrew — distributed as a cask)
brew tap entireio/tap
brew install --cask entire

# Or via Go
go install github.com/entireio/cli/cmd/entire@latest

# Enable in a repository
cd my-research-project
entire enable
```

The resulting `.claude/settings.json` registers six Claude Code hook events
(`PostToolUse` is registered twice, once per matcher):

```json
{
  "hooks": {
    "SessionStart":     [{ "matcher": "", "hooks": [{ "type": "command", "command": "<guarded> entire hooks claude-code session-start" }] }],
    "SessionEnd":       [{ "matcher": "", "hooks": [{ "type": "command", "command": "<guarded> entire hooks claude-code session-end" }] }],
    "UserPromptSubmit": [{ "matcher": "", "hooks": [{ "type": "command", "command": "<guarded> entire hooks claude-code user-prompt-submit" }] }],
    "Stop":             [{ "matcher": "", "hooks": [{ "type": "command", "command": "<guarded> entire hooks claude-code stop" }] }],
    "PreToolUse":       [{ "matcher": "Task", "hooks": [{ "type": "command", "command": "<guarded> entire hooks claude-code pre-task" }] }],
    "PostToolUse": [
      { "matcher": "Task",      "hooks": [{ "type": "command", "command": "<guarded> entire hooks claude-code post-task" }] },
      { "matcher": "TodoWrite", "hooks": [{ "type": "command", "command": "<guarded> entire hooks claude-code post-todo" }] }
    ]
  }
}
```

Each `<guarded>` placeholder above stands for an availability check that
makes the repository safe to clone on machines where `entire` is not
installed:

```
sh -c 'if ! command -v entire >/dev/null 2>&1; then exit 0; fi; exec <inner>'
```

These hooks fire automatically on every Claude Code session in the repository
from this point forward. `entire enable` also installs three git-side hooks
under `.git/hooks/` (`prepare-commit-msg`, `commit-msg`, `post-commit`) for
trailer insertion, creates the `entire/checkpoints/v1` orphan branch
immediately, and prompts for telemetry consent (pass `--yes` for
non-interactive setups). No further configuration is needed for basic
provenance capture.

## Concrete scenario: a neuroimaging preprocessing pipeline

A researcher opens Claude Code and asks:

> "Write a Python script that loads a BOLD fMRI timeseries from a NIfTI file,
> applies motion correction using the six rigid-body parameters in a .par file,
> high-pass filters at 1/128 Hz, and saves the result. Use nilearn."

The agent produces `preprocess.py`. The researcher reviews it, makes a small edit
to tighten the filter cutoff, and commits:

```sh
git add preprocess.py
git commit -m "Add BOLD preprocessing pipeline"
```

Because the git-side `prepare-commit-msg` and `post-commit` hooks are
installed, Entire amends the commit message to add the trailer:

```
commit 9f3ab12cde45f6a7
Author: Jane Researcher <jane@lab.edu>
Date:   Thu Feb 20 14:32:01 2026

    Add BOLD preprocessing pipeline

    Entire-Checkpoint: a3b2c4d5e6f7
```

The checkpoint ID `a3b2c4d5e6f7` is now permanently part of the repository history.

### What was captured

At the moment Jane submitted her prompt (`UserPromptSubmit` hook), Entire snapshotted
the working tree into a shadow branch. This records that `preprocess.py` did not
exist before the session — the file is attributable entirely to the agent. Jane's
subsequent edit to the filter cutoff is captured as a human modification.

When the session ended (`Stop` hook), Entire serialised the full session
metadata into the `entire/checkpoints/v1` orphan branch under
`a3/b2c4d5e6f7/`:

```
entire/checkpoints/v1
└── a3/
    └── b2c4d5e6f7/
        ├── metadata.json          # checkpoint-level summary (across sessions)
        └── 0/                     # per-session sub-index (0, 1, 2, ...)
            ├── metadata.json      # session metrics, token usage, attribution
            ├── full.jsonl         # JSONL transcript of the session
            ├── prompt.txt         # the user prompt
            └── content_hash.txt   # content fingerprint
```

Attribution data — per-file agent/human line counts and percentages — lives
inside `metadata.json` as the `initial_attribution` and
`combined_attribution` fields rather than in a separate file. When a follow-up
session is appended to the same checkpoint, it is written as a new sub-index
(`1/`, `2/`, ...) alongside `0/`.

## Querying the provenance

Two commands cover most provenance queries, alongside standard git:

```sh
# Inspect a session or commit (pass a checkpoint ID or commit SHA)
entire checkpoint explain a3b2c4d5e6f7

# Find all commits that involved agent assistance
git log --grep="Entire-Checkpoint" --format="%H %s"

# Browse the checkpoint branch directly
git log entire/checkpoints/v1 --oneline
```

`entire checkpoint explain` retrieves the full session record — prompts,
token usage, modified files, and attribution data — for the given checkpoint.

A collaborator cloning the repository six months later can run
`entire checkpoint explain` on any commit's checkpoint ID and retrieve the
exact prompt that drove the change — without needing access to the original
developer's machine or Claude conversation history.

## STAMPED analysis

| Principle | How Entire embodies it |
|---|---|
| [Tracked]({{< ref "stamped_principles/t" >}}) | Every AI-assisted session is stored in a content-addressed git orphan branch. The `Entire-Checkpoint:` trailer creates bidirectional links between commits and session metadata. File changes, prompts, token usage, and human-vs-agent attribution are all version-controlled. |
| [Actionable]({{< ref "stamped_principles/a" >}}) | Provenance capture requires no manual steps — hooks fire automatically on every session. Checkpoint data is machine-readable JSON that downstream tools can query, diff, and process. `entire checkpoint explain` makes any session's context retrievable on demand. |
| [Distributable]({{< ref "stamped_principles/d" >}}) | The `entire/checkpoints/v1` orphan branch is a standard git branch. Running `git push` transmits it alongside the code branches. Any collaborator who clones the repository receives the complete session history, not just the source files. |

**A note on [Ephemerality]({{< ref "stamped_principles/e" >}}).** Shadow branches are
created per-session and discarded once their contents are consolidated into the orphan
branch. The ephemeral working state of each session leaves no lasting trace on the
main branches — only the distilled checkpoint persists. This is the inverse of the
ephemerality principle as applied to *results* (where you want to be able to
regenerate them in a disposable environment), but it shares the same underlying
value: nothing from the transient session contaminates the permanent record.

## Working in a team

Because checkpoint IDs are 12 random hexadecimal characters, two developers working
concurrently will virtually never produce the same ID. The orphan branch therefore
merges as a pure tree union — new paths are added, existing paths are never
overwritten. Two researchers can push simultaneously without producing conflicts in
the metadata branch.

This also means the `entire/checkpoints/v1` branch accumulates indefinitely.
There is no automatic retention policy, but the CLI provides `entire clean`
for manual pruning (`--all` for the whole repository, `--session <id>` for a
specific session, or HEAD-only by default).

## Practical guidelines

1. **Run `entire enable` at project creation.** Retroactively adding provenance
   tracking to a repository means all prior AI-assisted commits will lack checkpoint
   links. Enable early, when the first agent session begins.

2. **Write informative prompts.** Prompts are stored verbatim in the session record
   and surfaced by `entire checkpoint explain`. A prompt like "fix the bug" leaves a poor audit
   trail; "fix the off-by-one error in the epoch indexing loop in train.py" tells
   future readers exactly what problem was being solved.

3. **Treat `Entire-Checkpoint:` as a citable reference.** The trailer is stable —
   it does not change when branches are rebased or force-pushed (though squash
   merges will lose it, since the original commit message is discarded). For
   important decisions, note the checkpoint ID in your lab notebook alongside the
   commit SHA.

4. **Be aware of privacy implications.** Full prompt transcripts are stored in the
   git repository and are readable by anyone with repository access. Do not include
   sensitive data — API keys, patient identifiers, unpublished results — in prompts
   when working in repositories that will be made public.

5. **Review AI contributions before submission.** Before submitting a paper or
   archiving a dataset, run `git log entire/checkpoints/v1 --since=<start-date>`
   to enumerate all AI-assisted sessions. This gives you a checklist of checkpoints
   to review for correctness and a ready-made record of the generative process to
   include in a methods section.

## Summary

Git's content-addressed storage was designed to make code history trustworthy and
distributable. Entire extends that guarantee to the *generative process* of
AI-assisted code: every session's prompts, file changes, and attribution data are
stored as ordinary git objects in an orphan branch that travels with the repository.

The result is a research object that is more fully [Tracked]({{< ref "stamped_principles/t" >}}) —
not just the state of the code at each commit, but the conversation that produced it —
and more fully [Distributable]({{< ref "stamped_principles/d" >}}), because that
conversation is bundled with the repository rather than siloed in a local terminal.
The hook-based design makes this [Actionable]({{< ref "stamped_principles/a" >}})
without requiring any change to the researcher's existing commit workflow.

For a complementary approach to recording computational provenance through explicit
run records, see [Recording Computational Provenance with datalad run]({{< ref "examples/datalad-run-provenance" >}}).
