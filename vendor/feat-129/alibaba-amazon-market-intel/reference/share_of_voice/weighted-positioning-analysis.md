# Weighted Positioning Analysis

Based on the Jungle Scout Share of Voice API, compares basic SOV vs weighted SOV,
analyzes page position quality, and tracks the impact of Amazon's Choice badges on visibility.

---

## When to Use

| Intent | Example Query |
|--------|-------------|
| Position quality assessment | "How is the quality of my product's ranking positions?" |
| Basic vs weighted comparison | "Do I have many search results but all in poor positions?" |
| Amazon's Choice tracking | "Which keywords have Amazon's Choice badges?" |
| Optimization priority | "Which keywords need ranking position improvement?" |

### ⛔ Not Applicable

| Intent | Alternative Module |
|--------|-------------------|
| Keyword rank tracking | `keywords_by_asin/share-of-search-tracking` |
| Listing quality scoring | `product_database/listing-quality-auditing` |
| Search volume historical trends | `historical_search_volume/seasonal-demand-profiling` |

---

## Usage

Reference script: `scripts/share_of_voice/weighted_positioning_analysis.py`

```python
# Step 1: Fetch data via MCP
# 调用品牌份额工具获取数据
# Step 2: Pass MCP response to analysis script
import sys
sys.path.insert(0, '{SKILL_DIR}/scripts/share_of_voice')
# Replace {SKILL_DIR} with the actual install dir, e.g.
# ${account_skills}/alibaba-amazon-market-intel
from weighted_positioning_analysis import analyze
result = analyze(mcp_data=<mcp_response>, output_dir="/round-{N}/data")
```

---

## Execution Steps

### Step 1: Determine Keyword List

- Extract target keywords from user query
- Determine target marketplace

### Step 2: Pull SOV Data per Keyword

- 调用 `js_share_of_voice`，入参：`keyword`, `marketplace`
- Extract both basic and weighted SOV metrics

### Step 3: Positioning Quality Analysis

- Calculate `position_quality_gap` = weighted_sov - basic_sov
  - Positive → `premium`: products in premium positions (front page + badge boost)
  - Negative → `poor`: many product listings but in poor positions
  - Near zero → `neutral`: average position quality
- Flag Amazon's Choice badges

### Step 4: Deliver Results

- Output the key findings (tables, insights) directly in the conversation. Reference the CSV file for the complete dataset.

---

## Output Files

### `weighted_positioning_analysis.csv` — Weighted Positioning Detail

| Column | Type | Description |
|--------|------|-------------|
| `keyword` | string | Keyword |
| `brand` | string | Brand name |
| `organic_sov_basic` | float | Basic organic SOV |
| `organic_sov_weighted` | float | Weighted organic SOV |
| `sponsored_sov_basic` | float | Basic sponsored SOV |
| `sponsored_sov_weighted` | float | Weighted sponsored SOV |
| `combined_sov_basic` | float | Basic combined SOV |
| `combined_sov_weighted` | float | Weighted combined SOV |
| `position_quality_gap` | float | Positioning quality gap (weighted - basic) |
| `position_quality` | string | Position quality (premium/neutral/poor) |
| `amazons_choice` | bool | Whether Amazon's Choice badge is present |
| `search_volume_30d` | int | 30-day search volume |
| `ppc_bid` | float | PPC bid (USD) |

---

## Notes

- Weighted SOV accounts for page position weight (page 1 > page 2 > page 3) and Amazon's Choice badge boost
- `position_quality_gap` > 0.05 indicates premium positioning; < -0.05 indicates ranking position needs optimization
- Amazon's Choice badges significantly boost weighted SOV
- Supported marketplaces: US, UK, DE, IN, CA, FR, IT, ES, MX, JP

