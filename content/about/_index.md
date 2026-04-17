---
title: "About"
description: "About the STAMPED Properties Examples resource"
---

## Companion to the STAMPED paper

This site is the companion resource to the
[STAMPED paper](https://github.com/stamped-principles/stamped-paper) ("STAMPED:
Properties of a Reproducible Research Object"). While the paper develops the
framework and evaluates existing tools against it, this site provides the
practical side: concrete, runnable examples that show how the properties look
when applied to real data management tasks.

## STAMPED and YODA

The [YODA principles](https://handbook.datalad.org/en/latest/basics/101-127-yoda.html)
(YODA's Organigram on Data Analysis) established foundational conventions for
structuring DataLad datasets. STAMPED extends and generalizes those ideas
beyond any single tool:

- Where YODA focuses on DataLad dataset organization, STAMPED formalizes
  **properties of a research object** that make YODA effective and expresses
  them in a tool-agnostic way.
- STAMPED adds properties (such as [Ephemerality]({{< ref "stamped_principles/e" >}}) and [Distributability]({{< ref "stamped_principles/d" >}})) that were
  implicit in YODA practice but not explicitly named.
- By decoupling the properties from a specific tool, STAMPED provides a
  vocabulary for evaluating *any* dataset management approach -- whether built
  on DataLad, DVC, Git LFS, Hugging Face Datasets, or plain Git with
  conventions.

## Multi-dimensional taxonomy

Examples on this site are organized along four independent dimensions:

1. **[STAMPED properties]({{< ref "stamped_principles" >}})** -- [Self-contained]({{< ref "stamped_principles/s" >}}), [Tracked]({{< ref "stamped_principles/t" >}}), [Actionable]({{< ref "stamped_principles/a" >}}),
   [Modular]({{< ref "stamped_principles/m" >}}), [Portable]({{< ref "stamped_principles/p" >}}), [Ephemeral]({{< ref "stamped_principles/e" >}}), and [Distributable]({{< ref "stamped_principles/d" >}}).
2. **[FAIR mapping]({{< ref "fair_principles" >}})** -- which of the FAIR goals ([Findable]({{< ref "fair_principles/f" >}}), [Accessible]({{< ref "fair_principles/a" >}}),
   [Interoperable]({{< ref "fair_principles/i" >}}), [Reusable]({{< ref "fair_principles/r" >}})) the practice supports.
3. **[Instrumentation level]({{< ref "instrumentation_levels" >}})** -- ranging from [conventions]({{< ref "instrumentation_levels/data-organization" >}}) that require no
   special tooling, through lightweight [tools]({{< ref "instrumentation_levels/tool" >}}), to full version-control
   [workflows]({{< ref "instrumentation_levels/workflow" >}}).
4. **[Aspirational goals]({{< ref "aspirations" >}})** -- higher-level objectives such as [reproducibility]({{< ref "aspirations/reproducibility" >}}),
   [rigor]({{< ref "aspirations/rigor" >}}), [transparency]({{< ref "aspirations/transparency" >}}), and [efficiency]({{< ref "aspirations/efficiency" >}}).

An example may be tagged with multiple values in each dimension. A README
convention, for instance, supports Self-containment *and* Findability *and*
Reusability while requiring no special instrumentation.

## Range of examples

Examples span a wide range of complexity:

- **Simple conventions** -- directory layouts, naming schemes, README templates
  that require nothing more than discipline.
- **Lightweight practices** -- using checksums, manifests, or small scripts to
  add provenance without heavy infrastructure.
- **Tool-assisted workflows** -- leveraging Git, Git-annex, DataLad, DVC, or
  similar tools for automated tracking and distribution.
- **Advanced pipelines** -- multi-step, multi-tool workflows that demonstrate
  several STAMPED principles working together.

## Contributing

We welcome contributions of new examples, corrections, and improvements.
The source for this site lives at
<https://github.com/stamped-principles/stamped-examples>. To contribute:

1. Fork the repository.
2. Add or edit example pages under `content/examples/`.
3. Tag your example with the appropriate STAMPED principles, FAIR mappings,
   instrumentation level, and aspirational goals in the front matter.
4. Open a pull request with a brief description of what the example
   demonstrates.

See the repository README for details on front-matter fields and the
taxonomy values available.
