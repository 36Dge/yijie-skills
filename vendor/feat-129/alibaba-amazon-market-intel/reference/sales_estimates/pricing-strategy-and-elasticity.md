# Pricing Strategy & Price Elasticity Analysis

Based on the Jungle Scout Sales Estimates API, correlates daily price changes with sales changes,
estimates price elasticity coefficients, detects promotional discount patterns, and identifies optimal price ranges.

---

## When to Use

| Intent | Example Query |
|--------|-------------|
| Price elasticity estimation | "What's the price elasticity for this ASIN?" |
| Promotion effectiveness analysis | "How much did competitor sales increase when they discounted?" |
| Optimal price point | "What's the optimal pricing range for these competitors?" |
| Price sensitivity comparison | "Compare the price sensitivity of these 3 ASINs" |
| Discount pattern detection | "What's the competitor's promotion frequency and discount depth?" |

### ⛔ Not Applicable

| Intent | Alternative Module |
|--------|-------------------|
| Competitor sales share monitoring | Competitive Sales Tracking (within this skill) |
| Keyword search volume trends | Seasonal Demand Profiling (within this skill) |
| Ad budget planning | Ad Campaign Timing (within this skill) |

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
from pricing_elasticity import analyze_pricing_elasticity

result = analyze_pricing_elasticity(
    mcp_data=<mcp_response>,
    output_dir="/round-{N}/data",
    asin="B0D1XD1ZV3",                    # ASIN 标签（用于 CSV 标识）
    promo_threshold=0.9,                   # Promotion detection threshold (default 0.9, i.e., 10% discount)
)
# Returns dict: {"output_dir", "total_rows", "rows_per_asin", "columns", "pricing_elasticity_csv", "pricing_summary_csv"}
```

---

## Execution Steps

### Step 1: Parse ASINs and Date Range

- Extract 1–10 ASINs and date range from the query
- If the user does not specify dates, default to the most recent 30 days

### Step 2: API Data Collection

- Call `sales_estimates` for each ASIN
- 429/5xx errors trigger automatic retry; 422 errors are gracefully skipped

### Step 3: Deliver Results

- Output the key findings (tables, insights) directly in the conversation. Reference the CSV file for the complete dataset.

---

## Output Files

### `pricing_elasticity.csv` — Daily Time Series with Elasticity Metrics

| Column | Type | Description |
|--------|------|-------------|
| `asin` | string | Product ASIN |
| `date` | string | Date (YYYY-MM-DD) |
| `estimated_units_sold` | int | Estimated daily units sold |
| `price` | float | Daily price (USD) |
| `price_change_pct` | float | Day-over-day price change rate (%) |
| `units_change_pct` | float | Day-over-day sales change rate (%) |
| `point_elasticity` | float | Point elasticity coefficient |
| `on_promo` | bool | Whether in promotion state |
| `ma7_units` | float | 7-day moving average units sold |

### `pricing_summary.csv` — ASIN-Level Pricing Analysis Summary

| Column | Type | Description |
|--------|------|-------------|
| `asin` | string | Product ASIN |
| `total_days` | int | Days of data coverage |
| `mean_price` | float | Average price (USD) |
| `price_range` | string | Price range (min–max) |
| `price_std` | float | Price standard deviation |
| `mean_daily_units` | float | Average daily units sold |
| `median_elasticity` | float | Median elasticity coefficient |
| `price_sales_correlation` | float | Price-sales Pearson correlation coefficient |
| `promo_days` | int | Number of promotion days |
| `promo_pct` | float | Promotion days percentage (%) |
| `promo_avg_units` | float | Average daily units during promotions |
| `non_promo_avg_units` | float | Average daily units during non-promotion periods |
| `promo_uplift_pct` | float | Promotion sales uplift (%) |

---

## Notes

- Maximum 10 ASINs; excess is automatically truncated
- Date range maximum 365 days; `end_date` cannot be later than yesterday
- Elasticity coefficient interpretation: |E| > 1 indicates elastic demand (price cuts are beneficial), |E| < 1 indicates inelastic demand
- Promotion detection threshold defaults to average price × 0.9; adjustable via the `promo_threshold` parameter
- Extreme values with |E| > 10 are filtered from summaries (typically caused by minimal price changes)

