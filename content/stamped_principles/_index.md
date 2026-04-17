---
title: "STAMPED Properties"
description: "The seven properties of a well-formed reproducible research object"
---

**STAMPED** defines seven properties that characterize a well-formed
reproducible research object. The framework originates from the YODA principles
and is described in full in the
[STAMPED paper](https://github.com/stamped-principles/stamped-paper).

- **S -- [Self-contained](s/)**: All modules and components essential to
  replicate results are within a single top-level boundary.

- **T -- [Tracked](t/)**: All components are content-addressed; provenance of
  every modification is recorded.

- **A -- [Actionable](a/)**: Procedures are executable specifications, not just
  documentation. A cross-cutting property that applies to every other dimension.

- **M -- [Modular](m/)**: Components are organized as independently versioned
  modules that can be composed and reused.

- **P -- [Portable](p/)**: Procedures do not depend on undocumented host state;
  environments are explicitly specified and versioned.

- **E -- [Ephemeral](e/)**: Results can be produced in temporary, disposable
  environments built solely from the research object's contents.

- **D -- [Distributable](d/)**: The research object and all its components are
  persistently retrievable, packaged like a software distribution.
