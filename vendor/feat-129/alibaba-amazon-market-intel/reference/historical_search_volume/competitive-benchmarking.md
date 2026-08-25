# Competitive Benchmarking

Based on the Jungle Scout Historical Search Volume API, compares weekly search volume time series
across multiple keywords (generic category terms + brand terms), calculates Share of Search,
correlation coefficients, and growth rate differences to quantify brand awareness changes and competitive landscape evolution.

---

## When to Use

| Intent | Example Query |
|--------|-------------|
| Brand vs category comparison | "Compare search volume trends for wireless earbuds and AirPods" |
| Monitor competitor dynamics | "Is Samsung earbuds eroding AirPods' search share?" |
| Track marketing campaign effectiveness | "How did Anker earbuds search volume change after Prime Day?" |
| Assess brand awareness | "What is Bose's search share in the headphones category?" |
| Multi-brand competitive landscape | "Compare search trends for AirPods, Galaxy Buds, and Bose QuietComfort" |

### ⛔ Not Applicable

| Intent | Alternative Module |
|--------|-------------------|
| Single-keyword seasonal analysis | `seasonal-demand-profiling` reference |
| Ad budget planning | `ad-campaign-timing` reference |
| Inventory planning | `inventory-demand-forecasting` reference |

---

## Usage

```python
# Step 1: Fetch data via MCP
# 调用历史搜索趋势工具获取数据
# Step 2: Pass MCP response to analysis script
import sys
sys.path.insert(0, '{SKILL_DIR}/scripts/historical_search_volume')
# Replace {SKILL_DIR} with the actual install dir, e.g.
# ${account_skills}/alibaba-amazon-market-intel
from competitive_benchmark import analyze_competitive_benchmark

result = analyze_competitive_benchmark(
    mcp_data=<mcp_response>,
    keyword="wireless earbuds",                          # keyword (string)
    output_dir="/round-{N}/data",
)
# Returns dict: {"output_dir": "...", "total_rows": N, "rows_per_keyword": {...}, ...}
```

---

## Execution Steps

### Step 1: Parse Keywords and Date Range

- Extract 2–5 keywords (typically including generic category terms and brand terms) and date range from the query
- If the user does not specify dates, default to the most recent 12 months

### Step 2: Run Analysis

- Execute `analyze_competitive_benchmark()`
- The script automatically calculates: weekly search share per keyword, week-over-week change rate,
  Pearson correlation coefficients between keywords, and total growth rate over the period

### Step 3: Deliver Results

- Output the key findings (tables, insights) directly in the conversation. Reference the CSV file for the complete dataset.

---

## Output Files

### `competitive_benchmark.csv` — Weekly Time Series with Benchmarking Metrics

| Column | Type | Description |
|--------|------|-------------|
| `keyword` | string | Queried keyword |
| `estimate_start_date` | string | Week start date (YYYY-MM-DD) |
| `estimate_end_date` | string | Week end date (YYYY-MM-DD) |
| `estimated_exact_search_volume` | int | Exact match search volume for the week |
| `share_of_search` | float | Search share for the week (%) |
| `wow_change_pct` | float | Week-over-week change rate (%) |

### `benchmark_summary.csv` — Keyword-Level Competitive Summary

| Column | Type | Description |
|--------|------|-------------|
| `keyword` | string | Keyword |
| `total_weeks` | int | Total weeks of data coverage |
| `mean_weekly_volume` | float | Average weekly search volume |
| `mean_share_of_search` | float | Average search share (%) |
| `peak_volume` | int | Peak weekly search volume |
| `peak_week` | string | Peak week start date |
| `total_growth_pct` | float | Total growth rate over the period (%) |
| `correlation_with_others` | float | Average Pearson correlation coefficient with other keywords |

---

## Example

**Query**: "Compare search volume trends for wireless earbuds and AirPods"

```python
result = analyze_competitive_benchmark(
    mcp_data=<mcp_response>,
    keyword="wireless earbuds",
    output_dir="/round-1/data",
)
```

**Key findings example**:
```
Compared 'wireless earbuds' (category term) and 'airpods' (brand term) search trends over the past 52 weeks.
AirPods average search share 62%, wireless earbuds 38%. Correlation 0.85 (highly synchronized).
AirPods share rose to 71% during Q4 holiday season, showing brand advantage in the gifting period.

Follow-up suggestions:
- Add 'galaxy buds' for a more comprehensive competitive landscape analysis
- Use ad-campaign-timing to plan ad boost strategies during brand term share troughs
- Use keyword-expansion to discover category long-tail keywords with low brand penetration
```

---

## Notes

- **At least 2 keywords recommended**: Benchmarking analysis requires comparison targets; a single keyword cannot calculate search share
- **Search share**: Calculated based on the input keyword set, does not represent absolute share of the entire category
- **Correlation coefficient**: Requires at least 4 weeks of data to calculate meaningful correlation

