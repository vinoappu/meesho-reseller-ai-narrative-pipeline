import csv


def mom_growth(previous: float, current: float) -> float:
    return round((current - previous) / previous * 100, 2)


def is_flagged(mom_pct: float, threshold: float = 8.0) -> str:
    if abs(mom_pct) == threshold:
        return "escalate_exact_boundary"
    if abs(mom_pct) > threshold:
        return "flagged"
    return "not_flagged"


def validate_feed(csv_path: str) -> tuple[bool, list[str]]:
    errors: list[str] = []

    with open(csv_path, newline="", encoding="utf-8") as feed:
        reader = csv.DictReader(feed)
        for line_number, row in enumerate(reader, start=2):
            month = row.get("month") or ""
            category = row.get("category") or ""
            revenue = row.get("revenue") or ""

            if not category.strip():
                errors.append(f"line {line_number}: missing category (month={month})")

            if not revenue.strip():
                errors.append(f"line {line_number}: missing revenue (category={category})")
                continue

            try:
                revenue_value = float(revenue)
            except ValueError:
                errors.append(f"line {line_number}: revenue not numeric: {revenue!r}")
                continue

            if revenue_value < 0:
                errors.append(
                    f"line {line_number}: negative revenue ({revenue_value}) for category={category}"
                )

    return (not errors, errors)