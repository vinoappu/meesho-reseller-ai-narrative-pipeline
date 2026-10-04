# Meesho Monitoring Agent Specification

## Five Core Components

### Goal

Keep Meesho category managers informed when category revenue moves beyond the 8% month-on-month threshold, while holding every drafted message for human approval before it can be considered sent.

### Tools

- `validate_feed(csv_path)` from Part 2 `part2_engine.growth_engine` validates each monthly revenue CSV before analysis.
- `mom_growth(previous, current)` from Part 2 calculates the month-on-month percentage.
- `is_flagged(mom_pct)` from Part 2 classifies the percentage as `flagged`, `not_flagged`, or `escalate_exact_boundary`.
- `fill_prompt_pack(...)` from Part 3 `part3_narrative.template_fill` fills the Context → Insight → Implication message template using supplied category, month, revenue, and growth values.
- The Part 1 `monthly_category_revenue.csv` is the source of monthly category revenue and order-count inputs.

The runner imports and calls the Part 2 functions; it does not reimplement their calculations or validation behavior.

### Memory / State

The runner is stateless between invocations. Each run reads the prior- and current-month CSV inputs afresh and holds the current invocation's month/category values only while constructing its result. Historical state is therefore carried by the supplied feed, not hidden process memory.

### Planner

The ordered planner is:

1. Load the monthly revenue feed(s) and run `validate_feed` on both the previous- and current-month inputs.
2. If either feed is invalid, Hard Stop and report its validation errors; perform no MoM computation.
3. If both feeds are valid, compute `mom_growth` for every category present in the adjacent months.
4. Run `is_flagged` for every category.
5. Sort categories classified as `flagged` by `abs(mom_pct)` descending; break ties by category name for repeatable output.
6. Draft a message through Part 3's template for at most the top three flagged categories. Keep each draft held for human approval; the cap prevents notification flooding.
7. Log any remaining flagged categories beyond the cap in `suppressed_categories` as “suppressed, review manually”; do not draft a message for them.
7b. Separately log every category classified as `escalate_exact_boundary` in `escalated_categories`, without drafting a message. An exact-boundary category is neither `flagged` nor `not_flagged`, so it must be represented explicitly and never silently dropped or mistaken for either class.
8. Emit one structured JSON object for the run, including successful and Hard Stop results.

### Feedback Loop

Every draft is held for a human reviewer. The mock runner does not send email or call a network service. A successful run uses `action_taken: "drafted_and_held_for_approval"`; this is a simulated approval checkpoint, not evidence that a message was sent or approved. A human must review and approve a draft in a separate process before any real delivery could occur.

## Guardrails and Stop Conditions

- **Input guardrail:** `validate_feed` must pass for both feeds before month selection, growth computation, classification, or drafting. If it returns `False`, the run is a Hard Stop and surfaces the validation errors rather than silently skipping bad rows.
- **Action guardrail:** messages are drafted and held only. The runner never auto-sends a message and has no Gmail, SMTP, or other delivery integration.
- **Output guardrail:** every numeric value in a draft must come from the supplied Part 1/Part 2 feed values or their calculated `mom_pct`. No unsupported numbers or causes may be introduced.
- **Success condition:** both feeds validate, adjacent-month category values are available, and the runner emits drafts for up to the top three flagged categories (or correctly emits zero drafts when none cross the threshold), with all figures traceable. Suppressed and exact-boundary categories are reported separately.
- **Error condition:** either feed fails `validate_feed`, or valid feeds lack the requested month/category values needed for comparison. The runner returns `validation_status: "invalid"`, reports the errors, emits no drafts, and sets `action_taken: "hard_stop"`.

## Structured Output

Every invocation returns exactly these top-level keys and the CLI prints that object as JSON:

```json
{
  "run_month": "May",
  "validation_status": "valid",
  "validation_errors": [],
  "flagged_categories": [
    {
      "category": "Ethnic Wear",
      "mom_pct": 77.1,
      "previous_revenue": 104520.77,
      "current_revenue": 185107.61,
      "drafted": true,
      "message": "Context / Insight / Implication draft held for approval"
    }
  ],
  "suppressed_categories": [],
  "escalated_categories": [],
  "action_taken": "drafted_and_held_for_approval"
}
```

`flagged_categories` contains every `flagged` result in descending absolute-growth order. Its first three entries at most have `drafted: true` and a `message`; entries beyond that cap have `drafted: false` and are also named in `suppressed_categories`. Exact-boundary results appear only in `escalated_categories`. A Hard Stop has empty `flagged_categories`, `suppressed_categories`, and `escalated_categories` lists.

## Given-When-Then Agent Specs

1. **GIVEN** April→May Ethnic Wear revenue moves from 104520.77 to 185107.61, **WHEN** the agent computes `mom_growth` then runs `is_flagged` on it, **THEN** `mom_growth` returns 77.1 and `is_flagged` returns `"flagged"`; the result is eligible for a held draft, subject to the three-message cap.
2. **GIVEN** May→June Beauty & Personal Care revenue moves from 35542.11 to 37559.07, **WHEN** the agent evaluates the category, **THEN** `mom_growth` returns 5.67 and `is_flagged` returns `"not_flagged"`; it appears in neither flagged nor suppressed output.
3. **GIVEN** a synthetic pair previous=100000, current=108000, **WHEN** the agent evaluates its exactly-on-threshold growth, **THEN** `mom_growth` returns exactly 8.0 and `is_flagged` returns `"escalate_exact_boundary"`, not `"flagged"` and not `"not_flagged"`; the category is logged separately without a draft.
4. **GIVEN** the corrupted feed fixture, **WHEN** `validate_feed` runs before the agent's analysis, **THEN** it returns `(False, errors)` where `errors` has exactly three entries, in order: the negative-revenue row, the missing-category row, and the missing-revenue row; the agent Hard Stops without computing MoM or drafting messages.

## Running the Mock Agent

From the project root, run either scenario with the shared Part 1 feed:

```powershell
python "Part 4/part4_agent/mock_agent_runner.py" May "Part 1/part1_sql/output/monthly_category_revenue.csv" "Part 1/part1_sql/output/monthly_category_revenue.csv"
python "Part 4/part4_agent/mock_agent_runner.py" June "Part 1/part1_sql/output/monthly_category_revenue.csv" "Part 1/part1_sql/output/monthly_category_revenue.csv"
```

The first CSV supplies the prior-month rows; the second supplies the current-month rows. The runner selects April/May or May/June from those feeds according to `run_month`.