# ASIN Deep Dive & Data Enrichment

Based on the Jungle Scout Product Database API, enriches CRM/product catalogs with estimated sales, revenue, BSR,
Listing Quality Score, weight/dimensions data, supporting FBA fee calculation and logistics planning.

---

## When to Use

| Intent | Example Query |
|--------|-------------|
| Catalog data enrichment | "Enrich these 10 ASINs with sales and revenue data" |
| Listing quality audit | "Check the Listing Quality Scores for my product catalog" |
| FBA fee estimation | "Get weight and dimensions for FBA fee calculation" |
| ASIN deep analysis | "Deep dive into B0XXXXXX's sales, keywords, and quality" |

### ⛔ Not Applicable

| Intent | Alternative Module |
|--------|-------------------|
| Single ASIN quick query | 销量估算工具 |
| Category-level analysis | Competitive Landscape Analysis (within this skill) or `jungle-scout-deep-dive-analyzer` |

---

## Usage

Reference script: `scripts/product_database/asin_deep_dive_enrichment.py`

```python
# Step 1: Fetch data via MCP
# 调用产品数据库工具获取数据
# Step 2: Pass MCP response to analysis script
import sys
sys.path.insert(0, '{SKILL_DIR}/scripts/product_database')
# Replace {SKILL_DIR} with the actual install dir, e.g.
# ${account_skills}/alibaba-amazon-market-intel
from asin_deep_dive_enrichment import analyze
result = analyze(mcp_data=<mcp_response>, output_dir="/round-{N}/data")
```

---

## Execution Steps

### Step 1: Parse ASINs or Keywords

- Extract ASIN list or brand/keywords from user query

### Step 2: Product Database Data Collection

- 调用 `js_product_database_query`，入参：`include_keywords`, `categories`, `marketplace`, `page_size`

### Step 3: Enrichment Metric Calculation

- LQS Gap: ASIN LQS vs category average LQS
- FBA fee estimation: based on weight/dimensions
- Revenue trend: 30-day revenue data

### Step 4: Deliver Results

- Output the key findings (tables, insights) directly in the conversation. Reference the CSV file for the complete dataset.

---

## Output Files

### `asin_details.csv` — ASIN Enrichment Data

| Column | Type | Description |
|--------|------|-------------|
| `asin` | string | Product ASIN |
| `title` | string | Product title |
| `brand` | string | Brand |
| `price` | float | Price (USD) |
| `sales_cnt_30d` | int | 30-day estimated sales |
| `revenue_30d` | float | 30-day estimated revenue |
| `reviews` | int | Review count |
| `rating` | float | Rating |
| `lqs` | float | Listing Quality Score (0–10) |
| `product_rank` | int | BSR rank |
| `weight` | string | Weight |
| `dimensions` | string | Dimensions |

---

## Notes

- `weight` and `dimensions` may be None for some products
- `product_url` does not exist in the SDK; construct via `f'https://www.amazon.com/dp/{asin}'`
- Recommend combining with Sales Estimates API and Keywords by ASIN API for deeper analysis

