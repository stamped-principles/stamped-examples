---
title: "Ephemeral Shell Scripts for Reproducing Issues"
date: 2026-02-19
description: "A pattern for writing minimal, self-contained shell scripts that reproduce software issues in temporary environments"
summary: "Distills a common practice among open-source developers: writing throwaway shell scripts that set up a fresh environment, reproduce a problem, and can be shared as actionable bug reports or starting points for test cases."
tags: ["shell", "posix", "reproducer", "bug-report", "testing"]
stamped_principles: ["S", "A", "E", "P"]
fair_principles: ["R", "A"]
instrumentation_levels: ["pattern"]
aspirations: ["reproducibility", "rigor", "transparency"]
params:
  tools: ["sh"]
  difficulty: "beginner"
  verified: false
state: wip
---

## The pattern

When a user encounters a bug or unexpected behavior in a command-line
tool, one of the most effective responses is to write a **minimal shell script**
that reproduces the problem from scratch.  The script creates a temporary
directory, sets up just enough state (repositories, files, configuration) to
trigger the issue, runs the offending commands, and exits.  The temporary
directory can then be inspected — or simply thrown away.

This pattern is ubiquitous in the git, git-annex, and DataLad communities.

## Anatomy of a reproducer script

### A bare-bone example

```sh
#!/bin/sh
# pragma: testrun bare-bone
# pragma: exitcode 1
# Reproducer for "file not found" — a filename typo

# -- setup shell environment --
set -eux
PS4='> '
cd "$(mktemp -d "${TMPDIR:-/tmp}/repro-XXXXXXX")"

# -- setup your case --
touch preciouss.dat

# -- collect extra information --
ls

# -- trigger --
test -e precious.dat
```

The script fails — `set -e` aborts as soon as `test -e precious.dat` returns
non-zero.  The trace (`set -x`) already tells the full story:

```output
> cd /tmp/repro-m6CM6OZ
> touch preciouss.dat
> ls
preciouss.dat
> test -e precious.dat
```

No extra diagnostics needed, although you would know where to look
(`/tmp/repro-m6CM6OZ`) — the `ls` output and the failing `test` make the
typo obvious.  This is maximally portable (POSIX `sh` + coreutils) and
self-contained.

### Key elements

**1. Shebang: `#!/bin/sh` (prefer POSIX)**

Use `#!/bin/sh` for maximum [portability]({{< ref "stamped_principles/p" >}}).
Only reach for `#!/bin/bash` when you genuinely need bash-specific features
(arrays, `[[ ]]`, process substitution).

**2. Strict mode and tracing: `set -eux` and `PS4='> '`**

- `-e` — exit immediately on any non-zero return.  If the setup steps fail,
  there is no point continuing to the "trigger" phase.
- `-u` — treat unset variables as errors.  Catches typos and missing
  configuration.
- `-x` — print every command before it executes — invaluable when sharing
  the script with someone who needs to see exactly what happened.

Always pair `-x` with an explicit `PS4` assignment:

```sh
set -eux
PS4='> '
```

as `PS4` controls the prefix printed before each traced command (the default is
`+ `).  Setting it explicitly serves two purposes beyond readability:

- **[Reproducibility]({{< ref "aspirations/reproducibility" >}})** — the
  output is identical regardless of what the user's shell profile sets `PS4`
  to, making traces diffable across environments.
- **[Portability]({{< ref "stamped_principles/p" >}})** — some systems define
  `PS4` with shell-specific expansions (timestamps, function names) that can
  cause errors or garbled output when the script runs under a different shell.
  A simple literal value avoids this entirely.

If a script invokes `bash -x script.sh` externally, having `PS4`
defined inside the script ensures consistent output regardless of how it was
launched.

**3. Ephemeral workspace: `mktemp -d`**

```sh
cd "$(mktemp -d "${TMPDIR:-/tmp}/dl-XXXXXXX")"
```

This is the core of [ephemerality]({{< ref "stamped_principles/e" >}}): every
run starts in a brand-new, empty directory.  Using `mktemp` rather than a
hardcoded path like `cd /tmp/mytest` is also a **security measure** — on
shared systems, a predictable path under `/tmp` is vulnerable to symlink
attacks where another user pre-creates a symlink pointing to a victim location.
`mktemp` generates an unpredictable name atomically.

