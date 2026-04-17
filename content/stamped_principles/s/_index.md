---
title: "S — Self-contained"
description: "All essential modules and components reside within a single top-level boundary"
---

A research object must never rely on implicit external state -- the "don't look
up" rule. All modules and components essential to replicate computational
execution must be contained within a single top-level boundary.

Components may be included literally (files committed directly) or by reference
(subdatasets, registered data URLs), provided the references are explicit and
tracked. Self-containment is the foundational property upon which the remaining
STAMPED properties build.

See the [STAMPED paper](https://github.com/stamped-principles/stamped-paper) for the
full treatment.
