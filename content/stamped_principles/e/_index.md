---
title: "E — Ephemeral"
description: "Results produced in temporary, disposable environments validate that other STAMPED properties hold"
---

If a research object can produce its results in a temporary, disposable
environment built solely from its own contents, this provides strong evidence
that its other STAMPED properties hold in practice. Inputs must be exhaustively
specified (S), outputs deposited correctly (T), and nothing outside the boundary
relied upon. Ephemerality is a form of validation: "make it a habit to destroy
the environment."

Beyond validation, ephemeral environments enable scaling -- when each
computational job runs in an independent, disposable instance, work can be
parallelized across subjects, parameters, or datasets.

At a minimum, a research object should be able to produce results from a fresh
clone on a system that meets its stated requirements (P). At the ideal end,
every computation runs in a disposable environment that is created and destroyed
per execution.

See the [STAMPED paper](https://github.com/stamped-principles/stamped-paper) for the
full treatment.
