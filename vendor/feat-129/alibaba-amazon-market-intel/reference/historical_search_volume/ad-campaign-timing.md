# Ad Campaign Timing & Budget Allocation

Based on the Jungle Scout Historical Search Volume API, analyzes weekly search volume trends for keywords,
classifies each week into demand tiers (high / medium / low), generates budget weight recommendations,
identifies optimal windows for increasing or reducing ad spend, and provides data-driven support for PPC bidding and advertising calendars.

---

## When to Use

| Intent | Example Query |
|--------|-------------|
| Optimize PPC bidding rhythm | "When should I increase PPC spend for sunscreen?" |
| Plan ad budget allocation | "Help me plan the annual ad budget rhythm for space heater" |
| Identify boost/reduce windows | "When should I reduce the ad budget for yoga mat?" |
| Multi-keyword ad rhythm comparison | "Compare the ad timing rhythm of sunscreen and moisturizer" |
| Sponsored Brand timing | "When is the best time to run brand video ads for rain jacket?" |

### ⛔ Not Applicable

| Intent | Alternative Module |
|--------|-------------------|
| View seasonal demand curves | `seasonal-demand-profiling` reference |
| Inventory planning and demand forecasting | `inventory-demand-forecasting` reference |
| Determine new product launch timing | `product-launch-timing` reference |

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
from ad_timing import analyze_ad_timing

result = analyze_ad_timing(
    mcp_data=<mcp_response>,
    keyword="sunscreen",                                 # keyword (string)
    output_dir="/round-{N}/data",
)
# Returns dict: {"output_dir": "...", "total_rows": N, "rows_per_keyword": {...}, ...}
```

---

## Execution Steps

### Step 1: Parse Keywords and Date Range

- Extract 1–5 keywords and date range from the query
- If the user does not specify dates, default to the most recent 12 months

### Step 2: Run Analysis

- Execute `analyze_ad_timing()`
- The script automatically calculates: demand tiers (high ≥ 70% of peak / medium 30–70% / low < 30%),
  budget weights (high → 1.5x / medium → 1.0x / low → 0.5x), ad action recommendations,
  week-over-week change rate, and optimal boost/reduce windows

### Step 3: Deliver Results

- Output the key findings (tables, insights) directly in the conversation. Reference the CSV file for the complete dataset.

---

## Output Files

### `ad_timing.csv` — Weekly Time Series with Ad Metrics

| Column | Type | Description |
|--------|------|-------------|
| `keyword` | string | Queried keyword |
| `estimate_start_date` | string | Week start date (YYYY-MM-DD) |
| `estimate_end_date` | string | Week end date (YYYY-MM-DD) |
| `estimated_exact_search_volume` | int | Exact match search volume for the week |
| `pct_of_peak` | float | Percentage of peak search volume (%) |
| `wow_change_pct` | float | Week-over-week change rate (%) |
| `demand_tier` | string | Demand tier (high / medium / low) |
| `budget_weight` | float | Budget weight (1.5 / 1.0 / 0.5) |
| `ad_action` | string | Ad action recommendation (boost / maintain / reduce) |

### `ad_summary.csv` — Keyword-Level Ad Decision Summary

| Column | Type | Description |
|--------|------|-------------|
| `keyword` | string | Keyword |
| `total_weeks` | int | Total weeks of data coverage |
| `high_demand_weeks` | int | Number of high-demand weeks |
| `medium_demand_weeks` | int | Number of medium-demand weeks |
| `low_demand_weeks` | int | Number of low-demand weeks |
| `high_demand_pct` | float | Percentage of high-demand weeks (%) |
| `boost_window_start` | string | Optimal boost window start week |
| `boost_window_end` | string | Optimal boost window end week |
| `reduce_window_start` | string | Optimal reduce window start week |
| `reduce_window_end` | string | Optimal reduce window end week |
| `peak_volume` | int | Peak weekly search volume |
| `peak_week` | string | Peak week start date |
| `suggested_budget_split` | string | Suggested budget allocation ratio |

---

## Example

**Query**: "When should I increase PPC spend for sunscreen?"

```python
result = analyze_ad_timing(
    mcp_data=<mcp_response>,
    keyword="sunscreen",
    output_dir="/round-1/data",
)
```

**Key findings example**:
```
Analyzed 'sunscreen' search volume trends over the past 52 weeks for ad budget planning.
High-demand period (boost): Week 1 of May ~ Week 2 of August (14 weeks), recommend increasing budget by 1.5x.
Low-demand period (reduce): November ~ February (22 weeks), recommend reducing to 0.5x budget.
Suggested budget allocation: 60% for high-demand period, 30% for medium-demand period, 10% for low-demand period.

Follow-up suggestions:
- Start gradually increasing bids 2 weeks before the boost window begins
- Use keyword-expansion to discover sunscreen-related long-tail keywords
- Compare ad timing differences for sub-keywords like 'sunscreen spf 50'
```

