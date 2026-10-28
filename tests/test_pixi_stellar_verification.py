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
    original = (Path(__file__).resolve().parents[1] / "content/examples/"
                "stellar-distance-walkthrough.md").read_text()
    script = re.search(
        r"cat > test/verify_distances.py <<'PYEOF'\n(.*?)\nPYEOF", original, re.S
    ).group(1)
    fetch = re.search(
        r"cat > test/fetch_reference_distances.sh <<'TESTSH'\n(.*?)\nTESTSH",
        original, re.S
    ).group(1)
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
