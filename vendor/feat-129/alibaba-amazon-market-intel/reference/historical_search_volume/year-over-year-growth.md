# Year-over-Year Growth Analysis

Based on the Jungle Scout Historical Search Volume API, pulls weekly search volume for the same time periods across consecutive years,
aligns by week index to calculate year-over-year growth rate, growth acceleration, and compound annual growth rate (CAGR),
determines category expansion/contraction trends, and detects structural changes in consumer behavior.

---

## When to Use

| Intent | Example Query |
|--------|-------------|
| Category YoY growth | "Compare yoga mat search volume this year vs last year" |
| Growth acceleration/deceleration | "Is the portable blender category growth slowing down?" |
| Multi-year trend tracking | "What's the search volume trend for air purifier over the past 3 years?" |
| Long-term investment decisions | "Is the electric scooter category worth long-term investment?" |
| Structural change detection | "Has home office furniture search volume returned to pre-pandemic levels?" |

### ⛔ Not Applicable

| Intent | Alternative Module |
|--------|-------------------|
| Single-year seasonal analysis | `seasonal-demand-profiling` reference |
| Multi-keyword competitive benchmarking | `competitive-benchmarking` reference |
| Ad budget planning | `ad-campaign-timing` reference |

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
from yoy_growth import analyze_yoy_growth

result = analyze_yoy_growth(
    mcp_data=<mcp_response>,
    keyword="yoga mat",                                 # keyword (string)
    output_dir="/round-{N}/data",
)
# Returns dict: {"output_dir": "...", "total_rows": N, "rows_per_keyword_year": {...}, ...}
```

---

## Execution Steps

### Step 1: Parse Keywords and Years

- Extract 1–5 keywords and the list of years to compare from the query
- If the user does not specify years, default to comparing the most recent two years
- If the user does not specify a month range, default to the full year (1–12)

### Step 2: Run Analysis

- Execute `analyze_yoy_growth()`
- Call the `historical_search_volume` API for each keyword × year combination
- 429/5xx errors trigger automatic exponential backoff retry; 422 errors are gracefully skipped

### Step 3: Deliver Results

- Output the key findings (tables, insights) directly in the conversation. Reference the CSV file for the complete dataset.

---

## Output Files

### `yoy_growth.csv` — Weekly Time Series with Year Labels

| Column | Type | Description |
|--------|------|-------------|
| `keyword` | string | Queried keyword |
| `year` | int | Year the data belongs to |
| `week_index` | int | Week index (starting from 1, used for cross-year alignment) |
| `estimate_start_date` | string | Week start date (YYYY-MM-DD) |
| `estimate_end_date` | string | Week end date (YYYY-MM-DD) |
| `estimated_exact_search_volume` | int | Exact match search volume for the week |


### `yoy_summary.csv` — Year-over-Year Growth Summary

| Column | Type | Description |
|--------|------|-------------|
| `keyword` | string | Keyword |
| `year` | int | Year |
| `total_volume` | int | Total search volume within the year's window |
| `mean_weekly_volume` | float | Average weekly search volume |
| `peak_volume` | int | Peak weekly search volume |
| `peak_week_date` | string | Peak week start date |
| `yoy_growth_pct` | float | Year-over-year growth rate vs previous year (%, null for first year) |
| `cagr_pct` | float | Compound annual growth rate (%, null for first year) |
| `growth_trend` | string | Growth trend (accelerating / decelerating / stable / insufficient_data) |

---

## Example

**Query**: "Compare yoga mat search volume this year vs last year"

```python
result = analyze_yoy_growth(
    mcp_data=<mcp_response>,
    keyword="yoga mat",
    output_dir="/round-1/data",
)
```

**Key findings example**:
```
Compared 'yoga mat' search volume for Q1 2025 vs Q1 2026.
2025 Q1 total search volume 245,000, 2026 Q1 total search volume 268,000, YoY growth 9.4%.
The category is in a stable growth phase, suitable for continued investment.

Follow-up suggestions:
- Pull 3 years of data to calculate CAGR and verify whether growth is sustainable
- Use seasonal-demand-profiling to analyze the full seasonal curve
- Use product-launch-timing to determine the optimal launch window
```

---

## Notes

- **Year range 2–4 years**: Fewer than 2 years cannot calculate YoY; more than 4 years are automatically truncated
- **Each year calls the API independently**: The API supports a maximum of 366 days per call, so cross-year requests require separate calls
- **Week index alignment**: Weeks across different years are aligned by index, not by calendar date
- **CAGR calculation**: Requires at least 2 years of data; 3+ years are needed to determine growth acceleration/deceleration trends

