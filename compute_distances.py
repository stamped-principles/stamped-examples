#!/usr/bin/env python3
"""Compute stellar distances from Gaia parallax measurements."""

import csv
import sys


def main(input_path, output_path):
    with open(input_path) as f:
        reader = csv.DictReader(f)
        stars = list(reader)

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["source_id", "distance_pc"])
        writer.writeheader()
        for star in stars:
            distance_pc = 1000.0 / float(star["parallax"])
            writer.writerow({
                "source_id": star["source_id"],
                "distance_pc": f"{distance_pc:.4f}",
            })

    print(f"Computed distances for {len(stars)} stars -> {output_path}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
