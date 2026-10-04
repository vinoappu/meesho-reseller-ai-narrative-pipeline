from pathlib import Path
import unittest
import csv

from part2_engine.growth_engine import is_flagged, mom_growth, validate_feed


ENGINE_DIR = Path(__file__).resolve().parent


class GrowthEngineTests(unittest.TestCase):
    def test_may_vs_april_growth_table(self):
        # GIVEN monthly category revenue values from the Part 1 report
        monthly_revenue = self._load_monthly_revenue()
        expected = {
            "Ethnic Wear": (77.1, "flagged"),
            "Western Wear": (-23.6, "flagged"),
            "Kids Wear": (-23.48, "flagged"),
            "Home & Kitchen": (-9.25, "flagged"),
            "Beauty & Personal Care": (-12.75, "flagged"),
        }

        # WHEN each May value is compared with April
        actual = {
            category: (
                mom_growth(monthly_revenue[("April", category)], monthly_revenue[("May", category)]),
                is_flagged(
                    mom_growth(
                        monthly_revenue[("April", category)],
                        monthly_revenue[("May", category)],
                    )
                ),
            )
            for category in expected
        }

        # THEN every category matches the requested May table
        self.assertEqual(actual, expected)

    def test_june_vs_may_growth_table(self):
        # GIVEN monthly category revenue values from the Part 1 report
        monthly_revenue = self._load_monthly_revenue()
        expected = {
            "Ethnic Wear": (-58.74, "flagged"),
            "Western Wear": (11.97, "flagged"),
            "Kids Wear": (23.9, "flagged"),
            "Home & Kitchen": (42.59, "flagged"),
            "Beauty & Personal Care": (5.67, "not_flagged"),
        }

        # WHEN each June value is compared with May
        actual = {
            category: (
                mom_growth(monthly_revenue[("May", category)], monthly_revenue[("June", category)]),
                is_flagged(
                    mom_growth(
                        monthly_revenue[("May", category)],
                        monthly_revenue[("June", category)],
                    )
                ),
            )
            for category in expected
        }

        # THEN exactly four categories are flagged in June
        self.assertEqual(actual, expected)
        self.assertEqual(sum(status == "flagged" for _, status in actual.values()), 4)

    def test_april_to_may_ethnic_wear_growth_is_flagged(self):
        # GIVEN April-to-May Ethnic Wear revenue values
        previous, current = 104520.77, 185107.61

        # WHEN growth and its status are evaluated
        growth = mom_growth(previous, current)

        # THEN growth is 77.1% and is flagged
        self.assertEqual(growth, 77.1)
        self.assertEqual(is_flagged(growth), "flagged")

    def test_may_to_june_beauty_growth_is_not_flagged(self):
        # GIVEN May-to-June Beauty & Personal Care revenue values
        previous, current = 35542.11, 37559.07

        # WHEN growth and its status are evaluated
        growth = mom_growth(previous, current)

        # THEN growth is 5.67% and is not flagged
        self.assertEqual(growth, 5.67)
        self.assertEqual(is_flagged(growth), "not_flagged")

    def test_growth_exactly_on_threshold_escalates(self):
        # GIVEN a pair whose growth is exactly the 8% threshold
        previous, current = 100000, 108000

        # WHEN growth and its status are evaluated
        growth = mom_growth(previous, current)

        # THEN the exact-boundary case receives its own status
        self.assertEqual(growth, 8.0)
        self.assertEqual(is_flagged(growth), "escalate_exact_boundary")

    def test_corrupted_feed_returns_ordered_guardrail_errors(self):
        # GIVEN the corrupted feed fixture
        feed_path = ENGINE_DIR / "fixtures" / "corrupted_feed.csv"

        # WHEN the feed is validated
        result = validate_feed(str(feed_path))

        # THEN all three errors are returned in data-row order
        self.assertEqual(
            result,
            (
                False,
                [
                    "line 3: negative revenue (-4200.0) for category=Western Wear",
                    "line 4: missing category (month=July)",
                    "line 6: missing revenue (category=Home & Kitchen)",
                ],
            ),
        )

    def test_part_one_monthly_revenue_feed_is_valid(self):
        # GIVEN the Part 1 monthly category revenue report
        feed_path = (
            ENGINE_DIR.parents[1]
            / "Part 1"
            / "part1_sql"
            / "output"
            / "monthly_category_revenue.csv"
        )

        # WHEN the feed is validated directly from its Part 1 path
        result = validate_feed(str(feed_path))

        # THEN there are no input guardrail errors
        self.assertEqual(result, (True, []))

    def test_nonnumeric_revenue_is_reported(self):
        # GIVEN a CSV row whose revenue is not numeric
        feed_path = ENGINE_DIR / "fixtures" / "nonnumeric_revenue.csv"

        # WHEN the feed is validated
        result = validate_feed(str(feed_path))

        # THEN the invalid revenue is reported with its original representation
        self.assertEqual(result, (False, ["line 2: revenue not numeric: 'unknown'"]))

    @staticmethod
    def _load_monthly_revenue():
        feed_path = (
            ENGINE_DIR.parents[1]
            / "Part 1"
            / "part1_sql"
            / "output"
            / "monthly_category_revenue.csv"
        )
        with feed_path.open(newline="", encoding="utf-8") as feed:
            return {
                (row["month"], row["category"]): float(row["revenue"])
                for row in csv.DictReader(feed)
            }
