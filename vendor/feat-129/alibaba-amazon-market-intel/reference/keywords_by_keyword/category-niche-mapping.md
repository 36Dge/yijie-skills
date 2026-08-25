# Category & Niche Mapping

Based on the Jungle Scout keywords_by_keyword API, groups keywords by dominant_category,
reveals which categories are competing for the same search traffic, maps competition density,
and identifies low-competition niches and cross-category positioning opportunities.

---

## When to Use

| Intent | Example Query |
|--------|-------------|
| Understand search traffic attribution | "Which categories does yoga mat search traffic mainly belong to?" |
| Cross-category opportunity mining | "Can yoga mat appear in multiple different categories simultaneously?" |
| Identify low-competition niches | "Which yoga mat related categories have the fewest sponsored products?" |
| Category selection for listing | "Which category should my product be listed in first?" |

### ⛔ Not Applicable

| Intent | Alternative Module |
|--------|-------------------|
| Keyword search volume benchmarking | Search Volume Benchmark (within this skill) |
| Complete market analysis | `jungle-scout-deep-dive-analyzer` skill |
| PPC bid strategy | PPC Bid Strategy (within this skill) |

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
from map_niches import map_niches

result = map_niches(
    mcp_data=<mcp_response>,
    output_dir="/round-{N}/data",
    seed_keyword="yoga mat",                       # seed keyword (string)
)
# Returns dict: {"output_dir", "total_rows", "top_categories", "low_competition_categories",
#             "cross_category_keywords", "category_summary_csv", "keyword_by_category_csv"}
```

---

## Execution Steps

### Step 1: Parse Seed Keywords

- Extract 1–10 seed keywords

### Step 2: API Data Collection

- Call `keywords_by_keyword` for each seed to collect keywords + category data

### Step 3: Category Grouping and Competition Analysis

- Group by dominant_category, calculate category-level metrics
- Identify cross-category keywords (same keyword name appearing in multiple categories)

### Step 4: Deliver Results

- Output the key findings (tables, insights) directly in the conversation. Reference the CSV file for the complete dataset.

---

## Output Files

### `category_summary.csv` — Category-Level Summary

| Column | Type | Description |
|--------|------|-------------|
| `dominant_category` | string | Category name |
| `keyword_count` | int | Number of keywords in this category |
| `total_exact_volume` | int | Total exact search volume within the category |
| `avg_exact_volume` | float | Average exact search volume |
| `avg_sponsored_count` | float | Average sponsored product count |
| `avg_ease_of_ranking` | float | Average ease of ranking score |
| `top_keyword` | string | Highest search volume keyword in the category |
| `competition_level` | string | LOW / MEDIUM / HIGH |

### `keyword_by_category.csv` — Keyword-Level Detail

| Column | Type | Description |
|--------|------|-------------|
| `seed_keyword` | string | Source seed keyword |
| `name` | string | Keyword |
| `dominant_category` | string | Primary category |
| `monthly_search_volume_exact` | int | Monthly exact search volume |
| `sponsored_product_count` | int | Sponsored product count |
| `ease_of_ranking_score` | int | Ease of ranking score |
| `is_cross_category` | bool | Whether it appears across multiple categories |

---

## Notes

- Competition density thresholds: avg_sponsored_count < 5 = LOW, 5–20 = MEDIUM, > 20 = HIGH
- Cross-category keywords indicate the keyword attracts buyers from different categories
- Data reflects a point-in-time snapshot; recommend re-running periodically

