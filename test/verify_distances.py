#!/usr/bin/env python3
"""Compare our computed distances against Gaia GSP-Phot reference distances."""

import csv
import sys


def main():
    computed = {}
    with open("output/distances.csv") as f:
        for row in csv.DictReader(f):
            computed[row["source_id"]] = float(row["distance_pc"])

    reference = {}
    with open("test/reference_distances.csv") as f:
        for row in csv.DictReader(f):
            reference[row["source_id"]] = float(row["distance_gspphot"])

    matched = set(computed) & set(reference)
    if not matched:
        print("ERROR: no matching source_ids between computed and reference")
        sys.exit(1)

    max_pct_err = 0
    failures = []
    for sid in sorted(matched):
        c = computed[sid]
        r = reference[sid]
        pct_err = abs(c - r) / r * 100
        max_pct_err = max(max_pct_err, pct_err)
        if pct_err > 0.5:
            failures.append((sid, c, r, pct_err))

    print(f"Compared {len(matched)} stars")
    print(f"Max error: {max_pct_err:.2f}%")

    if failures:
        print(f"\nFAILED: {len(failures)} stars differ by >0.5%:")
        for sid, c, r, pct in failures:
            print(f"  {sid}: computed={c:.4f} ref={r:.4f} err={pct:.1f}%")
        sys.exit(1)
    else:
        print("PASSED: all within 0.5%")


if __name__ == "__main__":
    main()
