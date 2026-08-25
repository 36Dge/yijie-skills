# PPC Bid Strategy & Ad Budget Forecasting

Based on PPC bid data from the Jungle Scout keywords_by_keyword API,
plans ad budgets, derives competitive bidding strategies, identifies high-traffic low-CPC "quick win" keywords,
and calculates the total addressable ad spend for a product category.

---

## When to Use

| Intent | Example Query |
|--------|-------------|
| Estimate product ad budget | "How much PPC budget do I need to launch yoga mat?" |
| Find low-cost keyword opportunities | "Find high-traffic low-CPC keywords for wireless earbuds" |
| Compare broad vs exact match bids | "Is broad match or exact match more cost-effective for foam roller?" |
| Calculate total addressable ad spend | "What's the total addressable ad spend for the portable blender category?" |
| Develop pre-launch bid strategy | "Give me a PPC strategy for launching bamboo toothbrush on Amazon" |

### ⛔ Not Applicable

| Intent | Alternative Module |
|--------|-------------------|
| Single keyword bid query | 关键词搜索量工具 |
| Complete product market analysis | `jungle-scout-deep-dive-analyzer` skill |
| Keyword discovery and clustering | Keyword Expansion (within this skill) |

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
from ppc_bid_strategy import analyze_ppc_bids

result = analyze_ppc_bids(
    mcp_data=<mcp_response>,
    seed_keyword="yoga mat",                       # seed keyword (string)
    output_dir="/round-{N}/data",
    assumed_ctr=0.05,                         # Click-through rate assumption (default 5%)
    target_monthly_clicks=1000,               # Monthly target clicks
)
# Returns dict: {"output_dir", "total_keywords", "quick_win_count", "weighted_avg_cpc",
#             "total_addressable_spend", "budget_moderate_usd", "top_quick_win_keywords",
#             "bid_strategy_csv", "budget_forecast_csv"}
```

---

## Execution Steps

### Step 1: Parse Seed Keywords

- Extract 1–10 seed keywords, normalize to lowercase

### Step 2: Collect PPC Bid Data

- Call `keywords_by_keyword(page_size=100)` for each seed, deduplicate across seeds

### Step 3: Calculate Bid Metrics

- cpc_efficiency = exact search volume / ppc_bid_exact
- estimated_monthly_spend = exact search volume × CTR × ppc_bid_exact
- bid_tier: LOW (< $1) / MID ($1–$3) / HIGH (> $3)

### Step 4: Classify Keywords

- Quick Win: high traffic + low CPC → maximize ROI
- Competitive: high traffic + high CPC → brand exposure
- Long-tail: low traffic + low CPC → niche targeting
- High-Spend: high CPC → avoid unless brand building

### Step 5: Deliver Results

- Output the key findings (tables, insights) directly in the conversation. Reference the CSV file for the complete dataset.

---

## Output Files

### `bid_strategy.csv` — Per-Keyword Bid Strategy Table

| Column | Type | Description |
|--------|------|-------------|
| `keyword` | string | Search term |
| `seed_keyword` | string | Source seed keyword |
| `exact_volume` | int | Monthly exact match search volume |
| `ppc_bid_exact` | float | PPC bid estimate (USD) |
| `ease_of_ranking_score` | int | Ease of ranking score (0–100) |
| `organic_product_count` | int | Organic search result product count |
| `cpc_efficiency` | float | Traffic/bid ratio (higher is more cost-effective) |
| `estimated_monthly_spend` | float | Estimated monthly spend (USD) |
| `bid_tier` | string | LOW / MID / HIGH |
| `keyword_category` | string | Quick Win / Competitive / Long-tail / High-Spend |

### `budget_forecast.csv` — Budget Summary

Contains: total_keywords_analyzed, keywords_with_bid_data, quick_win_keyword_count,
total_addressable_spend_usd, weighted_avg_cpc_usd, budget_conservative/moderate/aggressive_usd,
top_quick_win_keywords.

---

## Notes

- CPC efficiency = traffic/bid; higher values mean more search exposure per dollar of bid
- Total addressable spend is the theoretical maximum (100% click share); actual spend is typically a small fraction
- assumed_ctr defaults to 5%; brand terms typically 8–12%, generic category terms 2–4%
- Budget tiers: conservative = 0.5×, moderate = 1.0×, aggressive = 2.0×
- Keywords with ppc_bid_exact = None are labeled as NO_BID_DATA

