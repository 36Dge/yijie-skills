# Competitive Threat Monitoring

Based on the Jungle Scout Share of Voice API, tracks competitor SOV changes, detects brand advertising escalation,
identifies new entrants, and provides early warning of competitive threats.

---

## When to Use

| Intent | Example Query |
|--------|-------------|
| Competitor SOV monitoring | "Monitor competitor SOV changes on my core keywords" |
| Ad escalation detection | "Which competitor has recently increased ad spend?" |
| New entrant identification | "Are there any new brands entering my keyword space?" |
| Defensive strategy development | "Which keywords do I need to strengthen my defense on?" |

### ⛔ Not Applicable

| Intent | Alternative Module |
|--------|-------------------|
| Competitor sales tracking | `sales_estimates/competitive-sales-tracking` |
| Competitor keyword gap | `keywords_by_asin/keyword-gap-analysis` |
| Competitor product portfolio analysis | `product_database/competitive-landscape-analysis` |

---

## Usage

Reference script: `scripts/share_of_voice/competitive_threat_monitoring.py`

```python
# Step 1: Fetch data via MCP
# 调用品牌份额工具获取数据
# Step 2: Pass MCP response to analysis script
import sys
sys.path.insert(0, '{SKILL_DIR}/scripts/share_of_voice')
# Replace {SKILL_DIR} with the actual install dir, e.g.
# ${account_skills}/alibaba-amazon-market-intel
from competitive_threat_monitoring import analyze
result = analyze(mcp_data=<mcp_response>, output_dir="/round-{N}/data")
```

---

## Execution Steps

### Step 1: Determine Monitoring Keywords

- Extract core keyword list from user query
- Determine target marketplace

### Step 2: Pull SOV Data per Keyword

- 调用 `js_share_of_voice`，入参：`keyword`, `marketplace`

### Step 3: Threat Analysis

- Flag brands with abnormally high sponsored_sov (above 1.5× the mean → `high_ad_spend`)
- Identify newly appearing brands (when compared with historical data)
- Detect brands with sudden SOV surges

### Step 4: Deliver Results

- Output the key findings (tables, insights) directly in the conversation. Reference the CSV file for the complete dataset.

---

## Output Files

### `competitive_threat_monitoring.csv` — Competitive Threat Detail

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
| `threat_flag` | string | Threat flag (high_ad_spend/normal) |

---

## Notes

- Recommend pulling data regularly (weekly) to establish a baseline for detecting changes
- `high_ad_spend` flag indicates the brand's sponsored SOV is significantly above average
- New entrant detection requires comparison with historical data; the first pull only establishes a baseline
- Supported marketplaces: US, UK, DE, IN, CA, FR, IT, ES, MX, JP

