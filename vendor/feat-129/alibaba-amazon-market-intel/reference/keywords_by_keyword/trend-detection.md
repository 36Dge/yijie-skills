# Trend Detection & Early Signal Identification

Based on monthly_trend and quarterly_trend data from the Jungle Scout keywords_by_keyword API,
detects signals before consumer demand changes become obvious. Classifies keywords as
Emerging Opportunity, Declining Risk, Short-term Rebound, Recent Cooldown, or Stable.

---

## When to Use

| Intent | Example Query |
|--------|-------------|
| Discover emerging keywords | "Which yoga mat keywords have quarterly growth exceeding 20%?" |
| Identify declining trends | "Which yoga mat keywords have continuously declining demand?" |
| Detect short-term rebound signals | "Which yoga mat keywords have recently warmed up in the past month?" |
| Trend monitoring snapshot | "Give me a complete trend analysis of yoga mat keywords" |

### ⛔ Not Applicable

| Intent | Alternative Module |
|--------|-------------------|
| Complete historical time series (monthly) | Search Volume Benchmark (within this skill, includes YoY trends) |
| Search volume absolute value comparison | Search Volume Benchmark (within this skill) |
| Complete market analysis | `jungle-scout-deep-dive-analyzer` skill |

---

## Usage

```python
# Step 1: Fetch data via MCP
# 调用关键词搜索量工具获取数据
# Step 2: Pass MCP response to analysis script
import sys
sys.path.insert(0, '{SKILL_DIR}/scripts/keywords_by_keyword')
# Replace {SKILL_DIR} with the actual install dir, e.g.
# ${account_skills}/alibaba-amazon-market-intel
from detect_trends import detect_trends

result = detect_trends(
    mcp_data=<mcp_response>,
    output_dir="/round-{N}/data",
    seed_keyword="yoga mat",                       # seed keyword (string)
    emerging_threshold=20.0,                  # Quarterly growth threshold (default 20%)
    declining_threshold=-20.0,                # Quarterly decline threshold (default -20%)
)
# Returns dict: {"output_dir", "total_rows", "emerging_keywords",
#             "declining_keywords", "signal_counts", "trend_signals_csv"}
```

---

## Execution Steps

### Step 1: Parse Seed Keywords

- Extract 1–10 seed keywords

### Step 2: API Data Collection

- Call `keywords_by_keyword` for each seed to collect keywords + trend data

### Step 3: Trend Signal Classification

- Emerging Opportunity: quarterly_trend > +20%
- Declining Risk: quarterly_trend < -20%
- Short-term Rebound: monthly_trend > +10% and quarterly_trend < 0
- Recent Cooldown: monthly_trend < -10% and quarterly_trend > 0
- Stable: all others

### Step 4: Deliver Results

- Output the key findings (tables, insights) directly in the conversation. Reference the CSV file for the complete dataset.

---

## Output Files

### `trend_signals.csv` — Trend Signal Detail Table

| Column | Type | Description |
|--------|------|-------------|
| `seed_keyword` | string | Source seed keyword |
| `name` | string | Keyword |
| `monthly_search_volume_exact` | int | Monthly exact search volume |
| `monthly_trend` | float | Monthly trend (%) |
| `quarterly_trend` | float | Quarterly trend (%) |
| `trend_signal` | string | Emerging Opportunity / Stable / Declining Risk / Short-term Rebound / Recent Cooldown |
| `trend_strength` | string | STRONG / MODERATE / WEAK |
| `action_suggestion` | string | Specific action recommendation |

---

## Notes

- monthly_trend and quarterly_trend are percentage fields provided directly by Jungle Scout, reflecting period-over-period changes
- Short-term rebound keywords require caution: may be seasonal fluctuations; combine with Search Volume Benchmark YoY data for validation
- Recommend re-running this module periodically (monthly/quarterly) to compare trend signal changes
- Threshold parameters can be adjusted based on category characteristics

