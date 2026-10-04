def fill_prompt_pack(
    category: str,
    previous_revenue: str,
    current_revenue: str,
    mom_pct: float,
    month: str,
    prev_month: str,
) -> str:
    return (
        f"Context: {category} revenue is being compared for {month} vs. {prev_month}.\n"
        f"Insight (fact): Revenue changed by {mom_pct}% "
        f"(from {previous_revenue} to {current_revenue}).\n"
        "Implication (hypothesis): Check category inventory availability and campaign "
        f"activity across {prev_month} and {month} before changing stock or promotion plans; "
        "either may help explain the movement, but the supplied revenue figures do not "
        "establish a cause."
    )