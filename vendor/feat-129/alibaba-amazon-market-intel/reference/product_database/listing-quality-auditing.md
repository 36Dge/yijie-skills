# Listing Quality Auditing

Based on the Jungle Scout Product Database API, ranks a complete ASIN catalog by Listing Quality Score (LQS),
benchmarks against category top seller baselines, identifies optimization priorities, and supports periodic audits to track quality improvements.

---

## When to Use

| Intent | Example Query |
|--------|-------------|
| Catalog audit | "Audit the Listing quality for all my yoga mat ASINs" |
| Optimization priority | "Which Listings need optimization the most?" |
| Baseline benchmarking | "How do my Listings compare to top sellers?" |
| Periodic audit | "Run a quarterly Listing quality check" |

### ⛔ Not Applicable

| Intent | Alternative Module |
|--------|-------------------|
| Single ASIN LQS query | 产品数据库工具 |
| Complete market deep analysis | `jungle-scout-deep-dive-analyzer` skill |

---

## Usage

Reference script: `scripts/product_database/listing_quality_auditing.py`

```python
# ── Step 1: MCP 调用（需要两次：用户目录 + 类目基准） ──
# 第一次：获取用户自身 ASIN/品牌的产品数据
# accio-mcp-cli call js_product_database_query --json '{"include_keywords": ["your brand"], "marketplace": "us", "page_size": 50}'
# 第二次（可选）：获取类目 top seller 基准数据
# accio-mcp-cli call js_product_database_query --json '{"include_keywords": ["yoga mat"], "categories": [...], "marketplace": "us", "page_size": 50}'

# ── Step 2: 脚本分析 ──
import sys
sys.path.insert(0, '{SKILL_DIR}/scripts/product_database')
# Replace {SKILL_DIR} with the actual install dir, e.g.
# ${account_skills}/alibaba-amazon-market-intel
from listing_quality_auditing import analyze

result = analyze(
    mcp_user_data=<user_mcp_response>,           # 第一次 MCP 调用的返回（用户目录）
    mcp_benchmark_data=<benchmark_mcp_response>, # 第二次 MCP 调用的返回（可选，类目基准）
    output_dir="/round-{N}/data",
)
```

---

## Execution Steps

### Step 1: Parse User Catalog and Category

- Extract brand name/ASIN list and benchmark category keywords from user query

### Step 2: Product Database Data Collection

- Two separate calls: user catalog (by brand/keywords) + category benchmark (by category + keywords)
- Extract `listing_quality_score` (0–10 scale, higher is better)

### Step 3: Low LQS Product Keyword Coverage Analysis

- 调用 `js_keywords_by_asin` for ASINs with LQS below category average
- Identify keyword coverage gaps to explain low quality scores

### Step 4: Audit Metric Calculation

- Category average LQS, category Top 10 average LQS, user average LQS
- LQS gap = user LQS - category average LQS (per ASIN)
- Optimization priority = (category average LQS - ASIN LQS) × monthly revenue × (1 - keyword coverage rate)
- LQS distribution: 0–3 (poor), 3–5 (below average), 5–7 (average), 7–9 (good), 9–10 (excellent)

### Step 5: LLM-Generated Optimization Recommendations

- Generate per-ASIN recommendations: title optimization, image quality assessment, bullet point improvements, backend keyword suggestions
- Recommend A+ Content for high-revenue ASINs

### Step 6: Deliver Results

- Output the key findings (tables, insights) directly in the conversation. Reference the CSV file for the complete dataset.

---

## Output Files

### `catalog_lqs.csv` — Catalog LQS Data

| Column | Type | Description |
|--------|------|-------------|
| `source` | string | Data source (user / benchmark) |
| `asin` | string | Product ASIN |
| `title` | string | Product title |
| `brand` | string | Brand |
| `price` | float | Price (USD) |
| `sales_cnt_30d` | int | 30-day estimated sales |
| `revenue_30d` | float | 30-day estimated revenue (USD) |
| `reviews` | int | Review count |
| `rating` | float | Rating |
| `lqs` | float | Listing Quality Score (0–10) |
| `seller_type` | string | Seller type (FBA/FBM/AMZ) |

---

## Notes

- `listing_quality_score` is on a 0–10 scale; higher indicates better Listing quality
- For single ASIN LQS queries, use 产品数据库工具; this module is designed for batch auditing
- The optimization priority formula emphasizes high-revenue + large-gap + low-keyword-coverage ASINs
- Product Database returns a maximum of 50 results per call
- `categories` and `include_keywords` must be passed as list format

