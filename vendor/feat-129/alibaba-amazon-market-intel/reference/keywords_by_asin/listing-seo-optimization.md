# Listing SEO Keyword Optimization

Based on the Jungle Scout keywords_by_asin API, collects keywords for the target ASIN
and outputs three SEO optimization keyword lists: Title/Bullet keywords, Quick Win keywords, and Rank Improvement keywords.

---

## When to Use

| Intent | Example Query |
|--------|-------------|
| Optimize listing title keywords | "Help me find keywords that should go in the title for ASIN B001XX" |
| Discover low-competition optimization opportunities | "Which keywords for B001XX have high search volume but are easy to rank?" |
| Find keywords with poor rankings to improve | "What keywords is B001XX indexed for but ranking poorly?" |
| Validate listing update effectiveness | "Re-analyze B001XX keyword coverage after listing modification" |

### ⛔ Not Applicable

| Intent | Alternative Module |
|--------|-------------------|
| Multi-ASIN comparative analysis | Keyword Gap Analysis (within this skill) |
| Keyword-based vocabulary expansion | `keyword-expansion` skill |

---

## Usage

```python
# Step 1: Fetch data via MCP
# 调用ASIN关键词工具获取数据
# Step 2: Pass MCP response to analysis script
import sys
sys.path.insert(0, '{SKILL_DIR}/scripts/keywords_by_asin')
# Replace {SKILL_DIR} with the actual install dir, e.g.
# ${account_skills}/alibaba-amazon-market-intel
from listing_seo_optimization import listing_seo_optimization

result = listing_seo_optimization(
    mcp_data=<mcp_response>,
    output_dir="/round-{N}/data",
    asin="B001MYASIN",                          # ASIN 标签（用于 CSV 标识）
    high_vol_threshold=1000,    # Title keyword search volume threshold (default 1000)
    easy_rank_threshold=60,     # Quick win ranking difficulty threshold (default 60)
)
# Returns dict: {"total_keywords", "title_bullet_count", "quick_win_count", "rank_improvement_count", ...}
```

---

## Execution Steps

### Step 1: Parse Input

- Extract target ASIN (1) and optional search volume/difficulty threshold parameters from user query

### Step 2: API Collection and Grouping

- 调用 `js_keywords_by_asin`，入参：`asin`, `page_size`
- Filter and group by three SEO dimensions

### Step 3: Deliver Results

- Output the key findings (tables, insights) directly in the conversation. Reference the CSV file for the complete dataset.

---

## Output Files

### `seo_keywords_raw.csv` — Complete Raw Data

All collected keyword raw data.

### `title_bullet_keywords.csv` — Title/Bullet Keywords

| Column | Description |
|--------|-------------|
| `asin` | Target ASIN |
| `name` | Keyword |
| `monthly_search_volume_exact` | Exact monthly search volume |
| `ease_of_ranking_score` | Ease of ranking score (0–100) |
| `organic_rank` | Current organic search rank |
| `ppc_bid_exact` | PPC exact bid (USD) |

Filter criteria: `monthly_search_volume_exact ≥ 1000`

### `quick_win_keywords.csv` — Quick Win Keywords

Filter criteria: search volume ≥ 500 and `ease_of_ranking_score ≥ 60`

### `rank_improvement_keywords.csv` — Rank Improvement Keywords

Filter criteria: `organic_rank > 20` (indexed but ranking poorly)

---

## Notes

- Only pass 1 ASIN (your own product)
- `high_vol_threshold` and `easy_rank_threshold` can be adjusted based on category competitiveness
- Rank improvement keywords are only effective when the API returns the `organic_rank` field

