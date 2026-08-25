# Pricing Strategy & Elasticity Analysis — Product Database

Based on the Jungle Scout Product Database API, compares average sales and BSR across price tiers within a category,
identifies price ceilings and floors (sales drop-off points), and monitors category price compression trends.

---

## When to Use

| Intent | Example Query |
|--------|-------------|
| Optimal pricing | "What's the best price for yoga mats?" |
| Price tier analysis | "Compare wireless earbuds sales by price tier" |
| Price ceiling/floor | "At what price point do sales drop off sharply in the $20–$50 range?" |
| Price compression trend | "Is there a price compression trend in the kitchen scale category?" |

### ⛔ Not Applicable

| Intent | Alternative Module |
|--------|-------------------|
| Single product price query | `info_search(mode="shopping")` |
| Sales estimates-based price elasticity curve | Pricing Strategy & Elasticity — Sales Estimates (within this skill) |
| Complete market analysis | `jungle-scout-deep-dive-analyzer` skill |

---

## Usage

Reference script: `scripts/product_database/pricing_strategy_elasticity.py`

```python
# Step 1: Fetch data via MCP
# 调用产品数据库工具获取数据
# Step 2: Pass MCP response to analysis script
import sys
sys.path.insert(0, '{SKILL_DIR}/scripts/product_database')
# Replace {SKILL_DIR} with the actual install dir, e.g.
# ${account_skills}/alibaba-amazon-market-intel
from pricing_strategy_elasticity import analyze
result = analyze(mcp_data=<mcp_response>, output_dir="/round-{N}/data")
```

---

## Execution Steps

### Step 1: Parse Category and Keywords

- Extract category and keywords from user query

### Step 2: Product Database Data Collection

- 调用 `js_product_database_query`，入参：`include_keywords`, `categories`, `marketplace`, `page_size`

### Step 3: Pricing Analysis Calculation

- Price tiers: dynamically tiered by quartiles (Budget / Mid-Range / Premium / Luxury)
- Elasticity curve: price vs sales scatter plot → fitted curve
- Price ceiling: price point where sales drop >50% compared to adjacent tier
- Price floor: price point where profit margin <15% (after FBA fees)
- Sweet spot: price range with highest revenue density (price × sales)

### Step 4: Deliver Results

- Output the key findings (tables, insights) directly in the conversation. Reference the CSV file for the complete dataset.

---

## Output Files

### `price_data.csv` — Category Pricing Data

| Column | Type | Description |
|--------|------|-------------|
| `asin` | string | Product ASIN |
| `price` | float | Price (USD) |
| `sales_cnt_30d` | int | 30-day estimated sales |
| `revenue_30d` | float | 30-day estimated revenue |
| `product_rank` | int | BSR rank |
| `reviews` | int | Review count |
| `seller_type` | string | Seller type |

---

## Notes

- This module performs price tier analysis based on cross-sectional data from the Product Database
- For time-series elasticity analysis based on daily price changes, use the Sales Estimates version of the pricing strategy module
- Price tier thresholds are dynamically calculated based on data distribution, not fixed values

