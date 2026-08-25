# Brand Market Share Measurement

Based on the Jungle Scout Share of Voice API, quantifies brand share of voice across the top 3 pages of Amazon search results,
creates a cross-keyword composite market share score, compares competitor brands, and distinguishes organic vs paid visibility.

---

## When to Use

| Intent | Example Query |
|--------|-------------|
| Brand composite SOV score | "Calculate my brand's composite market share across the top 50 keywords" |
| Competitor brand comparison | "Compare my SOV against the top 3 competitors on core keywords" |
| Organic vs paid breakdown | "How much of my visibility comes from organic ranking vs ads?" |
| Brand positioning assessment | "What's my competitive position in the Bluetooth earbuds category?" |

### ⛔ Not Applicable

| Intent | Alternative Module |
|--------|-------------------|
| Single ASIN keyword rankings | `keywords_by_asin/reverse-asin-research` |
| Historical search volume trends | `historical_search_volume/seasonal-demand-profiling` |
| Brand product portfolio and revenue analysis | `product_database/brand-seller-intelligence` |

---

## Usage

Reference script: `scripts/share_of_voice/brand_market_share.py`

```python
# Step 1: Fetch data via MCP
# 调用品牌份额工具获取数据
# Step 2: Pass MCP response to analysis script
import sys
sys.path.insert(0, '{SKILL_DIR}/scripts/share_of_voice')
# Replace {SKILL_DIR} with the actual install dir, e.g.
# ${account_skills}/alibaba-amazon-market-intel
from brand_market_share import analyze
result = analyze(mcp_data=<mcp_response>, output_dir="/round-{N}/data")
```

---

## Execution Steps

### Step 1: Determine Keyword List

- Extract target keywords (up to 50) from user query
- Determine target marketplace (US/UK/DE/IN/CA/FR/IT/ES/MX/JP)

### Step 2: Pull SOV Data per Keyword

- 调用 `js_share_of_voice`，入参：`keyword`, `marketplace`
- Extract organic/sponsored/combined SOV (both basic and weighted versions)

### Step 3: Brand-Level Aggregation

- Calculate average combined_sov_weighted per brand across keywords (composite market share score)
- Break down organic vs sponsored share
- Rank brands by SOV descending

### Step 4: Deliver Results

- Output the key findings (tables, insights) directly in the conversation. Reference the CSV file for the complete dataset.

---

## Output Files

### `brand_sov_summary.csv` — Brand SOV Summary

| Column | Type | Description |
|--------|------|-------------|
| `brand` | string | Brand name |
| `keyword_count` | int | Number of keywords covered |
| `avg_combined_sov_weighted` | float | Average weighted combined SOV |
| `avg_organic_sov_weighted` | float | Average weighted organic SOV |
| `avg_sponsored_sov_weighted` | float | Average weighted sponsored SOV |
| `total_combined_sov_basic` | float | Total basic combined SOV |

### `brand_market_share_detail.csv` — Keyword × Brand Detail

| Column | Type | Description |
|--------|------|-------------|
| `keyword` | string | Keyword |
| `brand` | string | Brand name |
| `organic_sov_basic` | float | Basic organic SOV |
| `sponsored_sov_basic` | float | Basic sponsored SOV |
| `combined_sov_basic` | float | Basic combined SOV |
| `organic_sov_weighted` | float | Weighted organic SOV |
| `sponsored_sov_weighted` | float | Weighted sponsored SOV |
| `combined_sov_weighted` | float | Weighted combined SOV |
| `search_volume_30d` | int | 30-day search volume |
| `ppc_bid` | float | PPC bid (USD) |

---

## Notes

- SOV data covers the top 3 pages of Amazon search results (approximately 48 organic positions + ad positions)
- Weighted SOV accounts for page position weight and Amazon's Choice badge boost
- Recommend covering at least 10 core keywords for a meaningful composite score
- Supported marketplaces: US, UK, DE, IN, CA, FR, IT, ES, MX, JP

