# ASIN Keyword Trend & Seasonality Detection

Based on the Jungle Scout keywords_by_asin API, extracts monthly and quarterly trend data for keywords driving traffic to the target ASIN,
identifies rising, falling, and seasonal peak keywords, supporting forward-looking inventory and ad budget decisions.

---

## When to Use

| Intent | Example Query |
|--------|-------------|
| Identify growing keywords | "Which keywords for ASIN B001XX have an upward trend?" |
| Detect seasonal keywords early | "Does B001XX have any search terms approaching a seasonal peak?" |
| Avoid wasting ad spend on declining keywords | "Which keywords for B001XX have continuously declining search volume?" |
| Multi-ASIN trend comparison | "Compare the trending keywords across these three ASINs" |

### ⛔ Not Applicable

| Intent | Alternative Module |
|--------|-------------------|
| Keyword historical search volume time series | Seasonal Demand Profiling (within this skill) |
| Complete keyword profile analysis | Reverse ASIN Research (within this skill) |

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
from trend_seasonality_asin import trend_seasonality_asin

result = trend_seasonality_asin(
    mcp_data=<mcp_response>,
    output_dir="/round-{N}/data",
    asin="B001MYASIN",                      # ASIN 标签（用于 CSV 标识）
    rising_threshold=0.1,       # Rising trend threshold (default 0.1 = +10% MoM)
    falling_threshold=-0.1,     # Falling trend threshold (default -0.1 = -10% MoM)
    min_search_volume=200,      # Minimum search volume filter (default 200)
)
# Returns dict: {"rising_count", "falling_count", "seasonal_count", ...}
```

---

## Execution Steps

### Step 1: Parse Input

- Extract target ASINs (1–5) from user query

### Step 2: API Collection and Trend Classification

- 调用 `js_keywords_by_asin`，入参：`asin`, `page_size`（每个 ASIN 分别调用）
- Classify keywords as rising, falling, or seasonal peak based on monthly/quarterly trends

### Step 3: Deliver Results

- Output the key findings (tables, insights) directly in the conversation. Reference the CSV file for the complete dataset.

---

## Output Files

### `trend_raw.csv` — All Keyword Raw Data (with trend fields)

### `rising_keywords.csv` — Rising Trend Keywords

| Column | Description |
|--------|-------------|
| `asin` | Source ASIN |
| `name` | Keyword |
| `monthly_search_volume_exact` | Exact monthly search volume |
| `monthly_trend` | Monthly MoM trend (decimal, 0.1 = +10%) |
| `quarterly_trend` | Quarterly QoQ trend (decimal) |
| `ease_of_ranking_score` | Ease of ranking score |

Criteria: `monthly_trend > +10%` or `quarterly_trend > +10%`

### `falling_keywords.csv` — Falling Trend Keywords

Criteria: `monthly_trend < -10%` or `quarterly_trend < -10%`

### `seasonal_keywords.csv` — Seasonal Peak Keywords

Criteria: `quarterly_trend - monthly_trend > +15%`

---

## Notes

- Trend fields (`monthly_trend`, `quarterly_trend`) may be null for some ASINs/keywords; null is treated as no trend
- `min_search_volume` recommend setting to 200+ to filter out low search volume keywords
- Seasonal keyword detection is based on the difference between quarterly and monthly trends, not absolute values

