# Grocery Receipt Analysis

Run `make` to produce `total.txt` from raw price data.

The analysis runs inside an Alpine Linux container (`env.sif`)
that is committed to this repository — no network access needed.
Raw data lives in the `raw-data/` git submodule.

    git clone --recurse-submodules <url>
    make

Requires: POSIX sh, make, singularity (or apptainer).
