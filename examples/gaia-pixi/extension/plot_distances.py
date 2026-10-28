"""Plot saved numerical results without importing the scientific-analysis stack."""
import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D


def plot(source, destination):
    with Path(source).open() as stream:
        rows = list(csv.DictReader(stream))
    matched = [r for r in rows if r["reference_offset_pct"] != ""]
    if not matched:
        raise ValueError("No GSP-Phot comparisons to plot")
    chosen = sorted(matched, key=lambda r: abs(float(r["reference_offset_pct"])), reverse=True)[:8]
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "axes.titleweight": "bold", "savefig.facecolor": "#f7f8fa"})
    fig = plt.figure(figsize=(14, 10), facecolor="#f7f8fa", layout="constrained")
    grid = fig.add_gridspec(2, 2, height_ratios=[1, 1.45])
    ax = fig.add_subplot(grid[0, 0])
    point = np.array([float(r["distance_pc"]) for r in matched])
    offset = np.array([float(r["reference_offset_pct"]) for r in matched])
    ax.axhline(0, color="#263447", lw=1)
    ax.scatter(point, offset, c="#c76632", s=35, alpha=.8, edgecolors="white", linewidth=.5)
    for row in chosen[:3]:
        ax.annotate(row["source_id"][-6:], (float(row["distance_pc"]), float(row["reference_offset_pct"])),
                    xytext=(5, 5), textcoords="offset points", fontsize=9)
    ax.set(xlabel="Original inverse-parallax distance (pc)", ylabel="GSP-Phot difference (%)",
           title=f"A  /  {len(matched)} reference estimates: close, but not identical")
    ax.grid(alpha=.15)
    ax = fig.add_subplot(grid[0, 1])
    fraction = np.array([float(r["fractional_parallax_error"]) for r in rows])
    asymmetry = np.array([(float(r["upper_pc"]) - float(r["distance_pc"])) /
                         (float(r["distance_pc"]) - float(r["lower_pc"])) for r in rows])
    ax.scatter(fraction * 100, asymmetry, color="#287b91", s=25, alpha=.8)
    ax.axhline(1, color="#263447", ls=":", lw=1)
    ax.set(xlabel="Parallax uncertainty / parallax (%)", ylabel="Upper / lower distance error",
           title="B  /  Nonlinear propagation produces asymmetry")
    ax.grid(alpha=.15)
    ax = fig.add_subplot(grid[1, :])
    for i, row in enumerate(chosen):
        p = float(row["distance_pc"])
        transform = lambda name: 100 * (float(row[name]) / p - 1)
        lo, hi = transform("lower_pc"), transform("upper_pc")
        ax.errorbar(0, i - .13, xerr=np.array([[-lo], [hi]]), fmt="o", color="#287b91",
                    capsize=4, lw=2, markersize=5)
        r, rl, ru = (transform(k) for k in ("distance_gspphot", "distance_gspphot_lower", "distance_gspphot_upper"))
        ax.errorbar(r, i + .13, xerr=np.array([[r - rl], [ru - r]]), fmt="D",
                    color="#c76632", capsize=4, lw=2, markersize=5)
        ax.plot(transform("original_pc"), i - .13, "|", color="#263447", ms=14, mew=1.5)
    ax.axvline(0, color="#263447", lw=1, alpha=.5)
    ax.set_yticks(range(len(chosen)), [r["source_id"] for r in chosen])
    ax.invert_yaxis()
    ax.set(xlabel="Difference from the unrounded inverse-parallax estimate (%)", ylabel="Gaia DR3 source ID",
           title="C  /  The eight largest absolute differences, with uncertainty intervals")
    ax.grid(axis="x", alpha=.15)
    ax.legend(handles=[Line2D([], [], marker="|", ls="", color="#263447", markersize=12, label="Original point estimate"),
                       Line2D([], [], marker="o", color="#287b91", label="Extended: propagated 68% interval"),
                       Line2D([], [], marker="D", color="#c76632", label="GSP-Phot: 16th–84th percentiles")],
              loc="lower right", fontsize=9, framealpha=.95)
    fig.suptitle("From a point estimate to an uncertainty-aware comparison", fontsize=20, weight="bold")
    fig.supxlabel(f"{len(rows)} saved stars · {len(rows)-len(matched)} without GSP-Phot estimates · "
                  "Random parallax errors only; estimates share inputs, so differences are not independent tests.", fontsize=10)
    target = Path(destination)
    target.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(target.with_suffix(".png"), dpi=180)
    fig.savefig(target.with_suffix(".svg"))
    plt.close(fig)
    print(f"Saved {target.with_suffix('.png')} and SVG")


if __name__ == "__main__":
    plot("output/distance_intervals.csv", "figures/distance_comparison")
