#!/usr/bin/env python3
"""Fetch nearby star parallax data from Gaia DR3 via TAP query."""

import requests
import sys

GAIA_TAP_URL = "https://gea.esac.esa.int/tap-server/tap/sync"

QUERY = """\
SELECT TOP {limit}
    source_id, parallax
FROM gaiadr3.gaia_source
WHERE parallax > {min_parallax}
    AND parallax_error / parallax < {max_error_ratio}
ORDER BY parallax DESC
"""


def fetch(output_path, limit=100, min_parallax=10, max_error_ratio=0.1):
    query = QUERY.format(
        limit=limit,
        min_parallax=min_parallax,
        max_error_ratio=max_error_ratio,
    )
    resp = requests.get(GAIA_TAP_URL, params={
        "REQUEST": "doQuery",
        "LANG": "ADQL",
        "FORMAT": "csv",
        "QUERY": query,
    })
    resp.raise_for_status()

    with open(output_path, "w") as f:
        f.write(resp.text)

    n_stars = resp.text.count("\n") - 1
    print(f"Fetched {n_stars} stars -> {output_path}")


if __name__ == "__main__":
    output = sys.argv[1] if len(sys.argv) > 1 else "raw/gaia_nearby.csv"
    fetch(output)
