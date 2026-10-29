"""Transform Gaussian parallax confidence intervals into distance intervals.

This extends the original inverse-parallax estimate, not a Bayesian estimator.
It includes random parallax error only, not zero-point or other systematics.
"""
import csv
import json
from pathlib import Path

import numpy as np
from scipy.stats import norm


def distance_interval(parallax, error, probability=0.68):
    """Invert a central Gaussian confidence set where both endpoints are positive."""
    p, e = np.asarray(parallax, dtype=float), np.asarray(error, dtype=float)
    if not 0 < probability < 1:
        raise ValueError("Probability must be between zero and one")
    z = norm.ppf((1 + probability) / 2)
    if np.any(~np.isfinite(p)) or np.any(~np.isfinite(e)) or np.any(e <= 0) or np.any(p <= z * e):
        raise ValueError("Need finite positive errors and a positive lower parallax bound")
    return 1000 / p, 1000 / (p + z * e), 1000 / (p - z * e)


def read_rows(path):
    with Path(path).open() as stream:
        rows = list(csv.DictReader(stream))
    keyed = {row["source_id"]: row for row in rows}
    if len(keyed) != len(rows):
        raise ValueError(f"Duplicate source IDs in {path}")
    return keyed


def analyze(raw, catalog, original, output, summary):
    baseline, extra, computed = map(read_rows, (raw, catalog, original))
    if not baseline or set(baseline) != set(extra) or set(baseline) != set(computed):
        raise ValueError("Saved data and estimates must cover the same sample exactly")
    results = []
    for sid in sorted(baseline, key=int):
        p = float(baseline[sid]["parallax"])
        row = extra[sid]
        if not np.isclose(float(row["parallax"]), p, rtol=1e-10, atol=1e-10):
            raise ValueError(f"Parallax snapshot differs for {sid}")
        point, lower, upper = distance_interval(p, float(row["parallax_error"]))
        old = float(computed[sid]["distance_pc"])
        if abs(old - point) > 0.000051:
            raise ValueError(f"Original distance is inconsistent for {sid}")
        result = dict(source_id=sid, original_pc=old, distance_pc=float(point),
                      lower_pc=float(lower), upper_pc=float(upper),
                      fractional_parallax_error=float(row["parallax_error"]) / p)
        for field in ("distance_gspphot", "distance_gspphot_lower", "distance_gspphot_upper"):
            result[field] = row[field]
        if row["distance_gspphot"].strip():
            ref, lo, hi = [float(row[f]) for f in
                           ("distance_gspphot", "distance_gspphot_lower", "distance_gspphot_upper")]
            if not np.isfinite([ref, lo, hi]).all() or not 0 < lo <= ref <= hi:
                raise ValueError(f"Invalid GSP-Phot interval for {sid}")
            result["reference_offset_pct"] = 100 * (ref / point - 1)
        else:
            result["reference_offset_pct"] = ""
        results.append(result)
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    with Path(output).open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)
    matched = [r for r in results if r["reference_offset_pct"] != ""]
    report = {"sources": len(results), "with_reference": len(matched),
              "without_reference": len(results) - len(matched), "interval_probability": 0.68,
              "method": "inverted central Gaussian parallax confidence interval",
              "systematics_included": False,
              "largest_offsets": sorted(matched, key=lambda r: abs(r["reference_offset_pct"]), reverse=True)[:8]}
    Path(summary).write_text(json.dumps(report, indent=2) + "\n")
    print(f"Estimated {len(results)} intervals; {len(matched)} GSP-Phot comparisons")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("raw", "catalog", "original", "output", "summary"):
        parser.add_argument(name)
    args = parser.parse_args()
    analyze(args.raw, args.catalog, args.original, args.output, args.summary)
