# Search Volume Benchmark & Demand Validation

Based on the Jungle Scout keywords_by_keyword + historical_search_volume APIs,
compares search demand across multiple product concepts, calculates demand specificity ratio,
and derives year-over-year trend signals (GROWING / STABLE / DECLINING).

---

## When to Use

| Intent | Example Query |
|--------|-------------|
| Compare product concepts | "Compare search demand: yoga mat vs resistance band vs foam roller" |
| Validate a single idea | "Does bamboo toothbrush have real demand on Amazon?" |
| Understand demand specificity | "Is 'wireless earbuds' demand focused or diffuse?" |
| Determine growth or decline | "Is air fryer demand growing or declining?" |
| Pre-launch priority ranking | "Which of these 5 products has the highest and most stable demand?" |

### ⛔ Not Applicable

| Intent | Alternative Module |
|--------|-------------------|
| Quick single keyword search volume query | 关键词搜索量工具 |
| Complete market analysis pipeline | `jungle-scout-deep-dive-analyzer` skill |
| Historical trend chart only | 历史搜索趋势工具 |

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
from benchmark_demand import benchmark_demand

result = benchmark_demand(
    mcp_kw_data=<mcp_response>,
    product_concept="yoga mat",                    # product concept (string)
    output_dir="/round-{N}/data",
)
# Returns dict: {"output_dir", "concepts", "ranked_concepts", "demand_benchmark_csv", "volume_trend_csv"}
```

---

## Execution Steps

### Step 1: Parse Product Concepts

- Extract 1–10 product concept keywords, normalize to lowercase

### Step 2: Collect Search Volume

- Call `keywords_by_keyword` for each concept to get primary keyword and metrics
- Calculate: exact_volume, broad_volume, specificity_ratio, market_size_signal

### Step 3: Derive Trend Signals

- Call `historical_search_volume` for each concept's top keyword (12-month window)
- Calculate YoY change: GROWING (>+10%) / STABLE (±10%) / DECLINING (<-10%)

### Step 4: Rank and Deliver

- demand_score = exact_volume × (1 + yoy_change_pct/100), sorted descending
- Output the key findings (tables, insights) directly in the conversation. Reference the CSV file for the complete dataset.

---

## Output Files

### `demand_benchmark.csv` — Concept Comparison Table

| Column | Type | Description |
|--------|------|-------------|
| `rank` | int | Overall demand rank (1 = best) |
| `product_concept` | string | Product concept keyword |
| `primary_keyword` | string | Keyword with highest search volume |
| `exact_volume` | int | Monthly exact match search volume |
| `broad_volume` | int | Monthly broad match search volume |
| `specificity_ratio` | float | exact/broad (higher = more focused demand) |
| `keyword_count` | int | Number of related keywords discovered |
| `market_size_signal` | string | LARGE / MEDIUM / SMALL / NICHE |
| `trend_signal` | string | GROWING / STABLE / DECLINING / INSUFFICIENT_DATA |
| `yoy_change_pct` | float | Year-over-year search volume change (%) |
| `demand_score` | float | Overall ranking score |

### `volume_trend.csv` — Monthly Historical Series

| Column | Type | Description |
|--------|------|-------------|
| `product_concept` | string | Product concept |
| `keyword` | string | Keyword used for trend data collection |
| `date` | string | YYYY-MM-DD |
| `estimated_exact_search_volume` | int | Monthly exact match search volume |

---

## Notes

- Specificity ratio close to 1.0 indicates clear, focused demand; < 0.4 indicates diffuse demand
- YoY trend uses a 12-month window; fewer than 6 data points are labeled INSUFFICIENT_DATA
- demand_score naturally down-weights declining products and boosts growing product rankings
- Single concept API errors do not affect overall execution

