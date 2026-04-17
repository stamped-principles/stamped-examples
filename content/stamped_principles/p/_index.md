---
title: "P — Portable"
description: "Procedures do not depend on undocumented host state; environments are explicitly specified"
---

A research object that is self-contained, tracked, and modular may still fail to
reproduce if it depends on undocumented host environment state -- hardcoded
paths, implicitly available tools, or specific OS configurations. Portability
requires that procedures can be executed on different hosts, given documented
system requirements.

Computational environments must be explicitly defined (not implicitly assumed),
machine-reproducible, and version controlled alongside code and data. Whether
via containers (Docker, Singularity/Apptainer) or declarative package managers
(Nix, Guix), what matters is that environments are specified, versioned, and
available within the project.

See the [STAMPED paper](https://github.com/stamped-principles/stamped-paper) for the
full treatment.
