# STAMPED Principles — Examples

A companion website to the STAMPED paper, providing concrete examples of
Self-containment, Tracking, Actionability, Modularity, Portability,
Ephemerality, and Distributability for dataset version control.

**Live site:** <https://examples.stamped-principles.org/>

**Build locally:** `hugo server` (requires [Hugo extended](https://gohugo.io/installation/))

## How to contribute examples

We welcome contributions of new examples via pull requests.
If you are new to the PR workflow, see GitHub's
[Creating a pull request from a fork](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request-from-a-fork) guide.

### Adding an example

1. Create a new Markdown file under `content/examples/`, e.g.
   `content/examples/my-example-slug.md`.

2. Fill in the front matter — every example needs these fields:

   ```yaml
   ---
   title: "Short descriptive title"
   date: 2026-01-15
   description: "One-sentence description for metadata/SEO"
   summary: "Slightly longer summary shown in listings"
   tags: ["relevant", "keywords"]
   stamped_principles: ["S", "T", "A", "M", "P", "E", "D"]  # which apply
   fair_principles: ["F", "A", "I", "R"]                      # which apply
   instrumentation_levels: ["data-organization"]  # or: tool, workflow, pattern
   aspirations: ["reproducibility"]  # or: rigor, transparency, efficiency
   state: wip         # wip | uncurated-ai | final (omit for final)
   params:
     tools: ["git"]   # tools used in the example
     difficulty: "beginner"  # beginner | intermediate | advanced
     verified: false   # set true once commands have been tested
   ---
   ```

3. Write the body: explain the problem, show the solution with concrete
   commands and code snippets, and connect it back to the STAMPED
   principles it demonstrates.

4. Open a pull request against `main`.

### Taxonomy values

| Dimension | Valid values |
|---|---|
| `stamped_principles` | `S` `T` `A` `M` `P` `E` `D` |
| `fair_principles` | `F` `A` `I` `R` |
| `instrumentation_levels` | `data-organization` `tool` `workflow` `pattern` |
| `aspirations` | `reproducibility` `rigor` `transparency` `efficiency` |
| `state` | `wip` `uncurated-ai` `final` (or omit) |
| `params.difficulty` | `beginner` `intermediate` `advanced` |

## Licensing

This project follows the [REUSE specification](https://reuse.software/)
for machine-readable copyright and licensing information.

- Full license text: [`LICENSES/Apache-2.0.txt`](LICENSES/Apache-2.0.txt)
  (root `LICENSE` symlinks to it for GitHub auto-detection).
- Per-file declarations: `REUSE.toml` (a single catch-all block —
  everything is licensed under Apache-2.0).
- Verification: `tox -e reuse`.

<!-- REUSE-IgnoreStart -->
When adding new files, no per-file SPDX header is required — the
catch-all block in `REUSE.toml` covers the entire tree. If a file
ever needs a different license (rare), add a targeted block to
`REUSE.toml` or an in-file `SPDX-License-Identifier:` header.
<!-- REUSE-IgnoreEnd -->
