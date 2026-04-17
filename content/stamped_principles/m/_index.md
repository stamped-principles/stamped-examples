---
title: "M — Modular"
description: "Components organized as independently versioned modules that can be composed and reused"
---

Rather than managing a research object as one indivisible whole, STAMPED promotes
a compositional approach: independently versioned modules (input datasets,
processing scripts, computational environments) can be updated or replaced
separately, minimizing disruption and maximizing reusability.

An idiomatic layout delineates components into structured directories --
`code/`, `inputs/`, `envs/`, `docs/`, `results/` -- clarifying how they interact
and supporting domain-specific standards (e.g., BIDS). Components may be
included directly or linked as subdatasets (git submodules), each with its own
independent version history.

See the [STAMPED paper](https://github.com/stamped-principles/stamped-paper) for the
full treatment.
