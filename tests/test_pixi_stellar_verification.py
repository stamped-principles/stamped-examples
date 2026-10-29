"""Check the distributed Gaia project's boundaries and explicit provenance."""
import json
from pathlib import Path
import runpy
import subprocess
import tomllib

import pytest

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "examples/gaia-pixi"


def test_prepare_pins_reusable_input_and_public_url(tmp_path):
    baseline = BUNDLE / "gaia"
    before = subprocess.check_output(["git", "-C", str(baseline), "rev-parse", "HEAD"], text=True).strip()
    prepare = runpy.run_path(str(BUNDLE / "prepare-project.py"))["prepare"]
    output = tmp_path / "analysis"
    prepare(baseline, output)
    entry = subprocess.check_output(["git", "ls-files", "--stage", "inputs/gaia"], cwd=output, text=True)
    assert entry.startswith(f"160000 {before}")
    url = subprocess.check_output(["git", "config", "-f", ".gitmodules", "--get",
                                   "submodule.inputs/gaia.url"], cwd=output, text=True).strip()
    assert url == "https://github.com/stamped-principles/stamped-examples.git"
    provenance = json.loads((output / "source.json").read_text())
    assert provenance["gaia_commit"] == before
    assert (output / "pixi.lock").read_bytes() == (BUNDLE / "pixi.lock").read_bytes()
    assert not (output / "raw/gaia_uncertainties.csv").exists()
    assert not (output / "code/record.py").exists()
    assert (output / "inputs/gaia/Makefile").is_file()
    assert not subprocess.check_output(["git", "-C", str(baseline), "status", "--porcelain"])
    with pytest.raises(SystemExit, match="already exists"):
        prepare(baseline, output)


def test_records_expose_scripts_arguments_and_environment():
    pixi = tomllib.loads((BUNDLE / "pyproject.toml").read_text())["tool"]["pixi"]
    cases = [(pixi["tasks"]["baseline"], "default", "inputs/gaia/code/compute_distances.py"),
             (pixi["tasks"]["acquire"], "default", "code/fetch_uncertainties.py"),
             (pixi["feature"]["analysis"]["tasks"]["estimate"], "analysis", "code/estimate_distances.py"),
             (pixi["feature"]["plotting"]["tasks"]["figure"], "plotting", "code/plot_distances.py")]
    for task, environment, script in cases:
        command = task["cmd"]
        assert "datalad run --explicit --sidecar no" in command
        assert f"-- pixi run --environment {environment} --locked -- python {script} " in command
        assert f"-i {script}" in command
        assert "-i pyproject.toml -i pixi.lock" in command
        assert "-o " in command
        assert "record.py" not in command
