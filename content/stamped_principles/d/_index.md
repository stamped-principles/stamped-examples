---
title: "D — Distributable"
description: "The research object and all its components are persistently retrievable by others"
---

Self-containment (S) establishes that everything needed is within the research
object's boundary. Distributability promises that those references actually
deliver -- that the research object and its components can be shared, retrieved,
and used by others in a state consistent with reuse.

The distinction mirrors the concept of a software distribution: a curated,
versioned bundle in which all components are resolved to specific versions and
packaged for consumption. Simply sharing scripts with loose dependencies does not
constitute distribution in this sense.

The spectrum ranges from publicly accessible components with retrieval
instructions, through persistent hosting on archival infrastructure (Zenodo,
PyPI, conda-forge, DANDI) with frozen versions and content-addressed identifiers,
to a fully self-contained archive (e.g., a built container or a zipped RO-Crate).

See the [STAMPED paper](https://github.com/stamped-principles/stamped-paper) for the
full treatment.
