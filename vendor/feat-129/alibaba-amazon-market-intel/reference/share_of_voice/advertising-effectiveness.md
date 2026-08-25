# Advertising Effectiveness Assessment

Based on the Jungle Scout Share of Voice API, measures incremental visibility from paid placements relative to organic rankings,
identifies keywords where ad spend can be reduced or increased, and discovers competitor advertising weaknesses.

---

## When to Use

| Intent | Example Query |
|--------|-------------|
| Ad incremental assessment | "Which keywords are my ads actually generating incremental visibility on?" |
| Reduce ad spend | "Which keywords already rank well organically so I can reduce ads?" |
| Competitor ad weaknesses | "Which keywords do competitors have high ad share but weak organic rankings?" |
| Ad ROI optimization | "Where should I reallocate my ad budget across keywords?" |

### ⛔ Not Applicable

| Intent | Alternative Module |
|--------|-------------------|
| PPC bid amount estimation | `keywords_by_keyword/ppc-bid-strategy` |
| Ad keyword harvesting | `keywords_by_asin/ppc-keyword-harvesting` |
| Historical ad timing | `historical_search_volume/ad-campaign-timing` |

---

## Usage

Reference script: `scripts/share_of_voice/advertising_effectiveness.py`

```python
# Step 1: Fetch data via MCP
# 调用品牌份额工具获取数据
# Step 2: Pass MCP response to analysis script
import sys
sys.path.insert(0, '{SKILL_DIR}/scripts/share_of_voice')
# Replace {SKILL_DIR} with the actual install dir, e.g.
# ${account_skills}/alibaba-amazon-market-intel
from advertising_effectiveness import analyze
result = analyze(mcp_data=<mcp_response>, output_dir="/round-{N}/data")
```

---

## Execution Steps

### Step 1: Determine Keyword List

- Extract target keywords from user query
- Determine target marketplace

### Step 2: Pull SOV Data per Keyword

- 调用 `js_share_of_voice`，入参：`keyword`, `marketplace`
- Extract organic and sponsored SOV (weighted versions)

### Step 3: Advertising Effectiveness Analysis

- Calculate ad_incremental_lift = sponsored_sov - organic_sov
- Label ad strategy recommendations:
  - `reduce_spend`: high organic SOV but low sponsored SOV (already has organic advantage)
  - `increase_spend`: low organic SOV but has sponsored presence (needs ad support)
  - `maintain`: all other cases

### Step 4: Deliver Results

- Output the key findings (tables, insights) directly in the conversation. Reference the CSV file for the complete dataset.

---

## Output Files

### `advertising_effectiveness.csv` — Advertising Effectiveness Detail

| Column | Type | Description |
|--------|------|-------------|
| `keyword` | string | Keyword |
| `brand` | string | Brand name |
| `organic_sov_weighted` | float | Weighted organic SOV |
| `sponsored_sov_weighted` | float | Weighted sponsored SOV |
| `combined_sov_weighted` | float | Weighted combined SOV |
| `ad_incremental_lift` | float | Ad incremental lift (sponsored - organic) |
| `ad_strategy` | string | Strategy recommendation (reduce_spend/increase_spend/maintain) |
| `ppc_bid` | float | PPC bid (USD) |
| `search_volume_30d` | int | 30-day search volume |

---

## Notes

- Positive incremental lift indicates ads are generating additional visibility; negative indicates organic ranking already outperforms ads
- Recommend combining with PPC bid data to evaluate ad cost-effectiveness
- For competitor analysis, focus on brands with low organic_sov but high sponsored_sov (fragile ad-dependent positioning)
- Supported marketplaces: US, UK, DE, IN, CA, FR, IT, ES, MX, JP

