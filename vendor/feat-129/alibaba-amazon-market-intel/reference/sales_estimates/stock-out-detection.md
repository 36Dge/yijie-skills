# Stock-Out Detection & Competitive Opportunity Identification

Based on the Jungle Scout Sales Estimates API, detects competitor stock-out events by identifying
daily sales drop signals, quantifies stock-out duration and demand gaps.

---

## When to Use

| Intent | Example Query |
|--------|-------------|
| Competitor stock-out monitoring | "Have any of these competitors gone out of stock recently?" |
| Sales drop detection | "Detect abnormal sales drops for this ASIN" |
| Stock-out opportunity assessment | "How much demand can I capture when a competitor is out of stock?" |
| Ad boost timing | "When does the competitor go out of stock so I can increase ads?" |
| Supply chain risk | "Monitor the supply stability of these ASINs" |

### ⛔ Not Applicable

| Intent | Alternative Module |
|--------|-------------------|
| Routine competitor sales monitoring | Competitive Sales Tracking (within this skill) |
| Promotion impact quantification | Deal & Promotion Impact (within this skill) |
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
from stockout_detect import detect_stockouts

result = detect_stockouts(
    mcp_data=<mcp_response>,
    output_dir="/round-{N}/data",
    asin="B0D1XD1ZV3",               # ASIN 标签（用于 CSV 标识）
    drop_threshold=0.2,   # Sales below 20% of MA7 treated as stock-out signal (default)
    min_streak_days=2,     # Consecutive ≥2 days below threshold to flag as stock-out event (default)
)
# Returns dict: {"output_dir", "total_rows", "rows_per_asin", "columns", "stockout_daily_csv", "stockout_events_csv", "total_events"}
```

---

## Execution Steps

### Step 1: Parse Parameters

- Extract ASIN list and date range; if dates not specified, default to the most recent 60 days

### Step 2: API Data Collection

- Call `sales_estimates` for each ASIN
- 429/5xx errors trigger automatic retry; 422 errors are gracefully skipped

### Step 3: Deliver Results

- Output the key findings (tables, insights) directly in the conversation. Reference the CSV file for the complete dataset.

---

## Output Files

### `stockout_daily.csv` — Daily Stock-Out Signal Time Series

| Column | Type | Description |
|--------|------|-------------|
| `asin` | string | Product ASIN |
| `date` | string | Date (YYYY-MM-DD) |
| `estimated_units_sold` | int | Estimated daily units sold |
| `price` | float | Daily price (USD) |
| `ma7_units` | float | 7-day moving average units sold |
| `velocity_ratio` | float | Daily units / MA7 |
| `is_stockout_signal` | bool | Whether this is a stock-out signal |
| `stockout_event_id` | int | Stock-out event ID (0 = not a stock-out) |

### `stockout_events.csv` — Stock-Out Event Summary

| Column | Type | Description |
|--------|------|-------------|
| `event_id` | int | Stock-out event ID |
| `asin` | string | Product ASIN |
| `start_date` | string | Stock-out start date |
| `end_date` | string | Stock-out end date |
| `duration_days` | int | Stock-out duration in days |
| `avg_units_during` | float | Average daily units during stock-out |
| `baseline_ma7` | float | Pre-stock-out MA7 baseline units |
| `demand_gap_units` | int | Demand gap in units |
| `severity` | string | Severity level: severe / moderate / mild |

---

## Notes

- Maximum 10 ASINs; excess is automatically truncated
- Date range maximum 365 days; `end_date` cannot be later than yesterday
- `drop_threshold` defaults to 0.2 (sales below 20% of MA7); adjustable
- `min_streak_days` defaults to 2 to avoid false positives from single-day fluctuations
- Severity determination: daily average during stock-out < 5% of baseline = severe, 5–20% = moderate, >20% = mild

