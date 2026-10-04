# Reusable Stakeholder Narrative Prompt Pack

## Trigger

Run this prompt only when a category's `is_flagged` result is exactly `flagged`.

## Input list

- `{category}`: flagged category name.
- `{previous_revenue}`: revenue in the prior month.
- `{current_revenue}`: revenue in the current month.
- `{mom_pct}`: calculated month-on-month percentage.
- `{prev_month}`: prior month name.
- `{month}`: current month name.

## Prompt

Write a concise update for a regional manager about **{category}**, comparing **{month} vs. {prev_month}**. Use the supplied values `{previous_revenue}`, `{current_revenue}`, and `{mom_pct}` only. Organize the response under **Context**, **Insight**, and **Implication**. State what period and measure are being compared in Context. In Insight, report `{mom_pct}` as a fact and do not introduce any other numeric value. In Implication, recommend a specific next check or action; label any proposed explanation not established by the supplied data as a hypothesis. Do not infer causes, regions, reseller identities, or operational conditions that are not supplied. Never state a number unless it exactly matches one of the supplied placeholder values. Do not expose raw reseller names; if a reseller identifier is supplied in a separate approved input, refer to it only through its approved coded alias.

## Checklist

- Does every number in the draft match a supplied placeholder value exactly?
- Is each data-backed statement labeled as a fact, and each unverified proposed cause labeled as a hypothesis?
- Does the draft explicitly name the current and prior months and the category?
- Is the recommendation specific and actionable, naming a concrete check or next step?
- Does the draft avoid unsupported causes, operational claims, and unsupplied comparisons?
- If reseller information is present, is every reseller identified only by coded alias, with no raw name?