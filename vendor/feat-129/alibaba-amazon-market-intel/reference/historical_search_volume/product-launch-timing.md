# Product Launch Timing Optimization

Based on the Jungle Scout Historical Search Volume API, analyzes weekly search volume trends for keywords,
identifies demand ramp-up starting points and peak timing, calculates the optimal launch window (4–6 weeks before peak),
evaluates year-round demand stability for the category, and provides data-driven support for new product launch decisions.

---

## When to Use

| Intent | Example Query |
|--------|-------------|
| Determine optimal launch timing | "When is the best time to launch sunscreen?" |
| Validate category demand stability | "Is yoga mat an evergreen or seasonal product?" |
| Compare launch windows across categories | "Compare the best launch timing for sunscreen, rain jacket, and snow boots" |
| Evaluate current launch timing | "Is it too late to launch Christmas lights now?" |
| Find low-competition launch windows | "Which category has the least competition for a Q2 launch?" |

### ⛔ Not Applicable

| Intent | Alternative Module |
|--------|-------------------|
| View seasonal demand curves | `seasonal-demand-profiling` reference |
| Inventory planning and demand forecasting | `inventory-demand-forecasting` reference |
| Query current keyword search volume | 关键词搜索量工具 |

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
from launch_timing import analyze_launch_timing

result = analyze_launch_timing(
    mcp_data=<mcp_response>,
    keyword="sunscreen",                                 # keyword (string)
    output_dir="/round-{N}/data",
    pre_peak_weeks=6,                                # Weeks before peak for ideal launch window (default 6)
)
# Returns dict: {"output_dir": "...", "total_rows": N, "rows_per_keyword": {...}, ...}
```

---

## Execution Steps

### Step 1: Parse Keywords and Date Range

- Extract 1–5 keywords and date range from the query
- If the user does not specify dates, default to the most recent 12 months

### Step 2: Run Analysis

- Execute `analyze_launch_timing()`
- The script automatically calculates: demand ramp-up starting point (3 consecutive weeks of positive growth), peak week,
  optimal launch window (N weeks before peak), demand stability score (inverse of CV),
  demand classification (evergreen / seasonal / highly_seasonal)

### Step 3: Deliver Results

- Output the key findings (tables, insights) directly in the conversation. Reference the CSV file for the complete dataset.

---

## Output Files

### `launch_timing.csv` — Weekly Time Series with Trend Metrics

| Column | Type | Description |
|--------|------|-------------|
| `keyword` | string | Queried keyword |
| `estimate_start_date` | string | Week start date (YYYY-MM-DD) |
| `estimate_end_date` | string | Week end date (YYYY-MM-DD) |
| `estimated_exact_search_volume` | int | Exact match search volume for the week |
| `pct_of_peak` | float | Percentage of peak search volume (%) |
| `wow_change_pct` | float | Week-over-week change rate (%) |
| `phase` | string | Demand phase (ramp_up / peak / decline / trough) |


### `launch_summary.csv` — Keyword-Level Launch Decision Summary

| Column | Type | Description |
|--------|------|-------------|
| `keyword` | string | Keyword |
| `total_weeks` | int | Total weeks of data coverage |
| `demand_type` | string | Demand type (evergreen / seasonal / highly_seasonal) |
| `stability_score` | float | Demand stability score (0–1, higher is more stable) |
| `peak_volume` | int | Peak weekly search volume |
| `peak_week` | string | Peak week start date |
| `ramp_up_start` | string | Demand ramp-up starting point |
| `ideal_launch_window_start` | string | Optimal launch window start week |
| `ideal_launch_window_end` | string | Optimal launch window end week |
| `weeks_until_peak` | int | Weeks from launch window start to peak |
| `trough_volume` | int | Trough weekly search volume |
| `peak_trough_ratio` | float | Peak-to-trough ratio |

---

## Example

**Query**: "When is the best time to launch sunscreen?"

```python
result = analyze_launch_timing(
    mcp_data=<mcp_response>,
    keyword="sunscreen",
    output_dir="/round-1/data",
)
```

**Key findings example**:
```
Analyzed 'sunscreen' search volume trends over the past 52 weeks.
Demand type: highly seasonal (highly_seasonal), stability score 0.28.
Peak occurs in Week 2 of June (185K), demand starts ramping up from Week 3 of March.
Optimal launch window: Week 4 of April ~ Week 2 of May (4–6 weeks before peak).

Follow-up suggestions:
- Use keyword-expansion to discover sunscreen-related long-tail keywords
- Use inventory-demand-forecasting to plan restocking volume and timing
- Compare launch window differences for sub-keywords like 'sunscreen spf 50'
```

---

## Notes

- **pre_peak_weeks**: Ideal launch window is N weeks before peak, default 6 weeks
- **Demand classification thresholds**: CV < 0.3 is evergreen, 0.3–0.6 is seasonal, > 0.6 is highly_seasonal
- **Inflection point detection**: Requires 3 consecutive weeks of same-direction change to identify a ramp-up starting point