The `${TMPDIR:-/tmp}` fallback respects system conventions across Linux and
macOS.  The prefix (`dl-`, `gx-`, `ann-`) identifies which tool the script
tests, making it easy to find (or clean up) leftover directories.

No `trap ... EXIT` cleanup is usually needed — `/tmp` is cleaned by the OS,
and you often *want* to inspect the result after a failure, and having `set -x`
visualizes initial `cd` path.

**4. Self-contained setup**

The script creates everything it needs from scratch — `touch`, `mkdir`,
`echo content > file`.  It does not depend on pre-existing files on the
user's machine.  This makes the script
[self-contained]({{< ref "stamped_principles/s" >}}) — anyone with POSIX
`sh` can run it.

**5. Tracked externals**

When a reproducer *must* pull in external materials, that is fine — `git clone`,
`docker pull`, `wget` are all normal.  The key is to reference **exact,
immutable identifiers** so the script stays
[tracked]({{< ref "stamped_principles/t" >}}):

- **git** — pin to a commit hash or tag, not a branch:
  `git clone --branch v1.2.3 https://github.com/org/repo`
- **containers** — pin by digest, not a mutable tag:
  `docker pull alpine@sha256:a8560b36e8...`
- **URLs** — use version-pinned URLs or archived snapshots
  (e.g., [Wayback Machine](https://web.archive.org/) links) rather than
  a "latest" URL that may change or vanish.

The script does not need to *contain* every byte — it needs to *point* to an
exact, reproducible state of every dependency.

## STAMPED analysis

| Property | How the pattern embodies it |
|---|---|
| [Self-contained]({{< ref "stamped_principles/s" >}}) | Everything needed is created inline — no external state required beyond the tool under test |
| [Tracked]({{< ref "stamped_principles/t" >}}) | The script *is* the record: copy-pasteable into an issue, attachable to a commit |
| [Actionable]({{< ref "stamped_principles/a" >}}) | Running the script *is* the reproduction — it is an executable specification of the bug, not a prose description |
| [Portable]({{< ref "stamped_principles/p" >}}) | POSIX sh + `mktemp` + `${TMPDIR:-/tmp}` works across Linux and macOS; explicit `PS4` avoids shell-specific trace behavior; no hardcoded paths |
| [Ephemeral]({{< ref "stamped_principles/e" >}}) | Each run operates in a fresh temp directory; the entire workspace can be discarded after inspection |

## From reproducer to test case

A reproducer script is often the **first draft of a regression test**.  The
progression is natural:

1. **Bug report** — paste the script into a GitHub issue.  Anyone can run it.
2. **Bisection driver** — wrap the script's exit code in `git bisect run` to
   find the introducing commit.
3. **Red/green test** — translate the shell commands into the project's test
   framework (e.g., pytest).  The setup phase becomes a fixture, the trigger
   becomes the test body, and the inspection becomes an assertion.

This progression from throwaway script to permanent test case mirrors the
Red/Green cycle of [TDD](https://en.wikipedia.org/wiki/Test-driven_development):
the reproducer is the "red" test that fails, the fix
makes it "green", and the test prevents regressions.

## Practical guidelines

1. **Name scripts after issue numbers**: `bug-3686.sh`, `gh-6296.sh`,
   `annex-4369.sh`.  When you return months later, the filename links directly
   to the discussion.

2. **Use a descriptive prefix in `mktemp`**: `dl-` for DataLad, `gx-` for
   git-annex, `ann-` for general annex tests.  This makes orphaned temp
   directories identifiable.

3. **Always set `PS4`**: Even if you omit `set -x` from the script itself,
   setting `PS4='> '` ensures consistent trace output when someone runs
   `bash -x script.sh` externally.

4. **Print version information early**: `git --version` or
   `python3 --version` at the top helps recipients match your environment.

5. **Do not clean up on success**: Leave the temp directory intact so you (or
   the recipient) can inspect the state.  `/tmp` is cleaned on reboot.

6. **Keep scripts minimal**: Every line that is not strictly necessary to
   trigger the bug is noise.  Minimal scripts are easier to review, faster to
   bisect, and more likely to be turned into test cases.

7. **Test your own instructions**: Before sharing a reproducer (e.g., in a
   GitHub issue), copy-paste the invocation instructions you gave the recipient
   and run them yourself on a different machine or in a fresh shell.  This
   catches implicit assumptions — a forgotten dependency, a path that only
   exists on your system, or a missing `chmod +x` — before someone else hits
   them.
