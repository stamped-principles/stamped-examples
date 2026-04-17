---
title: "T — Tracked"
description: "Version information and provenance recorded for all components via content-addressed version control"
---

Version information must be recorded for all components, ideally using the same
content-addressed version control system. The primary value is not version
numbering ("v1" vs "v2") but content-addressed identification -- two datasets
with identical content hashes are provably identical.

Tracking encompasses not only version history but also provenance: what actions
produced or modified each component, what inputs were consumed, and what versions
of code and environment were involved. For code-driven modifications, provenance
should be captured programmatically rather than by manual annotation.

See the [STAMPED paper](https://github.com/stamped-principles/stamped-paper) for the
full treatment.
