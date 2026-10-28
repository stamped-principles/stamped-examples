"""Exercise the walkthrough's partial-coverage and stale-reference checks."""
import re
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize(
    "computed,reference,expected_code,expected_message",
    [
        ("1,10\n2,20\n", "1,10\n2,\n", 0,
         "Computed: 2; matched: 1; unmatched: 1"),
        ("1,10\n2,20\n3,30\n", "1,10\n2,\n", 1, "different sample"),
        ("1,10\n3,30\n", "1,10\n2,\n", 1, "different sample"),
        ("1,10\n", "1,\n", 1, "no matching source_ids"),
        ("1,11\n", "1,10\n", 1, "differ by >0.5%"),
    ],
)
def test_reference_coverage(tmp_path, computed, reference, expected_code, expected_message):
    page = (Path(__file__).resolve().parents[1] / "content/examples/"
            "pixi-stellar-distance-walkthrough.md").read_text()
    baseline = Path(__file__).resolve().parents[1] / "examples/gaia-pixi/gaia"
    script = (baseline / "test/verify_distances.py").read_text()
    fetch = (baseline / "test/fetch_reference_distances.sh").read_text()
    patch = re.search(r"# snippet: reference-patch\n(.*?)\n# /snippet", page, re.S).group(1)
    (tmp_path / "output").mkdir()
    (tmp_path / "test").mkdir()
    (tmp_path / "output/distances.csv").write_text(
        "source_id,distance_pc\n" + computed
    )
    (tmp_path / "test/reference_distances.csv").write_text(
        "source_id,distance_gspphot\n" + reference
    )
    (tmp_path / "test/verify_distances.py").write_text(script)
    (tmp_path / "test/fetch_reference_distances.sh").write_text(fetch)
    (tmp_path / "pyproject.toml").write_text(
        'cmd = "sh test/fetch_reference_distances.sh"\n'
    )
    (tmp_path / ".gitignore").write_text("test/reference_distances.csv\n")
    subprocess.run([sys.executable, "-c", patch], cwd=tmp_path, check=True)
    result = subprocess.run(
        [sys.executable, "test/verify_distances.py"], cwd=tmp_path, capture_output=True, text=True
    )
    assert result.returncode == expected_code, result.stderr
    assert expected_message in result.stdout


def test_setup_preserves_project_and_matches_display(tmp_path, monkeypatch):
    """Keep the migration and displayed complete manifest in agreement."""
    import runpy
    import tomlkit

    root = Path(__file__).resolve().parents[1]
    manifest = (root / "examples/gaia-pixi/gaia/pyproject.toml").read_text()
    (tmp_path / "pyproject.toml").write_text(manifest)
    (tmp_path / ".gitignore").write_text("test/reference_distances.csv\n")
    (tmp_path / "README.md").write_text("    make\n    make test\n")
    (tmp_path / "test").mkdir()
    fetch = tmp_path / "test/fetch_reference_distances.sh"
    fetch.write_text("ids=$(cat sample.csv | paste -sd,)\n")
    for name in ("Makefile", "requirements.txt"):
        (tmp_path / name).write_text("old setup\n")
    monkeypatch.chdir(tmp_path)
    runpy.run_path(str(root / "examples/gaia-pixi/migrate-gaia-to-pixi.py"))["migrate"]()
    result = (tmp_path / "pyproject.toml").read_text()
    assert tomlkit.parse(result)["project"] == tomlkit.parse(manifest)["project"]
    assert result == (root / "examples/gaia-pixi/pyproject.expected.toml").read_text()
    assert fetch.read_text() == "ids=$(cat sample.csv | paste -sd,)\n"
    assert not (tmp_path / "Makefile").exists()
    assert not (tmp_path / "requirements.txt").exists()


def test_prepare_preserves_baseline_and_records_provenance(tmp_path):
    import hashlib
    import json
    import runpy

    root = Path(__file__).resolve().parents[1]
    bundle = root / "examples/gaia-pixi"
    script = bundle / "migrate-gaia-to-pixi.py"
    baseline = bundle / "gaia"
    output = tmp_path / "analysis"
    before = subprocess.check_output(["git", "-C", str(baseline), "rev-parse", "HEAD"], text=True).strip()
    prepare = runpy.run_path(str(script))["prepare"]
    prepare(baseline, output)
    assert subprocess.check_output(
        ["git", "-C", str(output), "rev-parse", "HEAD"], text=True
    ).strip() == before
    provenance = json.loads((output / "pixi-source.json").read_text())
    assert provenance["gaia_commit"] == before
    assert provenance["migration_sha256"] == hashlib.sha256(script.read_bytes()).hexdigest()
    assert (output / script.name).read_bytes() == script.read_bytes()
    assert (baseline / "Makefile").is_file()
    assert not (output / "Makefile").exists()
    assert not subprocess.check_output(["git", "-C", str(baseline), "status", "--porcelain"])
    with pytest.raises(SystemExit, match="already exists"):
        prepare(baseline, output)
