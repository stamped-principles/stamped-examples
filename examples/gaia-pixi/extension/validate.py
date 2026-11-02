"""Check nonlinear interval propagation against independent expectations."""
import unittest
from pathlib import Path
import tempfile
import json

import numpy as np
from scipy.stats import norm

from estimate_distances import analyze, distance_interval, read_rows


def assert_equivalent(actual, expected):
    """Compare saved scientific results, allowing platform-level roundoff."""
    if isinstance(expected, dict):
        assert actual.keys() == expected.keys()
        for key in expected:
            if key == "source_id":
                assert actual[key] == expected[key]
            else:
                assert_equivalent(actual[key], expected[key])
    elif isinstance(expected, list):
        assert len(actual) == len(expected)
        for left, right in zip(actual, expected):
            assert_equivalent(left, right)
    elif isinstance(expected, bool) or expected is None:
        assert actual == expected
    else:
        try:
            left, right = float(actual), float(expected)
        except (TypeError, ValueError):
            assert actual == expected
        else:
            np.testing.assert_allclose(left, right, rtol=1e-9, atol=0)


class Intervals(unittest.TestCase):
    def test_saved_result_comparison_allows_roundoff_but_rejects_changes(self):
        assert_equivalent({"distance_pc": "10.000000001"}, {"distance_pc": "10"})
        with self.assertRaises(AssertionError):
            assert_equivalent({"distance_pc": "10.0001"}, {"distance_pc": "10"})
        with self.assertRaises(AssertionError):
            assert_equivalent({"source_id": "123456789012345678"},
                              {"source_id": "123456789012345679"})

    def test_one_sigma_transform(self):
        probability = norm.cdf(1) - norm.cdf(-1)
        point, lo, hi = distance_interval(10, 1, probability)
        np.testing.assert_allclose([point, lo, hi], [100, 1000 / 11, 1000 / 9])
        self.assertGreater(hi - point, point - lo)

    def test_small_error_linear_limit(self):
        point, lo, hi = distance_interval(10, .0001, norm.cdf(1) - norm.cdf(-1))
        np.testing.assert_allclose([point - lo, hi - point], [.001, .001], rtol=2e-5)

    def test_coverage_under_gaussian_measurement_model(self):
        rng = np.random.default_rng(42)
        measurements = rng.normal(10, 1, 100000)
        _, lo, hi = distance_interval(measurements, np.ones_like(measurements))
        coverage = np.mean((lo <= 100) & (100 <= hi))
        self.assertLess(abs(coverage - .68), .006)

    def test_rejects_duplicate_ids_and_mismatched_samples(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            duplicate = root / "duplicate.csv"
            duplicate.write_text("source_id,parallax\n1,10\n1,11\n")
            with self.assertRaisesRegex(ValueError, "Duplicate"):
                read_rows(duplicate)
            raw, catalog, original = [root / name for name in ("raw.csv", "extra.csv", "original.csv")]
            raw.write_text("source_id,parallax\n1,10\n")
            catalog.write_text("source_id,parallax\n2,10\n")
            original.write_text("source_id,distance_pc\n1,100\n")
            with self.assertRaisesRegex(ValueError, "same sample"):
                analyze(raw, catalog, original, root / "out.csv", root / "summary.json")

    def test_rejects_unbounded_or_invalid_intervals(self):
        for p, e in [(0, 1), (-1, 1), (10, 0), (10, -1), (np.nan, 1), (10, np.inf)]:
            with self.subTest(p=p, e=e), self.assertRaises(ValueError):
                distance_interval(p, e)


class SavedProject(unittest.TestCase):
    def test_baseline_reuses_original_calculation(self):
        self.assertEqual(Path("output/distances.csv").read_bytes(),
                         Path("inputs/gaia/output/distances.csv").read_bytes())

    def test_saved_intervals_reproduce(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            analyze("inputs/gaia/raw/gaia_nearby.csv", "raw/gaia_uncertainties.csv",
                    "output/distances.csv", root / "intervals.csv", root / "summary.json")
            assert_equivalent(read_rows(root / "intervals.csv"),
                              read_rows("output/distance_intervals.csv"))
            assert_equivalent(json.loads((root / "summary.json").read_text()),
                              json.loads(Path("output/distance_summary.json").read_text()))


if __name__ == "__main__":
    unittest.main()
