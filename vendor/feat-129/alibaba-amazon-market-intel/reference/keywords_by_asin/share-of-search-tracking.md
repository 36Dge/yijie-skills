# Share of Search & Organic Visibility Tracking

Based on the Jungle Scout keywords_by_asin API, collects organic rank and sponsored rank snapshots for target ASIN keywords,
calculates rank distribution and weighted search share, and supports historical comparison through periodic pulls.

---

## When to Use

| Intent | Example Query |
|--------|-------------|
| Establish initial rank baseline | "Help me record the current keyword rank snapshot for ASIN B001XX" |
| Monitor rank changes | "Has B001XX's ranking changed this month compared to last month?" |
| Quantify organic search health | "What is B001XX's weighted search share?" |
| Multi-ASIN search share comparison | "Compare the organic search share of B001XX and B002YY" |

### ⛔ Not Applicable

| Intent | Alternative Module |
|--------|-------------------|
| First-time comprehensive keyword analysis | Reverse ASIN Research (within this skill) |
| Keyword trend analysis | ASIN Trend & Seasonality Detection (within this skill) |

---

## Usage

```python
# Step 1: Fetch data via MCP
# 调用ASIN关键词工具获取数据
# Step 2: Pass MCP response to analysis script
import sys
sys.path.insert(0, '{SKILL_DIR}/scripts/keywords_by_asin')
# Replace {SKILL_DIR} with the actual install dir, e.g.
# ${account_skills}/alibaba-amazon-market-intel
from share_of_search_tracking import share_of_search_tracking

result = share_of_search_tracking(
    mcp_data=<mcp_response>,
    output_dir="/round-{N}/data",
    asin="B001MYASIN",                      # ASIN 标签（用于 CSV 标识）
    snapshot_label="2026-03",               # Snapshot label, recommend using year-month
    min_search_volume=100,                  # Minimum search volume filter (default 100)
)
# Returns dict: {"snapshot_label", "weighted_sos_per_asin", "raw_csv", ...}
```

---

## Execution Steps

### Step 1: Parse Input

- Extract target ASINs (1–5) and snapshot label (recommend year-month format) from user query

### Step 2: API Collection and Metric Calculation

- 调用 `js_keywords_by_asin`，入参：`asin`, `page_size`
- Calculate rank distribution (Top3/Top10/Top20/Top50) and weighted search share

### Step 3: Deliver Results

- Output the key findings (tables, insights) directly in the conversation. Reference the CSV file for the complete dataset.

---

## Output Files

### `rank_snapshot_{label}.csv` — Complete Keyword Rank Raw Snapshot

### `rank_distribution_{label}.csv` — Rank Distribution Summary

| Column | Description |
|--------|-------------|
| `asin` | Target ASIN |
| `snapshot` | Snapshot label |
| `total_keywords` | Total keywords collected |
| `rank_Top3` | Keywords with organic rank 1–3 |
| `rank_Top10` | Keywords with organic rank 4–10 |
| `rank_Top20` | Keywords with organic rank 11–20 |
| `rank_Top50` | Keywords with organic rank 21–50 |
| `rank_Beyond50` | Keywords with organic rank > 50 |
| `sponsored_coverage` | Keywords with sponsored rank |

### `weighted_sos_{label}.csv` — Weighted Search Share

| Column | Description |
|--------|-------------|
| `asin` | Target ASIN |
| `total_search_volume` | Total search volume across all keywords |
| `top20_organic_search_volume` | Total search volume for Top 20 ranked keywords |
| `weighted_organic_sos` | Weighted organic search share (0–1) |

---

## Notes

- Recommend running periodically (weekly or monthly) after the initial run, using `snapshot_label` to distinguish snapshot periods
- `organic_rank` and `sponsored_rank` may be null for some keywords; null values are excluded from distribution statistics
- Weighted search share only reflects Top 20 organic rank coverage, not overall market search share

