# Revenue Estimation & Financial Modeling

Based on the Jungle Scout Sales Estimates API, combines daily sales and price data
to build revenue timelines, supporting multi-granularity aggregation and financial metric calculations.

---

## When to Use

| Intent | Example Query |
|--------|-------------|
| ASIN revenue estimation | "What's the revenue for this ASIN over the past 3 months?" |
| Category market sizing | "Estimate the total revenue for the Top 10 ASINs in this category" |
| Revenue trend analysis | "What's the monthly revenue trend for these competitors?" |
| Acquisition due diligence | "Evaluate the revenue scale of products under this brand" |
| Revenue share comparison | "What revenue share does each of these 5 ASINs hold?" |

### ⛔ Not Applicable

| Intent | Alternative Module |
|--------|-------------------|
| Price elasticity analysis | Pricing Strategy & Elasticity (within this skill) |
| Promotion impact quantification | Deal & Promotion Impact (within this skill) |
| Routine competitor sales monitoring | Competitive Sales Tracking (within this skill) |
| Keyword search volume trends | Seasonal Demand Profiling (within this skill) |

---

## Usage

```python
# Step 1: Fetch data via MCP
# 调用销量估算工具获取数据
# Step 2: Pass MCP response to analysis script
import sys
sys.path.insert(0, '{SKILL_DIR}/scripts/sales_estimates')
# Replace {SKILL_DIR} with the actual install dir, e.g.
# ${account_skills}/alibaba-amazon-market-intel
from revenue_model import analyze_revenue

result = analyze_revenue(
    mcp_data=<mcp_response>,
    output_dir="/round-{N}/data",
    asin="B0D1XD1ZV3",                    # ASIN 标签（用于 CSV 标识）
)
# Returns dict: {"output_dir", "total_rows", "rows_per_asin", "columns", "revenue_daily_csv", "revenue_summary_csv"}
```

---

## Execution Steps

### Step 1: Parse ASINs and Date Range

- Extract 1–10 ASINs and date range from the query
- If the user does not specify dates, default to the most recent 90 days

### Step 2: API Data Collection

- Call `sales_estimates` for each ASIN
- 429/5xx errors trigger automatic retry; 422 errors are gracefully skipped

### Step 3: Deliver Results

- Output the key findings (tables, insights) directly in the conversation. Reference the CSV file for the complete dataset.

---

## Output Files

### `revenue_daily.csv` — Daily Revenue Time Series

| Column | Type | Description |
|--------|------|-------------|
| `asin` | string | Product ASIN |
| `date` | string | Date (YYYY-MM-DD) |
| `estimated_units_sold` | int | Estimated daily units sold |
| `price` | float | Daily price (USD) |
| `daily_revenue` | float | Daily revenue (USD) |
| `ma7_revenue` | float | 7-day moving average revenue |
| `cumulative_revenue` | float | Cumulative revenue |
| `week` | string | ISO week (YYYY-WNN) |
| `month` | string | Month (YYYY-MM) |

### `revenue_summary.csv` — ASIN-Level Revenue Summary

| Column | Type | Description |
|--------|------|-------------|
| `asin` | string | Product ASIN |
| `total_days` | int | Days of data coverage |
| `total_revenue` | float | Total revenue (USD) |
| `total_units` | int | Total units sold |
| `mean_daily_revenue` | float | Average daily revenue |
| `mean_price` | float | Average price |
| `peak_daily_revenue` | float | Highest single-day revenue |
| `peak_date` | string | Date of highest revenue |
| `monthly_avg_revenue` | float | Monthly average revenue |
| `revenue_share_pct` | float | Revenue share (%) |
| `revenue_trend` | string | Revenue trend (growing / declining / stable) |

---

## Notes

- Maximum 10 ASINs; excess is automatically truncated
- Date range maximum 365 days; `end_date` cannot be later than yesterday
- Revenue = units sold × price; some days may have price = 0 (missing data)
- Revenue trend determination: based on first-half vs second-half average daily revenue comparison; >10% growth = growing

