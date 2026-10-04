import csv
from pathlib import Path
import unittest

from part3_narrative.masking import alias_for, assert_no_raw_names_leak


PART3_DIR = Path(__file__).resolve().parent
PROJECT_DIR = PART3_DIR.parents[1]


class MaskingTests(unittest.TestCase):
    def test_alias_format(self):
        self.assertEqual(alias_for("RS019"), "ALIAS-19")
        self.assertEqual(alias_for("RS006"), "ALIAS-06")

    def test_final_report_does_not_expose_raw_reseller_names(self):
        report_path = PART3_DIR / "narrative_report.md"
        reseller_path = PROJECT_DIR / "Part 1" / "data" / "resellers.csv"
        report = report_path.read_text(encoding="utf-8")
        with reseller_path.open(newline="", encoding="utf-8") as reseller_file:
            reseller_names = [row["reseller_name"] for row in csv.DictReader(reseller_file)]

        self.assertTrue(assert_no_raw_names_leak(report, reseller_names))

    def test_raw_name_is_detected(self):
        self.assertFalse(
            assert_no_raw_names_leak(
                "Mumbai Reseller 1 is among the leaders.", ["Mumbai Reseller 1"]
            )
        )