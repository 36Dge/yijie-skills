# Competitive Landscape Analysis

Based on the Jungle Scout Product Database API, analyzes price distribution, review count tiers,
seller type composition (FBA/FBM/AMZ) within a category, identifies dominant brands,
and benchmarks internal products against category averages.

---

## When to Use

| Intent | Example Query |
|--------|-------------|
| Price distribution analysis | "Analyze the price distribution for the wireless earbuds category" |
| Brand dominance analysis | "Which brands dominate the yoga mat market?" |
| Product benchmarking | "How does my product compare to the category average?" |
| Seller composition | "What's the FBA vs FBM seller ratio in Home & Kitchen?" |

### ⛔ Not Applicable

| Intent | Alternative Module |
|--------|-------------------|
| Single keyword search volume | 关键词搜索量工具 |
| Complete 8-dimension deep analysis | `jungle-scout-deep-dive-analyzer` skill |

---

## Usage

Reference script: `scripts/product_database/competitive_landscape_analysis.py`

```python
# Step 1: Fetch data via MCP
# 调用产品数据库工具获取数据
# Step 2: Pass MCP response to analysis script
import sys
sys.path.insert(0, '{SKILL_DIR}/scripts/product_database')
# Replace {SKILL_DIR} with the actual install dir, e.g.
# ${account_skills}/alibaba-amazon-market-intel
from competitive_landscape_analysis import analyze
result = analyze(mcp_data=<mcp_response>, output_dir="/round-{N}/data")
```

---

## Execution Steps

### Step 1: Parse Category and Keywords

- Extract target category and keywords from user query

### Step 2: Product Database Data Collection

- 调用 `js_product_database_query`，入参：`categories`, `include_keywords`, `page_size`

### Step 3: Competitive Metric Calculation

- Price tiers: $0–15 / $15–30 / $30–50 / $50–100 / $100+, with product count, average sales, and average BSR per tier
- Review tiers: 0–50 / 50–200 / 200–500 / 500–1000 / 1000+
- Seller composition: FBA / FBM / AMZ percentages
- Brand coverage: Top 10 brands ranked by product count and revenue share
- LQS distribution: average Listing Quality Score per brand
- Category averages: average price, review count, rating, and sales

### Step 4: Deliver Results

- Output the key findings (tables, insights) directly in the conversation. Reference the CSV file for the complete dataset.

---

## Output Files

### `competitors.csv` — Category Competitive Product Data

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
| `lqs` | float | Listing Quality Score |
| `seller_type` | string | Seller type |
| `number_of_sellers` | int | Number of sellers |

---

## Notes

- Product Database returns a maximum of 50 results per call
- `categories` and `include_keywords` must be passed as lists
- Price tier thresholds can be adjusted based on category characteristics

