# Seasonal Demand Profiling

Based on the Jungle Scout Historical Search Volume API, retrieves weekly search volume time series for keywords,
analyzes seasonal demand curves, identifies peak/trough weeks, and provides data-driven support for inventory, advertising, and content planning.

---

## When to Use

| Intent | Example Query |
|--------|-------------|
| Analyze seasonal demand curves | "How does sunscreen search volume change throughout the year?" |
| Plan restocking timing | "When is the best time to start restocking space heater?" |
| Compare multi-keyword seasonality | "Compare the seasonal differences between sunscreen and moisturizer" |
| Identify secondary demand peaks | "Besides back-to-school season, what other demand peaks does backpack have?" |
| Validate product launch timing | "Is it still in time to launch Christmas lights now?" |

### ⛔ Not Applicable

| Intent | Alternative Module |
|--------|-------------------|
| Query current keyword search volume and competition data | 关键词搜索量工具 |
| Full keyword expansion | `keyword-expansion` skill |
| Complete product market analysis | `jungle-scout-deep-dive-analyzer` skill |

---

## Usage

```python
# Step 1: Fetch data via MCP
# 调用历史搜索趋势工具获取数据
# Step 2: Pass MCP response to analysis script
import sys
sys.path.insert(0, '{SKILL_DIR}/scripts/historical_search_volume')
# Replace {SKILL_DIR} with the actual install dir, e.g.
# ${account_skills}/alibaba-amazon-market-intel
from seasonal_demand import seasonal_demand_profile

result = seasonal_demand_profile(
    mcp_data=<mcp_response>,
    keyword="sunscreen",                                 # keyword (string)
    output_dir="/round-{N}/data",
)
# Returns dict: {"output_dir": "...", "total_rows": N, "rows_per_keyword": {...}, "columns": [...]}
```

---

## Execution Steps

### Step 1: Parse Keywords and Date Range

- Extract 1–5 keywords and date range from the user query
- If the user does not specify dates, default to the most recent 12 months
- Normalize keywords to lowercase and trim extra whitespace

### Step 2: Run Analysis

- Execute `seasonal_demand_profile()`
- Call the `historical_search_volume` API for each keyword
- 429/5xx errors trigger automatic exponential backoff retry; 422 errors are gracefully skipped

### Step 3: Deliver Results

- Output the key findings (tables, insights) directly in the conversation. Reference the CSV file for the complete dataset.

---

## Output Files

### `seasonal_demand.csv` — Weekly Search Volume Time Series

| Column | Type | Description |
|--------|------|-------------|
| `keyword` | string | Queried keyword |
| `estimate_start_date` | string | Week start date (YYYY-MM-DD) |
| `estimate_end_date` | string | Week end date (YYYY-MM-DD) |
| `estimated_exact_search_volume` | int | Exact match search volume for the week |

### `seasonal_summary.csv` — Keyword Seasonality Summary

| Column | Type | Description |
|--------|------|-------------|
| `keyword` | string | Keyword |
| `total_weeks` | int | Total weeks of data coverage |
| `mean_weekly_volume` | float | Average weekly search volume |
| `max_volume` | int | Peak weekly search volume |
| `max_volume_week` | string | Peak week start date |
| `min_volume` | int | Trough weekly search volume |
| `min_volume_week` | string | Trough week start date |
| `std_dev` | float | Search volume standard deviation |
| `cv` | float | Coefficient of variation (std/mean, higher = stronger seasonality) |
| `peak_trough_ratio` | float | Peak-to-trough ratio (max/min) |

---

## Example

**Query**: "Analyze the seasonal search volume for sunscreen over the past year"

```python
result = seasonal_demand_profile(
    mcp_data=<mcp_response>,
    keyword="sunscreen",
    output_dir="/round-1/data",
)
```

**Key findings example**:
```
Analyzed 'sunscreen' search volume trends over the past 52 weeks.
Peak occurs in Week 2 of June (weekly search volume 185K), trough in Week 4 of December (12K).
Peak-to-trough ratio 15.4x, coefficient of variation 0.72, classified as a strongly seasonal product.
Demand starts climbing in March, peaks in June–July, and drops rapidly after September.

Follow-up suggestions:
- Recommend starting restocking in early March and increasing ad spend in May
- Compare seasonal differences for sub-keywords like 'sunscreen spf 50'
- Use keyword-expansion to discover sunscreen-related long-tail keywords
```

