# Market Entry Keyword Research

Based on the Jungle Scout keywords_by_asin API, collects keywords from 3–10 top seller ASINs in the target category
to quickly build a complete keyword landscape for the category and identify core keywords and entry opportunity keywords.

---

## When to Use

| Intent | Example Query |
|--------|-------------|
| Keyword research before entering a new category | "I want to enter the yoga mat category, analyze the top sellers' keywords" |
| Quickly understand category keyword scale | "How large is the keyword universe for Home & Kitchen?" |
| Validate new product demand | "Is the search volume for these ASINs' keywords large enough to enter?" |

### ⛔ Not Applicable

| Intent | Alternative Module |
|--------|-------------------|
| Single competitor deep keyword analysis | Reverse ASIN Research (within this skill) |
| Competitor vs own gap analysis | Keyword Gap Analysis (within this skill) |

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
from market_entry_research import market_entry_research

result = market_entry_research(
    mcp_data=<mcp_response>,
    output_dir="/round-{N}/data",
    source_asin="B001T1",                # ASIN 标签（用于 CSV 标识）
    category_name="yoga mat",            # Category name (for labeling)
    core_kw_vol_threshold=1000,          # Core keyword search volume threshold (default 1000)
    entry_ease_threshold=65,             # Entry keyword ranking difficulty threshold (default 65)
    entry_vol_min=300,                   # Entry keyword minimum search volume (default 300)
)
# Returns dict: {"total_unique_keywords", "core_keyword_count", "entry_opportunity_count", ...}
```

---

## Execution Steps

### Step 1: Parse Input

- Extract category name and top seller ASINs (3–10) from user query

### Step 2: API Collection and Classification

- 调用 `js_keywords_by_asin`，入参：`asin`, `page_size`（每个 ASIN 分别调用）
- Deduplicate to build the category keyword landscape, filter core keywords and entry opportunity keywords

### Step 3: Deliver Results

- Output the key findings (tables, insights) directly in the conversation. Reference the CSV file for the complete dataset.

---

## Output Files

### `market_keywords_raw.csv` — All Raw Data (with source ASIN)

### `category_keyword_universe.csv` — Deduplicated Category Keyword Landscape

| Column | Description |
|--------|-------------|
| `source_asin` | Source top seller ASIN |
| `category` | Category name |
| `name` | Keyword |
| `monthly_search_volume_exact` | Exact monthly search volume |
| `ease_of_ranking_score` | Ease of ranking score (0–100) |
| `ppc_bid_exact` | PPC exact bid (USD) |
| `dominant_category` | Dominant category in search results |

### `core_keywords.csv` — Core Keywords (search volume ≥ 1000)

### `entry_opportunity.csv` — Entry Opportunity Keywords (search volume ≥ 300 and ease_of_ranking ≥ 65)

---

## Notes

- Recommend passing 3–5 top seller ASINs (Top 3–Top 5 from bestseller list) for optimal coverage
- `category_name` is only used for labeling in output files, does not affect API calls
- Entry opportunity keyword thresholds can be adjusted based on category competitiveness (for highly competitive categories, consider raising `entry_ease_threshold` to 70+)

