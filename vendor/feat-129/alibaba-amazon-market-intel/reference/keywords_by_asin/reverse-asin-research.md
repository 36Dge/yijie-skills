# Reverse ASIN Keyword Research

Based on the Jungle Scout keywords_by_asin API, takes one or more ASINs as input
to discover the complete keyword profile driving traffic to the product, including search volume, PPC bids, ranking difficulty, organic/sponsored rank positions, and more.

---

## When to Use

| Intent | Example Query |
|--------|-------------|
| Understand competitor keyword strategy | "Analyze which keywords ASIN B08N5WRWNW ranks for" |
| Discover keywords competitors rank for that you don't | "What high-traffic keywords does this competitor ASIN have that I'm missing?" |
| Find long-tail low-competition keywords | "Find long-tail keyword opportunities for this ASIN" |
| Multi-ASIN horizontal comparison | "Analyze keywords for these three ASINs separately" |

### ⛔ Not Applicable

| Intent | Alternative Module |
|--------|-------------------|
| Keyword-based related word expansion | `keyword-expansion` skill |
| Multi-ASIN gap analysis | Keyword Gap Analysis (within this skill) |
| Multi-ASIN full catalog coverage audit | Multi-ASIN Keyword Portfolio (within this skill) |

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
from reverse_asin_research import reverse_asin_research

result = reverse_asin_research(
    mcp_data=<mcp_response>,
    output_dir="/round-{N}/data",
    asin="B08N5WRWNW",              # ASIN 标签（用于 CSV 标识）
    top_n=50,                        # Top-N keywords retained per ASIN in summary table
)
# Returns dict: {"output_dir", "total_rows", "rows_per_asin", "columns", "raw_csv", "summary_csv"}
```

---

## Execution Steps

### Step 1: Parse ASINs

- Extract 1–10 ASINs from user query
- If the user pastes IDs with `us/` prefix, the script automatically strips the prefix

### Step 2: API Data Collection

- 调用 `js_keywords_by_asin`，入参：`asin`, `page_size`（每个 ASIN 分别调用）
- 429/5xx errors trigger automatic exponential backoff retry; 422 errors are gracefully skipped

### Step 3: Deliver Results

- Output the key findings (tables, insights) directly in the conversation. Reference the CSV file for the complete dataset.

---

## Output Files

### `asin_keywords_raw.csv` — Complete Raw Data

| Column | Type | Description |
|--------|------|-------------|
| `asin` | string | Source ASIN |
| `name` | string | Keyword |
| `monthly_search_volume_exact` | int | Exact monthly search volume |
| `monthly_search_volume_broad` | int | Broad monthly search volume |
| `monthly_trend` | float | Monthly trend (% vs previous month) |
| `quarterly_trend` | float | Quarterly trend (% vs previous quarter) |
| `ppc_bid_broad` | float | PPC broad match recommended bid (USD) |
| `ppc_bid_exact` | float | PPC exact match recommended bid (USD) |
| `ease_of_ranking_score` | int | Ease of ranking score (0–100, higher is easier) |
| `organic_rank` | int | Organic search rank position |
| `sponsored_rank` | int | Sponsored ad rank position |
| `dominant_category` | string | Primary category |

### `top_keywords_summary.csv` — Top-N Summary

Sorted by `monthly_search_volume_exact` descending, Top-N keywords per ASIN.

---

## Notes

- ASIN format: pass plain ASINs (e.g., `B08N5WRWNW`), the script automatically handles `us/` prefix
- Maximum 10 ASINs: excess is automatically truncated
- `page_size`: controls the maximum rows collected per ASIN (upper limit 100)
- Rate limiting: 429/5xx errors trigger automatic exponential backoff retry; single ASIN failure does not affect the overall process

