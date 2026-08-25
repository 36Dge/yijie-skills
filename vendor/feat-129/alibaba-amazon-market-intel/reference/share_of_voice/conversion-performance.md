# Product Conversion Performance Insights

Based on the Jungle Scout Share of Voice API, analyzes click and conversion data for the Top 3 ASINs under each keyword,
revealing which products are truly winning the search traffic.

---

## When to Use

| Intent | Example Query |
|--------|-------------|
| Keyword conversion winners | "Which ASINs get the most clicks on this keyword?" |
| Competitor conversion analysis | "Which competitor products convert best on core keywords?" |
| Product strategy reference | "What's the pricing and positioning of high-converting ASINs?" |
| New product threat detection | "Are any new ASINs quickly entering the top conversion positions?" |

### ⛔ Not Applicable

| Intent | Alternative Module |
|--------|-------------------|
| ASIN sales estimation | `sales_estimates/competitive-sales-tracking` |
| ASIN keyword landscape | `keywords_by_asin/reverse-asin-research` |
| ASIN detailed data enrichment | `product_database/asin-deep-dive-enrichment` |

---

## Usage

Reference script: `scripts/share_of_voice/conversion_performance.py`

```python
# Step 1: Fetch data via MCP
# 调用品牌份额工具获取数据
# Step 2: Pass MCP response to analysis script
import sys
sys.path.insert(0, '{SKILL_DIR}/scripts/share_of_voice')
# Replace {SKILL_DIR} with the actual install dir, e.g.
# ${account_skills}/alibaba-amazon-market-intel
from conversion_performance import analyze
result = analyze(mcp_data=<mcp_response>, output_dir="/round-{N}/data")
```

---

## Execution Steps

### Step 1: Determine Keyword List

- Extract target keywords from user query
- Determine target marketplace

### Step 2: Pull SOV Data per Keyword

- 调用 `js_share_of_voice`，入参：`keyword`, `marketplace`
- Extract Top 3 ASIN conversion data per brand

### Step 3: Conversion Analysis

- List Top 3 ASINs per keyword by clicks, conversions, and conversion rate
- Identify high-converting ASINs that appear frequently across keywords

### Step 4: Deliver Results

- Output the key findings (tables, insights) directly in the conversation. Reference the CSV file for the complete dataset.

---

## Output Files

### `conversion_performance.csv` — Conversion Performance Detail

| Column | Type | Description |
|--------|------|-------------|
| `keyword` | string | Keyword |
| `brand` | string | Brand name |
| `asin` | string | ASIN |
| `click_rank` | int | Click rank (1-3) |
| `clicks` | int | Click count |
| `conversions` | int | Conversion count |
| `conversion_rate` | float | Conversion rate |
| `search_volume_30d` | int | 30-day search volume |
| `combined_sov_weighted` | float | Brand weighted combined SOV |

---

## Notes

- Top 3 ASIN data is ranked by click volume, reflecting actual user behavior
- Conversion data helps understand "who is truly winning on this keyword"
- Recommend combining with ASIN price, review count, and other information for comprehensive analysis
- Supported marketplaces: US, UK, DE, IN, CA, FR, IT, ES, MX, JP

