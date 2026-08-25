# Keyword Expansion

Based on the Jungle Scout keywords_by_keyword API, discovers 100+ related search terms (including long-tail variants) from seed keywords,
deduplicates and outputs a complete keyword database with search volume, PPC bids, and ranking difficulty.

---

## When to Use

| Intent | Example Query |
|--------|-------------|
| Build a complete keyword library | "Find all keywords related to yoga mat" |
| Discover long-tail variants | "What long-tail keywords exist for wireless earbuds?" |
| Identify sub-niche clusters | "Cluster portable blender keywords by sub-niche" |
| Validate category coverage | "Is my Home & Kitchen product keyword coverage complete?" |
| Multi-seed expansion | "Expand from these keywords: yoga mat, exercise mat, gym mat" |

### ⛔ Not Applicable

| Intent | Alternative Module |
|--------|-------------------|
| Single keyword search volume query | 关键词搜索量工具 |
| ASIN keyword rankings | Reverse ASIN Research (within this skill) |
| Complete product market analysis | `jungle-scout-deep-dive-analyzer` skill |

---

## Usage

```python
# Step 1: Fetch data via MCP
# 调用关键词搜索量工具获取数据
# Step 2: Pass MCP response to analysis script
import sys
sys.path.insert(0, '{SKILL_DIR}/scripts/keywords_by_keyword')
# Replace {SKILL_DIR} with the actual install dir, e.g.
# ${account_skills}/alibaba-amazon-market-intel
from expand_keywords import expand_keywords

result = expand_keywords(
    mcp_data=<mcp_response>,
    output_dir="/round-{N}/data",
    seed_keyword="yoga mat",                       # seed keyword (string)
)
# Returns dict: {"output_dir", "total_rows", "rows_per_seed", "columns", "keyword_expansion_csv"}
```

---

## Execution Steps

### Step 1: Parse Seed Keywords

- Extract 1–10 seed keywords from user query
- Multiple keywords (comma-separated or list format) are all used, normalized to lowercase

### Step 2: API Data Collection

- Call `keywords_by_keyword(search_terms=seed, page_size=100)` for each seed
- 429/5xx errors trigger automatic exponential backoff retry; 422 errors are gracefully skipped

### Step 3: Deliver Results

- Output the key findings (tables, insights) directly in the conversation. Reference the CSV file for the complete dataset.

---

## Output Files

### `keyword_expansion.csv` — Complete Keyword Table

| Column | Type | Description |
|--------|------|-------------|
| `seed_keyword` | string | Source seed keyword |
| `country` | string | Marketplace code (e.g., us) |
| `name` | string | Keyword |
| `monthly_trend` | float | Monthly trend (%) |
| `monthly_search_volume_exact` | int | Exact match monthly search volume |
| `quarterly_trend` | float | Quarterly trend (%) |
| `monthly_search_volume_broad` | int | Broad match monthly search volume |
| `dominant_category` | string | Primary category |
| `recommended_promotions` | int | Recommended promotion count |
| `sp_brand_ad_bid` | float | Brand ad recommended bid (USD) |
| `ppc_bid_broad` | float | PPC broad match recommended bid (USD) |
| `ppc_bid_exact` | float | PPC exact match recommended bid (USD) |
| `ease_of_ranking_score` | int | Ease of ranking score (0–100) |
| `relevancy_score` | int | Relevancy score to seed keyword |
| `organic_product_count` | int | Organic search result product count |
| `sponsored_product_count` | int | Sponsored product count |

---

## Notes

- Maximum 10 seeds: excess is automatically truncated
- `page_size` controls both the API per-page request count and the max rows collected per seed
- Rate limiting: 429/5xx errors trigger automatic exponential backoff retry; single seed failure does not affect overall execution
- Empty results: seeds returning empty data print a warning and are skipped
- Local debugging: authentication is handled server-side

