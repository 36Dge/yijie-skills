# New Product Launch Monitoring

Based on the Jungle Scout Product Database API, filters newly launched products within the last 30/60/90 days by `date_first_available`,
monitors new entrants' BSR trajectories and review accumulation speed, and builds category launch velocity benchmarks.

---

## When to Use

| Intent | Example Query |
|--------|-------------|
| New product tracking | "Show new products launched in the pet supplies category in the last 30 days" |
| Competitor entry monitoring | "Monitor new entrants in the yoga mat category" |
| Launch benchmarks | "What's the typical review accumulation speed for new products?" |
| Competitive threat early warning | "Which new products are growing the fastest?" |

### ⛔ Not Applicable

| Intent | Alternative Module |
|--------|-------------------|
| Keyword search volume trends | Seasonal Demand Profiling (within this skill) |
| Single ASIN sales query | 销量估算工具 |

---

## Usage

Reference script: `scripts/product_database/new_product_launch_monitoring.py`

```python
# Step 1: Fetch data via MCP
# 调用产品数据库工具获取数据
# Step 2: Pass MCP response to analysis script
import sys
sys.path.insert(0, '{SKILL_DIR}/scripts/product_database')
# Replace {SKILL_DIR} with the actual install dir, e.g.
# ${account_skills}/alibaba-amazon-market-intel
from new_product_launch_monitoring import analyze
result = analyze(mcp_data=<mcp_response>, output_dir="/round-{N}/data")
```

---

## Execution Steps

### Step 1: Parse Category and Time Window

- Extract category and lookback days (default 90 days) from user query

### Step 2: Product Database Data Collection + Date Filtering

- 调用 `js_product_database_query`，入参：`include_keywords`, `categories`, `marketplace`, `page_size`，post-filter in Python: `date_first_available >= threshold`

### Step 3: Launch Velocity Metric Calculation

- Review accumulation rate: reviews / days_since_launch (fast >2/day, normal 0.5–2/day, slow <0.5/day)
- BSR trajectory slope: negative = improving, positive = declining
- Sales ramp-up: week-over-week growth rate
- Launch success rate: percentage of new products with revenue > $5K/month

### Step 4: Deliver Results

- Output the key findings (tables, insights) directly in the conversation. Reference the CSV file for the complete dataset.

---

## Output Files

### `new_launches.csv` — New Product List

| Column | Type | Description |
|--------|------|-------------|
| `asin` | string | Product ASIN |
| `title` | string | Product title |
| `brand` | string | Brand |
| `price` | float | Price (USD) |
| `sales_cnt_30d` | int | 30-day estimated sales |
| `revenue_30d` | float | 30-day estimated revenue |
| `reviews` | int | Review count |
| `product_rank` | int | BSR rank |
| `date_first_available` | string | Launch date |
| `lqs` | float | Listing Quality Score |

---

## Notes

- `date_first_available` is a string field; post-filtering must be done in Python, not via API parameters
- Some new products may not yet have Sales Estimates data (422 error); gracefully skipped
- Review accumulation rate >2/day typically indicates use of Vine or aggressive PPC strategy

