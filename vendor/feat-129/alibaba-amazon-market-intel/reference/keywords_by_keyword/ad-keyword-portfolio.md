# Ad Keyword Portfolio Builder

Based on the Jungle Scout keywords_by_keyword API, builds structured keyword portfolios for SP / SB / SD ad campaigns,
uses relevancy scores to tier keywords into exact/phrase/broad match groups, segments campaigns by CPC tier,
and identifies Sponsored Brand (SB) bidding opportunities.

---

## When to Use

| Intent | Example Query |
|--------|-------------|
| Build ad account structure | "Help me build a complete PPC ad keyword portfolio for yoga mat" |
| Tier match types | "How should yoga mat keywords be allocated to exact/phrase/broad match?" |
| Identify brand ad opportunities | "Which yoga mat keywords have SB ad bid data?" |
| Separate high/low CPC campaigns | "Split yoga mat keywords into two campaigns by CPC level" |

### ⛔ Not Applicable

| Intent | Alternative Module |
|--------|-------------------|
| Ad budget total forecasting | PPC Bid Strategy (within this skill) |
| Keyword search volume validation | Search Volume Benchmark (within this skill) |
| Keyword discovery and expansion | Keyword Expansion (within this skill) |

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
from ad_portfolio import build_ad_portfolio

result = build_ad_portfolio(
    mcp_data=<mcp_response>,
    output_dir="/round-{N}/data",
    seed_keyword="yoga mat",                       # seed keyword (string)
)
# Returns dict: {"output_dir", "total_keywords", "sb_opportunity_keywords",
#             "campaign_count", "ad_keyword_portfolio_csv", "campaign_structure_csv"}
```

---

## Execution Steps

### Step 1: Parse Seed Keywords

- Extract 1–10 seed keywords

### Step 2: API Data Collection

- Call `keywords_by_keyword` for each seed to collect keywords + bid data

### Step 3: Assign Match Types and Campaigns

- Assign by relevancy_score: > 100 exact match, 60–100 phrase match, < 60 broad match
- Assign CPC tier by ppc_bid_exact: LOW / MID / HIGH
- Generate suggested_campaign names

### Step 4: Deliver Results

- Output the key findings (tables, insights) directly in the conversation. Reference the CSV file for the complete dataset.

---

## Output Files

### `ad_keyword_portfolio.csv` — Keyword-Level Ad Plan

| Column | Type | Description |
|--------|------|-------------|
| `seed_keyword` | string | Source seed keyword |
| `name` | string | Keyword |
| `monthly_search_volume_exact` | int | Monthly exact search volume |
| `relevancy_score` | int | Relevancy score |
| `ppc_bid_exact` | float | Exact match bid (USD) |
| `ppc_bid_broad` | float | Broad match bid (USD) |
| `sp_brand_ad_bid` | float | Brand ad bid (USD) |
| `match_type` | string | Exact Match / Phrase Match / Broad Match |
| `cpc_tier` | string | LOW / MID / HIGH |
| `suggested_campaign` | string | Suggested ad campaign name |
| `sb_opportunity` | bool | Whether SB ad bid data is available |

### `campaign_structure.csv` — Ad Campaign Structure Summary

| Column | Type | Description |
|--------|------|-------------|
| `campaign_name` | string | Suggested ad campaign name |
| `match_type` | string | Match type |
| `cpc_tier` | string | CPC tier |
| `keyword_count` | int | Number of keywords |
| `avg_bid` | float | Average bid |
| `total_volume` | int | Total keyword search volume |

---

## Notes

- relevancy_score has no fixed upper bound (can exceed 100 in practice); 100 is used as the exact/phrase split threshold
- SB opportunity: keywords where sp_brand_ad_bid has a value > 0
- Recommend creating separate campaigns for high CPC keywords to independently control budget caps
- Broad match campaigns are typically used for keyword discovery; regularly extract converting keywords to exact match campaigns

