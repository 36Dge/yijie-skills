# Content & SEO Strategy Planning

Based on the Jungle Scout keywords_by_keyword API, leverages search volume and ease of ranking data
to build a data-driven content strategy for product detail page titles/bullet points, A+ Content modules, and Brand Store.
Ensures every word in the detail page is backed by real search demand data.

---

## When to Use

| Intent | Example Query |
|--------|-------------|
| Detail page keyword prioritization | "Which keywords should go in the yoga mat detail page title?" |
| Discover easy-to-rank content opportunities | "Which yoga mat keywords are easy to rank but still have decent search volume?" |
| A+ Content module planning | "Plan A+ Content modules around yoga mat search themes" |
| Long-tail content strategy | "Find yoga mat long-tail keywords for Brand Store content" |

### ⛔ Not Applicable

| Intent | Alternative Module |
|--------|-------------------|
| PPC bid analysis | PPC Bid Strategy (within this skill) |
| Cross-product search volume comparison | Search Volume Benchmark (within this skill) |
| Category competitive landscape analysis | Category & Niche Mapping (within this skill) |

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
from content_seo import plan_content_seo

result = plan_content_seo(
    mcp_data=<mcp_response>,
    output_dir="/round-{N}/data",
    seed_keyword="yoga mat",                       # seed keyword (string)
    min_ease_for_opportunity=60,              # ease_of_ranking threshold (default 60)
)
# Returns dict: {"output_dir", "total_rows", "title_keywords", "opportunity_keywords",
#             "content_keyword_plan_csv"}
```

---

## Execution Steps

### Step 1: Parse Seed Keywords

- Extract 1–5 product seed keywords

### Step 2: API Data Collection

- Call `keywords_by_keyword` for each seed to collect keyword data

### Step 3: Calculate Content Priority

- content_priority_score = search volume × (ease_of_ranking / 100)
- Assign content placement by percentile

### Step 4: Deliver Results

- Output the key findings (tables, insights) directly in the conversation. Reference the CSV file for the complete dataset.

---

## Output Files

### `content_keyword_plan.csv` — Content Keyword Plan

| Column | Type | Description |
|--------|------|-------------|
| `seed_keyword` | string | Source seed keyword |
| `name` | string | Keyword |
| `monthly_search_volume_exact` | int | Monthly exact search volume |
| `ease_of_ranking_score` | int | Ease of ranking score (0–100) |
| `content_priority_score` | float | Content priority score |
| `content_placement` | string | Title Priority / Bullet Priority / A+ Theme / Long-tail Opportunity |
| `relevancy_score` | int | Relevancy score to seed keyword |
| `recommended_action` | string | Specific content recommendation |

content_placement classification rules:
- Title Priority: top 10% by content_priority_score
- Bullet Priority: top 10–30%
- A+ Theme: ease_of_ranking ≥ 60
- Long-tail Opportunity: remaining

---

## Notes

- content_priority_score considers both search volume and attainability, avoiding chasing high-volume keywords that are difficult to rank for
- A+ theme clustering: uses the first two words of the keyword as theme identifier
- Recommend first using Keyword Expansion to get a complete keyword library, then use this module for content allocation planning
- Maximum 5 seed keywords

