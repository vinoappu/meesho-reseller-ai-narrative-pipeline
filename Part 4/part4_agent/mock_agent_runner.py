import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PART2_DIR = PROJECT_ROOT / "Part 2"
PART3_DIR = PROJECT_ROOT / "Part 3"
for module_dir in (str(PART2_DIR), str(PART3_DIR)):
    if module_dir not in sys.path:
        sys.path.insert(0, module_dir)

from part2_engine.growth_engine import is_flagged, mom_growth, validate_feed
from part3_narrative.template_fill import fill_prompt_pack


OUTPUT_KEYS = (
    "run_month",
    "validation_status",
    "validation_errors",
    "flagged_categories",
    "suppressed_categories",
    "escalated_categories",
    "action_taken",
)
MAX_DRAFTS = 3


def _read_feed(csv_path: str) -> list[dict[str, str]]:
    with open(csv_path, newline="", encoding="utf-8") as feed:
        return list(csv.DictReader(feed))


def _previous_month(month: str) -> str:
    month_names = (
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December",
    )
    try:
        index = month_names.index(month)
    except ValueError as error:
        raise ValueError(f"Unknown run month: {month}") from error
    return month_names[(index - 1) % len(month_names)]


def _month_rows(rows: list[dict[str, str]], month: str) -> dict[str, dict[str, str]]:
    return {
        row["category"]: row
        for row in rows
        if row.get("month") == month and row.get("category")
    }


def _result(
    month: str,
    validation_status: str,
    validation_errors: list[str],
    flagged_categories: list[dict[str, Any]],
    suppressed_categories: list[str],
    escalated_categories: list[str],
    action_taken: str,
) -> dict[str, Any]:
    result = {
        "run_month": month,
        "validation_status": validation_status,
        "validation_errors": validation_errors,
        "flagged_categories": flagged_categories,
        "suppressed_categories": suppressed_categories,
        "escalated_categories": escalated_categories,
        "action_taken": action_taken,
    }
    assert tuple(result) == OUTPUT_KEYS
    return result


def run(month: str, previous_month_csv: str, current_month_csv: str) -> dict[str, Any]:
    """Validate both feeds, compare category revenue, and return held message drafts."""
    previous_valid, previous_errors = validate_feed(previous_month_csv)
    current_valid, current_errors = validate_feed(current_month_csv)
    validation_errors = previous_errors + current_errors

    if not previous_valid or not current_valid:
        return _result(
            month, "invalid", validation_errors, [], [], [], "hard_stop"
        )

    previous_name = _previous_month(month)
    previous_rows = _month_rows(_read_feed(previous_month_csv), previous_name)
    current_rows = _month_rows(_read_feed(current_month_csv), month)
    if not previous_rows:
        validation_errors.append(f"no revenue rows found for previous month={previous_name}")
    if not current_rows:
        validation_errors.append(f"no revenue rows found for run month={month}")

    categories = sorted(set(previous_rows) | set(current_rows))
    for category in categories:
        if category not in previous_rows:
            validation_errors.append(
                f"missing previous-month revenue (month={previous_name}, category={category})"
            )
        elif category not in current_rows:
            validation_errors.append(
                f"missing current-month revenue (month={month}, category={category})"
            )

    if validation_errors:
        return _result(
            month, "invalid", validation_errors, [], [], [], "hard_stop"
        )

    flagged: list[dict[str, Any]] = []
    escalated: list[str] = []
    for category in categories:
        previous_revenue_text = previous_rows[category]["revenue"]
        current_revenue_text = current_rows[category]["revenue"]
        mom_pct = mom_growth(float(previous_revenue_text), float(current_revenue_text))
        status = is_flagged(mom_pct)

        if status == "escalate_exact_boundary":
            escalated.append(category)
        elif status == "flagged":
            flagged.append(
                {
                    "category": category,
                    "mom_pct": mom_pct,
                    "previous_revenue": float(previous_revenue_text),
                    "current_revenue": float(current_revenue_text),
                    "drafted": False,
                }
            )

    flagged.sort(key=lambda item: (-abs(item["mom_pct"]), item["category"]))
    suppressed = [item["category"] for item in flagged[MAX_DRAFTS:]]
    for item in flagged[:MAX_DRAFTS]:
        item["drafted"] = True
        item["message"] = fill_prompt_pack(
            category=item["category"],
            previous_revenue=str(item["previous_revenue"]),
            current_revenue=str(item["current_revenue"]),
            mom_pct=item["mom_pct"],
            month=month,
            prev_month=previous_name,
        )

    return _result(
        month,
        "valid",
        [],
        flagged,
        suppressed,
        escalated,
        "drafted_and_held_for_approval",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the guarded Meesho mock monitoring agent.")
    parser.add_argument("month", help="Current month to evaluate, such as May")
    parser.add_argument("previous_month_csv")
    parser.add_argument("current_month_csv")
    args = parser.parse_args()
    print(json.dumps(run(args.month, args.previous_month_csv, args.current_month_csv), indent=2))


if __name__ == "__main__":
    main()