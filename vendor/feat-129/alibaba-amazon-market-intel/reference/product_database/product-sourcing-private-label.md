# Product Sourcing & Private Label Opportunity

Based on the Jungle Scout Product Database API, filters lightweight small-sized products with healthy sales,
excludes categories with high brand monopoly, and cross-references Alibaba supplier data for profit analysis.

---

## When to Use

| Intent | Example Query |
|--------|-------------|
| Private label product selection | "Find products under 2 lbs with monthly revenue over $10K" |
| Sourcing feasibility | "Which Home & Kitchen products are easy to source from Alibaba?" |
| Profit analysis | "Compare yoga mat Amazon selling price vs Alibaba cost" |

### ⛔ Not Applicable

| Intent | Alternative Module |
|--------|-------------------|
| Alibaba supplier search only | 品搜工具 |
| Complete market deep analysis | `jungle-scout-deep-dive-analyzer` skill |

---

## Usage

Reference script: `scripts/product_database/product_sourcing_private_label.py`

```python
# Step 1: Fetch data via MCP
# 调用产品数据库工具获取数据
# Step 2: Pass MCP response to analysis script
import sys
sys.path.insert(0, '{SKILL_DIR}/scripts/product_database')
# Replace {SKILL_DIR} with the actual install dir, e.g.
# ${account_skills}/alibaba-amazon-market-intel
from product_sourcing_private_label import analyze
result = analyze(mcp_data=<mcp_response>, output_dir="/round-{N}/data")
```

---

## Execution Steps

### Step 1: Parse Categories and Filter Criteria

- Extract target category, keywords, weight threshold (default < 2 lbs), minimum revenue threshold (default $5K/month) from user query

### Step 2: Product Database Collection + Weight Filtering

- 调用 `js_product_database_query`，入参：`include_keywords`, `categories`, `page_size`
- Post-filter: `revenue >= 5000`
- Secondary filter: `weight` is not None and < 2 lbs (lightweight small-sized priority)

### Step 3: Exclude High-Monopoly Categories

- Call Share of Voice for candidate product keywords
- Categories where Top 1 brand share > 30% are flagged as high risk, not recommended for private label entry

### Step 4: Alibaba Supplier Search

- Call 品搜工具 for top candidate products to get supplier quotes, MOQ, and ratings
- Output `alibaba_supply.csv`

### Step 5: Profit Analysis

- Calculate: Amazon selling price - Alibaba unit price - shipping (weight × rate) - FBA fees = net profit
- Net profit margin > 25% flagged as viable candidate

### Step 6: Deliver Results

- Output the key findings (tables, insights) directly in the conversation. Reference the CSV file for the complete dataset.

---

## Output Files

### `sourcing_candidates.csv` — Sourcing Candidate Products

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
| `weight` | float | Weight (lbs) |
| `dimensions` | string | Dimensions |
| `seller_type` | string | Seller type (FBA/FBM/AMZ) |
| `category` | string | Category |
| `lqs` | float | Listing Quality Score (0–10) |

---

## Notes

- `weight` field may be `None`; post-filtering must be done in Python, cannot rely on API parameters
- Lightweight threshold is typically < 2 lbs, favorable for FBA fee control
- Net profit margin > 25% is the basic threshold for viable candidates
- `categories` and `include_keywords` must be passed as list format
- Alibaba supplier data is obtained via the 品搜工具 tool, not the Jungle Scout API

