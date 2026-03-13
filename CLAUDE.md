# CLAUDE.md — principles-examples

Companion website to the STAMPED paper with runnable examples demonstrating
Self-containment, Tracking, Actionability, Modularity, Portability,
Ephemerality, and Distributability for dataset version control.

- **Live site:** https://myyoda.github.io/principles-examples/
- **Repo:** https://github.com/myyoda/principles-examples
- **License:** Apache 2.0

## Tech stack

- **Hugo Extended** (0.153.0) with **Congo** theme (git submodule, custom fork at `themes/congo`)
- **Sybil + pytest** for testing shell snippets embedded in markdown
- **tox** for test orchestration
- Hugo theme submodule: `git submodule update --init themes/congo`

## Key commands

```bash
hugo server --enableGitInfo     # Local dev server
tox                             # Run all tests (snippets + hugo build)
tox -e snippets                 # Test shell snippets only
tox -e hugo                     # Validate Hugo build only
tox -e materialize              # Create example git branches from scripts
make pdf                        # Generate stamped-examples.pdf (needs pandoc + xelatex)
```

## Project layout

```
content/examples/         # Markdown examples (the core content)
config/_default/          # Hugo config (hugo.toml, params.toml, menus, markup)
layouts/                  # Hugo template overrides and custom partials
  _default/_markup/       # Code block renderers (strip pragmas, detect scripts)
  partials/               # state-banner.html, example-meta.html
scripts/
  snippet_parser.py       # Shared parser for ```sh blocks and pragmas
  materialize_examples    # Execute testruns, import results as git branches
  dematerialize_examples  # Clean up materialized branches
  build-pdf.py            # Group examples by principle, generate PDF via pandoc
tests/test_materialize.py # Unit + integration tests for materialization
conftest.py               # Sybil setup — finds and executes testrun blocks
```

## Writing examples

Each example is a markdown file under `content/examples/`. Required front matter:

```yaml
stamped_principles: ["S", "T"]   # Subset of S,T,A,M,P,E,D
fair_principles: ["F", "A"]      # Subset of F,A,I,R
instrumentation_levels: ["tool"] # data-organization | tool | workflow | pattern
aspirations: ["reproducibility"] # reproducibility | rigor | transparency | efficiency
state: wip                       # wip | uncurated-ai | final (omit for final)
params:
  tools: ["git", "datalad"]
  difficulty: "intermediate"     # beginner | intermediate | advanced
  verified: false
```

Must read `README.md` for the full taxonomy reference.

## Shell snippet pragmas

Executable code blocks use `# pragma:` annotations parsed by `scripts/snippet_parser.py`:

```sh
#!/bin/sh
# pragma: testrun scenario-1      # Required — identifies the test
# pragma: requires sh awk          # Tools needed (skips if missing)
# pragma: timeout 120              # Seconds before timeout (default 60)
# pragma: exitcode 0               # Expected exit code (default 0)
# pragma: materialize grocery-analysis  # Git repo to capture as branch
```

Pragmas are stripped from rendered HTML by `layouts/_default/_markup/render-codeblock-sh.html`.

## Materialized example branches

`scripts/materialize_examples` runs testrun scripts and imports resulting git
repos as branches under `examples/{file-stem}/{testrun-id}/{repo-name}`.
Uses `refs/notes/materialize` for SHA-256 cache to avoid regeneration.
CI runs this on push to main with `--strict --push`.

## CI/CD

- **GitHub Actions** (`test.yml`): tox tests + materialize on PR/push
- **GitHub Pages** (`hugo.yml`): deploy on push to main
- **Netlify** (`netlify.toml`): PR deploy previews with CORS headers for SRI

## Hugo customizations

- **Congo theme fork** with mermaid pan/zoom/fullscreen (`params.toml: mermaid.panZoom = true`)
- Four custom taxonomies: `stamped_principles`, `fair_principles`, `instrumentation_levels`, `aspirations`
- State banners for `wip` / `uncurated-ai` content
- Code block renderers distinguish scripts (full shebang) from snippets
