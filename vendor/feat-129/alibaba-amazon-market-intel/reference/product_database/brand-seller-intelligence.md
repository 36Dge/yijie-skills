# Brand & Seller Intelligence

Based on the Jungle Scout Product Database API, tracks brand product portfolio size, average price, and total revenue,
identifies unauthorized third-party sellers, and analyzes FBA/FBM fulfillment composition within a category.

---

## When to Use

| Intent | Example Query |
|--------|-------------|
| Brand portfolio analysis | "Analyze Anker's product portfolio and revenue" |
| Unauthorized seller detection | "Find third-party sellers using my brand name" |
| Fulfillment composition | "What's the FBA vs FBM ratio for yoga mat sellers?" |
| Competitor brand comparison | "Compare the top 5 brands in the power bank category" |

### ⛔ Not Applicable

| Intent | Alternative Module |
|--------|-------------------|
| Single brand search share | 品牌份额工具 |
| Complete category deep analysis | `jungle-scout-deep-dive-analyzer` skill |

---

## Usage

Reference script: `scripts/product_database/brand_seller_intelligence.py`

```python
# Step 1: Fetch data via MCP
# 调用产品数据库工具获取数据
# Step 2: Pass MCP response to analysis script
import sys
sys.path.insert(0, '{SKILL_DIR}/scripts/product_database')
# Replace {SKILL_DIR} with the actual install dir, e.g.
# ${account_skills}/alibaba-amazon-market-intel
from brand_seller_intelligence import analyze
result = analyze(mcp_data=<mcp_response>, output_dir="/round-{N}/data")
```

---

## Execution Steps

### Step 1: Parse Brand and Category

- Extract target brand name and/or category from user query

### Step 2: Product Database Data Collection

- 调用 `js_product_database_query`，入参：`include_keywords`, `categories`, `marketplace`, `page_size`

### Step 3: Brand Metric Calculation

- Portfolio size: unique ASIN count per brand
- Price range: min/max/avg price per brand
- Total revenue: sum(revenue_30d) per brand
- Average rating: mean(rating) per brand
- Fulfillment composition: FBA% / FBM% / AMZ% per brand
- Multi-seller ASINs: ASINs with number_of_sellers > 1 (potential unauthorized sellers)

### Step 4: Deliver Results

- Output the key findings (tables, insights) directly in the conversation. Reference the CSV file for the complete dataset.

---

## Output Files

### `brand_products.csv` — Brand Product Data

| Column | Type | Description |
|--------|------|-------------|
| `asin` | string | Product ASIN |
| `brand` | string | Brand |
| `price` | float | Price (USD) |
| `revenue_30d` | float | 30-day estimated revenue |
| `seller_type` | string | Seller type (FBA/FBM/AMZ) |
| `number_of_sellers` | int | Number of sellers |
| `lqs` | float | Listing Quality Score |

---

## Notes

- Unauthorized seller detection: `brand` matches target brand but `seller_type` is FBM or `number_of_sellers > 1`
- Brand name matching is case-sensitive; recommend searching both uppercase and lowercase variants
- Fulfillment composition analysis requires sufficient sample size (recommend ≥ 20 products)

