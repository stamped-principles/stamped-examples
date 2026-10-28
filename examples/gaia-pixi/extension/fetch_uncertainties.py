"""Retrieve DR3 errors and GSP-Phot intervals for the saved Gaia sample."""
import csv
import io
from pathlib import Path

import requests

FIELDS = ["source_id", "parallax", "parallax_error", "distance_gspphot",
          "distance_gspphot_lower", "distance_gspphot_upper"]


def fetch(baseline, output):
    with Path(baseline).open() as stream:
        ids = [row["source_id"] for row in csv.DictReader(stream)]
    if not ids or any(not sid.isdigit() for sid in ids):
        raise ValueError("Expected Gaia source IDs")
    response = requests.get(
        "https://gea.esac.esa.int/tap-server/tap/sync",
        params={"REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": "csv",
                "QUERY": f"SELECT {', '.join(FIELDS)} FROM gaiadr3.gaia_source "
                         f"WHERE source_id IN ({','.join(ids)})"}, timeout=120,
    )
    response.raise_for_status()
    rows = list(csv.DictReader(io.StringIO(response.text)))
    if len(rows) != len(ids) or {r["source_id"] for r in rows} != set(ids):
        raise ValueError("The response does not cover the saved sample exactly")
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(sorted(rows, key=lambda r: int(r["source_id"])))
    print(f"Saved {len(rows)} sources to {target}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline")
    parser.add_argument("output")
    args = parser.parse_args()
    fetch(args.baseline, args.output)
