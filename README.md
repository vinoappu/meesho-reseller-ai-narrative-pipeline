# Meesho Reseller AI Narrative Pipeline

A four-part analytics project that turns reseller order data into revenue insights and review-ready stakeholder updates. It combines Python, SQL, CSV, and SQLite. The mock monitoring agent validates its inputs and holds generated drafts for human review; it does not send messages.

## At a Glance

- Generate a reproducible sample dataset of 24 resellers and 900 orders across April–June 2026.
- Query monthly category revenue, regional performance, top reseller spend, zero-order resellers, and June delivered-order average order value.
- Validate revenue feeds and classify month-over-month changes against an 8% threshold.
- Create fact-grounded narrative drafts and run a mock agent with a three-draft limit.

## Requirements

- Python 3.9 or newer
- No third-party Python packages
- SQLite support for working with the database (included in Python's standard library)

## Quick Start

Run commands from the repository root. The supplied CSV reports and database are included in the project.

Run the mock agent for May or June:

```sh
python "Part 4/part4_agent/mock_agent_runner.py" May "Part 1/part1_sql/output/monthly_category_revenue.csv" "Part 1/part1_sql/output/monthly_category_revenue.csv"
python "Part 4/part4_agent/mock_agent_runner.py" June "Part 1/part1_sql/output/monthly_category_revenue.csv" "Part 1/part1_sql/output/monthly_category_revenue.csv"
```

The first feed supplies prior-month rows; the second supplies current-month rows. The runner selects the requested adjacent months and prints a structured JSON result.

## Project Layout

```text
Part 1/
  data/                 Dataset generator, CSV data, and SQLite database
  part1_sql/
    SQLQuery/            Analysis queries
    output/              CSV query results
Part 2/
  part2_engine/          Revenue growth calculations and feed validation
Part 3/
  part3_narrative/       Narrative template, masking helpers, prompt, and report
Part 4/
  part4_agent/           Agent specification, mock runner, and tests
```

## Part 1: Data and SQL

The seeded generator creates 24 resellers and 900 orders for April, May, and June 2026. To recreate the source CSV files and SQLite database:

```sh
python "Part 1/data/generate_dataset.py"
```

This overwrites `resellers.csv`, `orders.csv`, and `meesho_reseller.db` in `Part 1/data/`. It does not refresh the SQL result exports.

The queries in `Part 1/part1_sql/SQLQuery/SQL_Query.txt` cover:

- Monthly revenue and order count by category
- Revenue and order count by region
- Top five resellers by total spend
- Resellers who have never ordered, including a `COUNT(*)` versus `COUNT(order_id)` demonstration
- June delivered-order average order value

The supplied result CSVs are in `Part 1/part1_sql/output/`.

## Part 2: Growth Engine

`Part 2/part2_engine/growth_engine.py` calculates month-over-month revenue growth and validates monthly revenue feeds. Changes greater than 8% in either direction are flagged; a change exactly at 8% is classified separately for escalation. Missing, nonnumeric, and negative revenue values are reported as validation errors.

## Part 3: Stakeholder Narratives

`Part 3/part3_narrative/prompt_pack.md` defines the prompt constraints, and `template_fill.py` creates a Context / Insight / Implication draft. `masking.py` provides reseller aliases and a raw-name leak check. Worked narratives and chart recommendations are in `narrative_report.md`.

## Part 4: Mock Monitoring Agent

The runner validates both feeds before analysis, compares adjacent-month category revenue, and sorts flagged changes by absolute growth. It drafts up to three messages and reports additional flagged categories as suppressed. Exact-boundary categories are reported separately. Every draft is held for human approval; there is no email or network delivery integration.

The agent behavior and structured output are documented in `Part 4/part4_agent/agent_spec.md`.

## Tests

For each suite, start from the repository root and run the commands for that part:

```sh
cd "Part 2"
python -m unittest part2_engine.test_growth_engine -v
```

```sh
cd "Part 3"
python -m unittest part3_narrative.test_masking -v
```

```sh
cd "Part 4"
python -m unittest part4_agent.test_mock_agent_runner -v
```
