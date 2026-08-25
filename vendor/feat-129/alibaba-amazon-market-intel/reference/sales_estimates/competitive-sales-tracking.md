# Competitive Sales Tracking & Benchmarking

Based on the Jungle Scout Sales Estimates API, tracks daily estimated sales and prices for competitor ASINs,
calculates market share, sales velocity, and promotion detection signals to provide ongoing competitive intelligence.

---

## When to Use

| Intent | Example Query |
|--------|-------------|
| Competitor sales monitoring | "Track the sales of these 5 competitor ASINs over the last 30 days" |
| Promotion activity detection | "Has the competitor run any promotions recently? Any abnormal sales spikes?" |
| Market share calculation | "What are the sales share percentages for these ASINs in the category?" |
| Price strategy analysis | "What's the relationship between competitor price changes and sales?" |
| Own product benchmarking | "Compare my ASIN's sales velocity against competitors" |

### ⛔ Not Applicable

| Intent | Alternative Module |
|--------|-------------------|
| Keyword search volume trends | Seasonal Demand Profiling (within this skill) |
| Keyword competitive benchmarking | Competitive Benchmarking (within this skill) |
| Ad budget planning | Ad Campaign Timing (within this skill) |
| Price elasticity analysis | Pricing Strategy & Elasticity (within this skill) |

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
from competitive_sales import analyze_competitive_sales

result = analyze_competitive_sales(
    mcp_data=<mcp_response>,
    output_dir="/round-{N}/data",
    asin="B0D5CZSM45",              # ASIN 标签（用于 CSV 标识）
)
# Returns dict: {"output_dir", "total_rows", "rows_per_asin", "columns", "competitive_sales_csv", "sales_summary_csv"}
```

---

## Execution Steps

### Step 1: Parse ASINs and Date Range

- Extract 1–10 ASINs and date range from user query
- If the user does not specify dates, default to the most recent 30 days
- Normalize ASINs to uppercase

### Step 2: API Data Collection

- Call `sales_estimates(asin=asin, start_date=..., end_date=...)` for each ASIN
- 429/5xx errors trigger automatic exponential backoff retry; 422 errors are gracefully skipped

### Step 3: Deliver Results

- Output the key findings (tables, insights) directly in the conversation. Reference the CSV file for the complete dataset.

---

## Output Files

### `competitive_sales.csv` — Daily Time Series with Competitive Metrics

| Column | Type | Description |
|--------|------|-------------|
| `asin` | string | Product ASIN |
| `date` | string | Date (YYYY-MM-DD) |
| `estimated_units_sold` | int | Estimated daily units sold |
| `price` | float | Daily price (USD) |
| `market_share` | float | Daily sales share (%) |
| `ma7_units` | float | 7-day moving average units sold |
| `dod_change_pct` | float | Day-over-day change rate (%) |
| `is_spike` | bool | Promotion/anomaly detection (units > MA7 × 2) |
| `price_changed` | bool | Whether price changed from previous day |

### `sales_summary.csv` — ASIN-Level Competitive Summary

| Column | Type | Description |
|--------|------|-------------|
| `asin` | string | Product ASIN |
| `total_days` | int | Days of data coverage |
| `total_units_sold` | int | Total units sold over the period |
| `mean_daily_units` | float | Average daily units sold |
| `peak_daily_units` | int | Highest single-day units sold |
| `peak_date` | string | Date of highest sales |
| `mean_price` | float | Average price (USD) |
| `price_range` | string | Price range (min–max) |
| `market_share_pct` | float | Average sales share over the period (%) |
| `spike_days` | int | Number of detected promotion/anomaly days |
| `price_change_count` | int | Number of price changes |

---

## Notes

- Maximum 10 ASINs; excess is automatically truncated
- Date range maximum 365 days; `end_date` cannot be later than yesterday
- Market share is calculated based on the input ASIN set, not the absolute share of the entire category
- Promotion detection is based on a simple MA7 × 2 threshold; recommend combining with price changes for comprehensive assessment
- Rate limiting: 429/5xx errors trigger automatic exponential backoff retry; single ASIN failure does not affect the overall process

