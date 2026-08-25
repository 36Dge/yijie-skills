# Keyword-Level Competitive Intelligence

Based on the Jungle Scout Share of Voice API, analyzes brand concentration and competitive structure for each keyword,
identifies fragmented market opportunities and monopolized high-barrier keywords.

---

## When to Use

| Intent | Example Query |
|--------|-------------|
| Brand concentration analysis | "Which keywords are monopolized by a few brands?" |
| Fragmented market opportunities | "Which keywords have dispersed competition and are suitable for entry?" |
| Competition intensity assessment | "How intense is the competition for this keyword?" |
| Keyword prioritization | "Which keywords should I invest in first?" |

### ⛔ Not Applicable

| Intent | Alternative Module |
|--------|-------------------|
| Keyword search volume trends | `historical_search_volume/year-over-year-growth` |
| Keyword expansion and discovery | `keywords_by_keyword/keyword-expansion` |
| Category competitive landscape | `product_database/competitive-landscape-analysis` |

---

## Usage

Reference script: `scripts/share_of_voice/keyword_competitive_intel.py`

```python
# Step 1: Fetch data via MCP
# 调用品牌份额工具获取数据
# Step 2: Pass MCP response to analysis script
import sys
sys.path.insert(0, '{SKILL_DIR}/scripts/share_of_voice')
# Replace {SKILL_DIR} with the actual install dir, e.g.
# ${account_skills}/alibaba-amazon-market-intel
from keyword_competitive_intel import analyze
result = analyze(mcp_data=<mcp_response>, output_dir="/round-{N}/data")
```

---

## Execution Steps

### Step 1: Determine Keyword List

- Extract target keywords from user query
- Determine target marketplace

### Step 2: Pull SOV Data per Keyword

- 调用 `js_share_of_voice`，入参：`keyword`, `marketplace`

### Step 3: Competitive Structure Analysis

- Calculate brand concentration metrics per keyword:
  - `top3_brand_share`: total SOV of the top 3 brands
  - `total_brands`: total number of competing brands
  - `concentration`: dominated (>60%) / moderate / fragmented (<30%)
- Output keyword × brand detail

### Step 4: Deliver Results

- Output the key findings (tables, insights) directly in the conversation. Reference the CSV file for the complete dataset.

---

## Output Files

### `keyword_competitive_intel.csv` — Keyword Competitive Structure

| Column | Type | Description |
|--------|------|-------------|
| `keyword` | string | Keyword |
| `total_brands` | int | Number of competing brands |
| `top3_brand_share` | float | Top 3 brands total SOV |
| `concentration` | string | Concentration level (dominated/moderate/fragmented) |
| `top_brand` | string | Brand with highest SOV |
| `top_brand_sov` | float | Highest brand's SOV |

### `keyword_brand_detail.csv` — Keyword × Brand Detail

| Column | Type | Description |
|--------|------|-------------|
| `keyword` | string | Keyword |
| `brand` | string | Brand name |
| `combined_sov_weighted` | float | Weighted combined SOV |
| `organic_sov_weighted` | float | Weighted organic SOV |
| `sponsored_sov_weighted` | float | Weighted sponsored SOV |
| `search_volume_30d` | int | 30-day search volume |

---

## Notes

- `dominated` keywords (top3 > 60%) have high entry costs, requiring significant ad budget
- `fragmented` keywords (top3 < 30%) represent entry opportunities with dispersed competition
- Recommend combining with search volume data, prioritizing high search volume + fragmented keywords
- Supported marketplaces: US, UK, DE, IN, CA, FR, IT, ES, MX, JP

