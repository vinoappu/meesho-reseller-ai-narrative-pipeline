import csv
import json
from pathlib import Path
import tempfile
import unittest

from part4_agent.mock_agent_runner import OUTPUT_KEYS, run


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MONTHLY_FEED = (
    PROJECT_ROOT
    / "Part 1"
    / "part1_sql"
    / "output"
    / "monthly_category_revenue.csv"
)
CORRUPTED_FEED = (
    PROJECT_ROOT / "Part 2" / "part2_engine" / "fixtures" / "corrupted_feed.csv"
)


class MockAgentRunnerTests(unittest.TestCase):
    def test_may_scenario_drafts_top_three_and_suppresses_two(self):
        # GIVEN the validated Part 1 monthly feed
        # WHEN the agent runs May against April
        result = run("May", str(MONTHLY_FEED), str(MONTHLY_FEED))

        # THEN the top three flagged categories are drafted and two are suppressed
        self.assertEqual(tuple(result), OUTPUT_KEYS)
        self.assertEqual(result["validation_status"], "valid")
        self.assertEqual(
            [(item["category"], item["mom_pct"], item["drafted"]) for item in result["flagged_categories"]],
            [
                ("Ethnic Wear", 77.1, True),
                ("Western Wear", -23.6, True),
                ("Kids Wear", -23.48, True),
                ("Beauty & Personal Care", -12.75, False),
                ("Home & Kitchen", -9.25, False),
            ],
        )
        self.assertEqual(
            set(result["suppressed_categories"]),
            {"Beauty & Personal Care", "Home & Kitchen"},
        )
        self.assertEqual(result["escalated_categories"], [])
        self.assertEqual(
            sum(item["drafted"] for item in result["flagged_categories"]), 3
        )
        self._assert_messages_are_grounded(result)

    def test_june_scenario_drafts_top_three_and_suppresses_one(self):
        # GIVEN the validated Part 1 monthly feed
        # WHEN the agent runs June against May
        result = run("June", str(MONTHLY_FEED), str(MONTHLY_FEED))

        # THEN the top three are drafted, one is suppressed, and beauty is unflagged
        self.assertEqual(result["validation_status"], "valid")
        self.assertEqual(
            [(item["category"], item["mom_pct"], item["drafted"]) for item in result["flagged_categories"]],
            [
                ("Ethnic Wear", -58.74, True),
                ("Home & Kitchen", 42.59, True),
                ("Kids Wear", 23.9, True),
                ("Western Wear", 11.97, False),
            ],
        )
        self.assertEqual(result["suppressed_categories"], ["Western Wear"])
        self.assertNotIn(
            "Beauty & Personal Care",
            [item["category"] for item in result["flagged_categories"]],
        )
        self.assertNotIn("Beauty & Personal Care", result["suppressed_categories"])
        self.assertEqual(result["escalated_categories"], [])
        self._assert_messages_are_grounded(result)

    def test_corrupted_current_feed_hard_stops_without_analysis(self):
        # GIVEN a corrupted current-month feed
        # WHEN the agent attempts to run May
        result = run("May", str(MONTHLY_FEED), str(CORRUPTED_FEED))

        # THEN validation errors surface and no categories are analyzed or drafted
        self.assertEqual(result["validation_status"], "invalid")
        self.assertEqual(result["action_taken"], "hard_stop")
        self.assertEqual(
            result["validation_errors"],
            [
                "line 3: negative revenue (-4200.0) for category=Western Wear",
                "line 4: missing category (month=July)",
                "line 6: missing revenue (category=Home & Kitchen)",
            ],
        )
        self.assertEqual(result["flagged_categories"], [])
        self.assertEqual(result["suppressed_categories"], [])
        self.assertEqual(result["escalated_categories"], [])

    def test_exact_boundary_is_separately_escalated(self):
        # GIVEN adjacent monthly feeds with exactly 8% category growth
        previous_path, current_path = self._create_boundary_feeds()

        # WHEN the agent evaluates the current month
        result = run("May", str(previous_path), str(current_path))

        # THEN the category is escalated, not flagged or suppressed
        self.assertEqual(result["validation_status"], "valid")
        self.assertEqual(result["flagged_categories"], [])
        self.assertEqual(result["suppressed_categories"], [])
        self.assertEqual(result["escalated_categories"], ["Boundary Category"])

    def test_valid_feed_with_no_flags_returns_valid_empty_drafts(self):
        # GIVEN adjacent months whose revenue change stays within the threshold
        previous_path, current_path = self._create_no_flag_feeds()

        # WHEN the agent evaluates the current month
        result = run("May", str(previous_path), str(current_path))

        # THEN the successful run emits empty category lists and no drafts
        self.assertEqual(result["validation_status"], "valid")
        self.assertEqual(result["flagged_categories"], [])
        self.assertEqual(result["suppressed_categories"], [])
        self.assertEqual(result["escalated_categories"], [])
        self.assertEqual(result["action_taken"], "drafted_and_held_for_approval")
        json.dumps(result)

    def _assert_messages_are_grounded(self, result):
        for item in result["flagged_categories"]:
            if item["drafted"]:
                message = item["message"]
                self.assertIn(item["category"], message)
                self.assertIn(str(item["mom_pct"]), message)
                self.assertIn(str(item["previous_revenue"]), message)
                self.assertIn(str(item["current_revenue"]), message)
                self.assertIn("held", result["action_taken"])

    def _create_boundary_feeds(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        previous_path = Path(directory.name) / "previous.csv"
        current_path = Path(directory.name) / "current.csv"
        self._write_feed(previous_path, "April", "100", "Boundary Category")
        self._write_feed(current_path, "May", "108", "Boundary Category")
        return previous_path, current_path

    def _create_no_flag_feeds(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        previous_path = Path(directory.name) / "previous.csv"
        current_path = Path(directory.name) / "current.csv"
        self._write_feed(previous_path, "April", "100", "Stable Category")
        self._write_feed(current_path, "May", "105", "Stable Category")
        return previous_path, current_path

    @staticmethod
    def _write_feed(path, month, revenue, category):
        with path.open("w", newline="", encoding="utf-8") as feed:
            writer = csv.writer(feed)
            writer.writerow(["month", "category", "revenue", "n_orders"])
            writer.writerow([month, category, revenue, "1"])


if __name__ == "__main__":
    unittest.main()