#!/usr/bin/env python3
"""Quick proof of concept: fetch Gaia parallax data and compute distances."""

import csv
import io
import urllib.request
import urllib.parse

GAIA_TAP_URL = "https://gea.esac.esa.int/tap-server/tap/sync"
QUERY = (
    "SELECT TOP 100 source_id, parallax "
    "FROM gaiadr3.gaia_source "
    "WHERE parallax > 10 AND parallax_error/parallax < 0.1 "
    "ORDER BY parallax DESC"
)

params = urllib.parse.urlencode({
    "REQUEST": "doQuery",
    "LANG": "ADQL",
    "FORMAT": "csv",
    "QUERY": QUERY,
})

with urllib.request.urlopen(f"{GAIA_TAP_URL}?{params}") as resp:
    raw = resp.read().decode()

reader = csv.DictReader(io.StringIO(raw))
with open("distances.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["source_id", "distance_pc"])
    writer.writeheader()
    for star in reader:
        distance_pc = 1000.0 / float(star["parallax"])
        writer.writerow({"source_id": star["source_id"], "distance_pc": f"{distance_pc:.4f}"})

print("Done — wrote distances.csv")
