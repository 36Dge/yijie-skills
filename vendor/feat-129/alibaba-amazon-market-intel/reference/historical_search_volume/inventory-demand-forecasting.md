# Inventory & Demand Forecasting

Based on the Jungle Scout Historical Search Volume API, uses weekly search volume as a leading demand indicator,
calculates moving average trends, demand ramp-up/ramp-down inflection points, and inventory coverage week recommendations
to provide data-driven support for procurement and inventory decisions.

---

## When to Use

| Intent | Example Query |
|--------|-------------|
| Forecast future demand trends | "Forecast the search volume trend for space heater in the coming weeks" |
| Determine restocking timing | "When should I start restocking Christmas lights?" |
| Calculate inventory coverage weeks | "Based on current trends, how many weeks will my sunscreen inventory last?" |
| Identify demand inflection points | "When does demand for portable fan start ramping up?" |
| Year-over-year comparison | "Compare this year and last year search volume trends for yoga mat" |

### ⛔ Not Applicable

| Intent | Alternative Module |
|--------|-------------------|
| View seasonal demand curves only | `seasonal-demand-profiling` reference |
| Query current keyword search volume | 关键词搜索量工具 |
| Full keyword expansion | `keyword-expansion` skill |

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
from inventory_forecast import inventory_demand_forecast

result = inventory_demand_forecast(
    mcp_data=<mcp_response>,
    keyword="space heater",                              # keyword (string)
    output_dir="/round-{N}/data",
    lead_time_weeks=4,                               # Supply chain lead time (weeks), default 4
)
# Returns dict: {"output_dir": "...", "total_rows": N, "rows_per_keyword": {...}, ...}
```

---

## Execution Steps

### Step 1: Parse Keywords and Date Range

- Extract 1-5 keywords and date range from the query
- If the user does not specify dates, default to the most recent 12 months

### Step 2: Run Analysis

- Execute `inventory_demand_forecast()`
- The script automatically calculates: 4-week moving average (MA4), week-over-week change rate, trend direction,
  demand ramp-up/ramp-down inflection points (3 consecutive weeks of same-direction change), and suggested restocking start week based on lead time

### Step 3: Deliver Results

- Output the key findings (tables, insights) directly in the conversation. Reference the CSV file for the complete dataset.

---

## Output Files

### `inventory_forecast.csv` — Weekly Time Series with Forecast Metrics

| Column | Type | Description |
|--------|------|-------------|
| `keyword` | string | Queried keyword |
| `estimate_start_date` | string | Week start date (YYYY-MM-DD) |
| `estimate_end_date` | string | Week end date (YYYY-MM-DD) |
| `estimated_exact_search_volume` | int | Exact match search volume for the week |
| `ma4` | float | 4-week moving average search volume |
| `wow_change_pct` | float | Week-over-week change rate (%) |
| `trend_direction` | string | Trend direction (up / down / flat) |

### `forecast_summary.csv` — Keyword-Level Decision Summary

| Column | Type | Description |
|--------|------|-------------|
| `keyword` | string | Keyword |
| `total_weeks` | int | Total weeks of data coverage |
| `mean_weekly_volume` | float | Average weekly search volume |
| `peak_volume` | int | Peak weekly search volume |
| `peak_week` | string | Peak week start date |
| `trough_volume` | int | Trough weekly search volume |
| `trough_week` | string | Trough week start date |
| `ramp_up_week` | string | Demand ramp-up inflection point |
| `ramp_down_week` | string | Demand ramp-down inflection point |
| `suggested_stock_week` | string | Suggested restocking start week |
| `latest_trend` | string | Latest trend direction |

---

## Example

**Query**: "Forecast the demand trend for space heater and help me plan restocking"

```python
result = inventory_demand_forecast(
    mcp_data=<mcp_response>,
    keyword="space heater",
    output_dir="/round-1/data",
)
```

**Key findings example**:
```
Analyzed space heater search volume trends over the past 52 weeks.
Demand starts ramping up from Week 2 of September, peaks in Week 3 of November (weekly search volume 220K),
and drops rapidly after January. Considering a 4-week supply chain lead time, recommend starting restocking in Week 2 of August.

Follow-up suggestions:
- Use seasonal-demand-profiling to view more detailed seasonal fluctuation coefficients
- Compare demand rhythm differences for sub-keywords like portable heater
- Combine with jungle-scout-deep-dive-analyzer to evaluate the competitive landscape of this category
```

---

## Notes

- **Moving average window**: Default 4 weeks (MA4), requires at least 4 weeks of data to calculate
- **Inflection point detection**: Requires 3 consecutive weeks of same-direction change to identify an inflection point, avoiding noise interference
- **lead_time_weeks**: Supply chain lead time, default 4 weeks, used to calculate the suggested restocking start week

