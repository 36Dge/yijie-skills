# Category Market Sizing

Based on the Jungle Scout Product Database API, aggregates estimated monthly revenue within a category and extrapolates annual market size,
supports cross-market (US/UK/DE) comparison and market structure segmentation by price tier/seller type.

---

## When to Use

| Intent | Example Query |
|--------|-------------|
| Market size estimation | "What's the annual market size for yoga mats on Amazon US?" |
| Cross-market comparison | "Compare pet supplies market size: US vs UK vs Germany" |
| Market structure segmentation | "Segment the kitchen scale market structure by price tier" |
| Management briefing | "Prepare a market sizing briefing for management" |

### ⛔ Not Applicable

| Intent | Alternative Module |
|--------|-------------------|
| Single keyword search volume | 关键词搜索量工具 |
| Competitive landscape analysis | Competitive Landscape Analysis (within this skill) |

---

## Usage

Reference script: `scripts/product_database/category_market_sizing.py`

```python
# Step 1: Fetch data via MCP
# 调用产品数据库工具获取数据
# Step 2: Pass MCP response to analysis script
import sys
sys.path.insert(0, '{SKILL_DIR}/scripts/product_database')
# Replace {SKILL_DIR} with the actual install dir, e.g.
# ${account_skills}/alibaba-amazon-market-intel
from category_market_sizing import analyze
result = analyze(mcp_data=<mcp_response>, output_dir="/round-{N}/data")
```

---

## Execution Steps

### Step 1: Parse Category and Target Markets

- Extract category and market list from user query (default US only)

### Step 2: Cross-Market Product Database Data Collection

- 调用 `js_product_database_query`，入参：`include_keywords`, `categories`, `marketplace`, `page_size`（每个市场分别调用）
- `marketplace` must use `Marketplace.US` / `Marketplace.UK` / `Marketplace.DE` enums

### Step 3: Market Size Calculation

- Supply-side estimation: Sample Revenue = sum(revenue_30d), Coverage Factor = 30–60%, Monthly Size = Sample / Factor, Annual Size = Monthly × 12
- Market structure segmentation: segment by price quartiles → revenue share per tier; segment by seller type
- Cross-market comparison: monthly revenue, annual estimate, average price, product count per market

### Step 4: Deliver Results

- Output the key findings (tables, insights) directly in the conversation. Reference the CSV file for the complete dataset.

---

## Output Files

### `category_data.csv` — Category Product Data (with market label)

| Column | Type | Description |
|--------|------|-------------|
| `marketplace` | string | Marketplace code (US/UK/DE) |
| `asin` | string | Product ASIN |
| `price` | float | Price |
| `revenue_30d` | float | 30-day estimated revenue |
| `sales_cnt_30d` | int | 30-day estimated sales |
| `seller_type` | string | Seller type |
| `category` | string | Category |

---

## Notes

- Product Database returns a maximum of 50 results per call; extrapolation is needed to estimate full market size
- Coverage Factor is typically 30–60%, depending on category concentration
- When comparing across markets, absolute search volumes are not directly comparable (different user bases per country)
- `marketplace` must use enum types, not strings

