"""Record each extension task with its explicit Pixi environment and file inputs."""
import subprocess
import sys

STAGES = {
    "analysis": ("estimate_distances.py",
                 ["raw/gaia_nearby.csv", "raw/gaia_uncertainties.csv", "output/distances.csv"],
                 ["output/distance_intervals.csv", "output/distance_summary.json"]),
    "plotting": ("plot_distances.py", ["output/distance_intervals.csv"],
                 ["figures/distance_comparison.png", "figures/distance_comparison.svg"]),
}


def record(stage):
    script, inputs, outputs = STAGES[stage]
    script = "code/extension/" + script
    command = ["datalad", "run", "--explicit", "--sidecar", "yes", "-m", f"Gaia {stage}"]
    for path in [*inputs, script, "code/extension/record.py", "pyproject.toml", "pixi.lock"]:
        command.extend(["-i", path])
    for path in outputs:
        command.extend(["-o", path])
    command.extend(["--", "pixi", "run", "--environment", stage, "--locked", "--", "python", script])
    subprocess.run(command, check=True)


if __name__ == "__main__":
    record(sys.argv[1])
