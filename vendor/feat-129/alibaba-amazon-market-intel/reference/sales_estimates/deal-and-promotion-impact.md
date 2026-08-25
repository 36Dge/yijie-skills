# Deal & Promotion Impact Quantification

Based on the Jungle Scout Sales Estimates API, compares daily sales and prices between promotion periods and baseline periods,
quantifies promotion lift, discount depth, and incremental units captured, supporting promotion ROI modeling.

---

## When to Use

| Intent | Example Query |
|--------|-------------|
| Promotion effectiveness quantification | "How much sales lift did this Lightning Deal generate?" |
| Pre/post promotion comparison | "Compare the sales baseline before and after the promotion" |
| Competitor deal tracking | "How much did competitor sales grow during Prime Day?" |
| Promotion ROI estimation | "What's the ROI of this discount?" |
| Multi-ASIN promotion comparison | "Compare the performance of these 5 competitors during Black Friday" |

### ⛔ Not Applicable

| Intent | Alternative Module |
|--------|-------------------|
| Price elasticity curve analysis | Pricing Strategy & Elasticity (within this skill) |
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
from promotion_impact import analyze_promotion_impact

result = analyze_promotion_impact(
    mcp_data=<mcp_response>,
    promo_start="2025-11-24",              # Promotion start date
    promo_end="2025-12-02",                # Promotion end date
    output_dir="/round-{N}/data",
    asin="B0D1XD1ZV3",                    # ASIN 标签（用于 CSV 标识）
)
# Returns dict: {"output_dir", "total_rows", "rows_per_asin", "columns", "promotion_impact_csv", "promotion_summary_csv"}
```

---

## Execution Steps

### Step 1: Parse Parameters

- Extract ASIN list, promotion start/end dates
- If the user does not specify baseline days, default to 14; recovery period defaults to 7

### Step 2: API Data Collection

- Automatically calculate the full date range (baseline_start → recovery_end)
- Call `sales_estimates` for each ASIN
- 429/5xx errors trigger automatic retry; 422 errors are gracefully skipped

### Step 3: Deliver Results

- Output the key findings (tables, insights) directly in the conversation. Reference the CSV file for the complete dataset.

---

## Output Files

### `promotion_impact.csv` — Daily Time Series with Phase Labels

| Column | Type | Description |
|--------|------|-------------|
| `asin` | string | Product ASIN |
| `date` | string | Date (YYYY-MM-DD) |
| `estimated_units_sold` | int | Estimated daily units sold |
| `price` | float | Daily price (USD) |
| `phase` | string | Phase: baseline / promo / recovery |
| `ma7_units` | float | 7-day moving average units sold |
| `baseline_avg_units` | float | Baseline period average daily units |
| `baseline_avg_price` | float | Baseline period average price |
| `lift_pct` | float | Daily sales lift vs baseline (%) |
| `discount_pct` | float | Daily price discount vs baseline average price (%) |

### `promotion_summary.csv` — ASIN-Level Promotion Impact Summary

| Column | Type | Description |
|--------|------|-------------|
| `asin` | string | Product ASIN |
| `baseline_days` | int | Baseline period days |
| `promo_days` | int | Promotion period days |
| `recovery_days` | int | Recovery period days |
| `baseline_avg_units` | float | Baseline period average daily units |
| `promo_avg_units` | float | Promotion period average daily units |
| `recovery_avg_units` | float | Recovery period average daily units |
| `promo_lift_pct` | float | Promotion period sales lift (%) |
| `recovery_vs_baseline_pct` | float | Recovery period vs baseline change (%) |
| `baseline_avg_price` | float | Baseline period average price |
| `promo_avg_price` | float | Promotion period average price |
| `avg_discount_pct` | float | Promotion period average discount (%) |
| `max_discount_pct` | float | Promotion period maximum discount (%) |
| `incremental_units` | int | Incremental units from promotion |
| `total_promo_units` | int | Total units sold during promotion |

---

## Notes

- Maximum 10 ASINs; excess is automatically truncated
- Full range = baseline_days + promo_days + recovery_days, total not exceeding 365 days
- `end_date` ≤ yesterday (API limitation); recovery end date is automatically clamped
- Baseline period selection: defaults to 14 days before promotion; recommend avoiding other promotions for a clean baseline
- Negative `recovery_vs_baseline_pct` indicates post-promotion demand cannibalization

