---
title: "STAMPED Principles — Examples"
description: "Concrete examples demonstrating the STAMPED principles for idiomatic dataset version control"
---

This site is a companion resource to the
[STAMPED paper](https://github.com/stamped-principles/stamped-paper) on properties of
a reproducible research object. It provides concrete, pragmatic examples that
demonstrate the seven STAMPED properties in practice -- from simple naming
conventions to complex multi-tool workflows.

## What is STAMPED?

STAMPED defines seven properties that characterize a well-formed reproducible
research object -- a collection of data, code, and metadata that together
represent a complete unit of research output.
See the [paper](https://github.com/stamped-principles/stamped-paper) for the full
treatment; the table below is a quick reference:

| Property | Core idea |
|---|---|
| **[S]({{< ref "stamped_principles/s" >}})** -- [Self-contained]({{< ref "stamped_principles/s" >}}) | Everything needed to replicate results is within a single top-level boundary -- the "don't look up" rule. |
| **[T]({{< ref "stamped_principles/t" >}})** -- [Tracked]({{< ref "stamped_principles/t" >}}) | All components are content-addressed and version-controlled; provenance of every modification is recorded. |
| **[A]({{< ref "stamped_principles/a" >}})** -- [Actionable]({{< ref "stamped_principles/a" >}}) | Procedures are executable specifications, not just documentation -- a cross-cutting property that applies to every other STAMPED dimension. |
| **[M]({{< ref "stamped_principles/m" >}})** -- [Modular]({{< ref "stamped_principles/m" >}}) | Components are organized as independently versioned modules that can be composed, updated, and reused separately. |
| **[P]({{< ref "stamped_principles/p" >}})** -- [Portable]({{< ref "stamped_principles/p" >}}) | Procedures do not depend on undocumented host state; computational environments are explicitly specified and versioned. |
| **[E]({{< ref "stamped_principles/e" >}})** -- [Ephemeral]({{< ref "stamped_principles/e" >}}) | Results can be produced in temporary, disposable environments built solely from the research object's contents -- validating that other properties hold. |
| **[D]({{< ref "stamped_principles/d" >}})** -- [Distributable]({{< ref "stamped_principles/d" >}}) | The research object and all its components are persistently retrievable by others, packaged like a software distribution. |

These properties reinforce one another.
Self-containment makes portability practical, tracking enables actionability,
and modularity supports distributability.

## How examples are organized

Each example on this site is tagged along multiple dimensions so you can
explore the collection from whatever angle is most useful to you:

- **[STAMPED principles]({{< ref "stamped_principles" >}})** -- which of the seven principles does the example
  primarily demonstrate?
- **[FAIR mapping]({{< ref "fair_principles" >}})** -- which of the FAIR
  goals ([Findable]({{< ref "fair_principles/f" >}}), [Accessible]({{< ref "fair_principles/a" >}}), [Interoperable]({{< ref "fair_principles/i" >}}), [Reusable]({{< ref "fair_principles/r" >}})) does the practice
  help achieve?
- **[Instrumentation level]({{< ref "instrumentation_levels" >}})** -- how much tooling does the example require,
  from plain conventions that need no special software to workflows that
  depend on specific version-control infrastructure?
- **[Aspirational goals]({{< ref "aspirations" >}})** -- what higher-level objectives ([reproducibility]({{< ref "aspirations/reproducibility" >}}),
  [transparency]({{< ref "aspirations/transparency" >}}), [rigor]({{< ref "aspirations/rigor" >}}), [efficiency]({{< ref "aspirations/efficiency" >}})) does the practice serve?

## Get started

Head to the [Examples]({{< ref "examples" >}}) section to browse the full
collection. You can also explore by taxonomy using the footer links, or use
the search bar to find examples relevant to your needs.
