# Cross-Market Demand Comparison

Based on the Jungle Scout keywords_by_keyword API, runs the same set of seed keywords across multiple Amazon marketplaces
(US / UK / DE / CA, etc.), compares search demand, bid levels, and ease of ranking across markets,
and identifies "high demand, low competition" market expansion opportunities.

---

## When to Use

| Intent | Example Query |
|--------|-------------|
| Evaluate market expansion priority | "Which market has the biggest opportunity for yoga mat: US, UK, or Germany?" |
| Cross-market demand comparison | "How do search volume and bids differ for the same product across markets?" |
| Identify low-competition overseas markets | "Which market has the lowest competition for yoga mat?" |
| Validate localization strategy | "How does the demand landscape differ between German and English keywords?" |

### ⛔ Not Applicable

| Intent | Alternative Module |
|--------|-------------------|
| Single-market deep keyword analysis | Keyword Expansion (within this skill) |
| Complete market competition analysis | `jungle-scout-deep-dive-analyzer` skill |
| Ad budget planning | PPC Bid Strategy (within this skill) |

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
from compare_markets import compare_markets

result = compare_markets(
    mcp_data=<mcp_response>,
    output_dir="/round-{N}/data",
    seed_keyword="yoga mat",                       # seed keyword (string)
    marketplace="US",                              # 单个市场标签（用于 CSV 标识）
)
# Returns dict: {"output_dir", "total_rows", "best_market_per_seed",
#             "opportunity_markets", "market_summary_csv", "cross_market_raw_csv"}
```

---

## Execution Steps

### Step 1: Parse Seed Keywords and Target Markets

- Extract 1–5 seed keywords and marketplace list

### Step 2: Cross-Market Data Collection

- Call `keywords_by_keyword` for each "seed keyword × marketplace" combination

### Step 3: Aggregate and Rank

- Calculate opportunity_score = total_exact_volume / (1 + avg_ppc_bid_exact)
- Rank markets within each seed keyword

### Step 4: Deliver Results

- Output the key findings (tables, insights) directly in the conversation. Reference the CSV file for the complete dataset.

---

## Supported Marketplace Codes

US (United States), UK (United Kingdom), DE (Germany), CA (Canada), FR (France),
IT (Italy), ES (Spain), JP (Japan), MX (Mexico), BR (Brazil)

---

## Output Files

### `market_summary.csv` — Market-Level Summary

| Column | Type | Description |
|--------|------|-------------|
| `seed_keyword` | string | Seed keyword |
| `marketplace` | string | Marketplace code |
| `keyword_count` | int | Number of keywords collected |
| `avg_exact_volume` | float | Average monthly exact search volume |
| `total_exact_volume` | int | Total exact search volume |
| `avg_ppc_bid_exact` | float | Average exact match bid (USD) |
| `avg_ease_of_ranking` | float | Average ease of ranking score |
| `opportunity_score` | float | Opportunity score |
| `market_rank` | int | Market opportunity rank (1 = best) |

### `cross_market_raw.csv` — Raw Keyword Detail

Contains raw keyword data for all marketplace × seed keyword combinations, with an additional `marketplace` column.

---

## Notes

- opportunity_score = total search volume / (1 + average bid): higher search volume and lower bids yield higher scores
- Absolute search volumes across different markets are not directly comparable (different user bases per country)
- Non-English markets require local language keywords for complete data
- Each "seed keyword × marketplace" combination counts as one API call; be mindful of rate limits
- Maximum 5 seed keywords

