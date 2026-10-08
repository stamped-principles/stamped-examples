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
    script = re.search(
        r"cat > test/verify_distances.py <<'PYEOF'\n(.*?)\nPYEOF", page, re.S
    ).group(1)
    (tmp_path / "output").mkdir()
    (tmp_path / "test").mkdir()
    (tmp_path / "output/distances.csv").write_text(
        "source_id,distance_pc\n" + computed
    )
    (tmp_path / "test/reference_distances.csv").write_text(
        "source_id,distance_gspphot\n" + reference
    )
    result = subprocess.run(
        [sys.executable, "-c", script], cwd=tmp_path, capture_output=True, text=True
    )
    assert result.returncode == expected_code, result.stderr
    assert expected_message in result.stdout
