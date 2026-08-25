# Market Opportunity Discovery

Based on the Jungle Scout Product Database API, filters by category, revenue, and review count
to discover high-revenue low-competition blue ocean niches, builds launch priority rankings,
and identifies white-space categories with low FBA seller penetration.

---

## When to Use

| Intent | Example Query |
|--------|-------------|
| Blue ocean niche discovery | "Find high-revenue low-review blue ocean opportunities in Home & Kitchen" |
| Launch priority ranking | "Scan 5 categories and rank by FBA launch priority" |
| White space analysis | "Which categories have low FBA seller penetration?" |
| Category scanning | "Find high-revenue niches in Home & Kitchen with under 200 reviews" |

### ⛔ Not Applicable

| Intent | Alternative Module |
|--------|-------------------|
| Single keyword search volume query | 关键词搜索量工具 |
| Single ASIN sales query | 销量估算工具 |
| Complete 8-dimension deep analysis | `jungle-scout-deep-dive-analyzer` skill |

---

## Usage

Reference script: `scripts/product_database/market_opportunity_discovery.py`

```python
# Step 1: Fetch data via MCP
# 调用产品数据库工具获取数据
# Step 2: Pass MCP response to analysis script
import sys
sys.path.insert(0, '{SKILL_DIR}/scripts/product_database')
# Replace {SKILL_DIR} with the actual install dir, e.g.
# ${account_skills}/alibaba-amazon-market-intel
from market_opportunity_discovery import analyze
result = analyze(mcp_data=<mcp_response>, output_dir="/round-{N}/data")
```

---

## Execution Steps

### Step 1: Parse Categories and Filter Criteria

- Extract target categories, minimum revenue threshold (default $10K/month), maximum review count (default 200) from user query

### Step 2: Product Database Data Collection

- 调用 `js_product_database_query`，入参：`categories`, `include_keywords`, `page_size`（每个 category 分别调用）
- Post-filter: `revenue >= 10000 AND reviews <= 200`

### Step 3: Niche Scoring Calculation

- Revenue Density (30%): average revenue within the category
- Competition Gap (25%): 1 - (avg_reviews / max_reviews)
- FBA Ratio (20%): FBA seller percentage
- Brand Dispersion (15%): 1 - Top 1 brand share
- Keyword Opportunity (10%): average ease of ranking score

### Step 4: Deliver Results

- Output the key findings (tables, insights) directly in the conversation. Reference the CSV file for the complete dataset.

---

## Output Files

### `niche_candidates.csv` — Filtered Niche Candidate Products

| Column | Type | Description |
|--------|------|-------------|
| `asin` | string | Product ASIN |
| `title` | string | Product title |
| `brand` | string | Brand |
| `price` | float | Price (USD) |
| `sales_cnt_30d` | int | 30-day estimated sales |
| `revenue_30d` | float | 30-day estimated revenue (USD) |
| `reviews` | int | Review count |
| `rating` | float | Rating |
| `seller_type` | string | Seller type (FBA/FBM/AMZ) |
| `category` | string | Category |
| `lqs` | float | Listing Quality Score (0–10) |

---

## Notes

- Product Database returns a maximum of 50 results per call; extrapolation is needed to estimate the full market
- Filter criteria (revenue, review count) are post-filtered in Python, not API parameters
- `categories` and `include_keywords` must be passed as list format
- White space determination: categories with FBA seller percentage < 40%

