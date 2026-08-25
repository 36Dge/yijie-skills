# Multi-ASIN Keyword Portfolio

Based on the Jungle Scout keywords_by_asin API, batch-collects keywords for up to 10 ASINs in a brand catalog,
builds a keyword × ASIN matrix, and identifies keyword cannibalization and coverage gaps.

---

## When to Use

| Intent | Example Query |
|--------|-------------|
| Audit brand catalog keyword coverage | "Help me analyze keyword coverage for these 8 brand ASINs" |
| Identify keyword cannibalization | "Which of my products are competing for the same keywords?" |
| Ensure high-value keywords have product coverage | "Are there any high search volume keywords with no product ranking?" |

### ⛔ Not Applicable

| Intent | Alternative Module |
|--------|-------------------|
| Single ASIN deep keyword analysis | Reverse ASIN Research (within this skill) |
| Competitor vs own gap analysis | Keyword Gap Analysis (within this skill) |

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
from multi_asin_portfolio import multi_asin_portfolio

result = multi_asin_portfolio(
    mcp_data=<mcp_response>,
    output_dir="/round-{N}/data",
    asin="B001AA",                           # ASIN 标签（用于 CSV 标识）
    cannibalization_threshold=2,             # Cannibalization detection threshold (default 2)
)
# Returns dict: {"total_unique_keywords", "cannibalization_count", "rows_per_asin", ...}
```

---

## Execution Steps

### Step 1: Parse Input

- Extract brand catalog ASINs (1–10) from user query

### Step 2: API Collection and Matrix Construction

- 调用 `js_keywords_by_asin`，入参：`asin`, `page_size`（每个 ASIN 分别调用）
- Build keyword × ASIN matrix, identify cannibalization keywords

### Step 3: Deliver Results

- Output the key findings (tables, insights) directly in the conversation. Reference the CSV file for the complete dataset.

---

## Output Files

### `portfolio_raw.csv` — All ASIN × Keyword Raw Data

### `keyword_asin_matrix.csv` — Keyword × ASIN Matrix

| Column | Description |
|--------|-------------|
| `name` | Keyword |
| `monthly_search_volume_exact` | Exact monthly search volume |
| `B001AA` | Whether this ASIN covers this keyword (1=yes, 0=no) |
| `B002BB` | Same as above, one column per ASIN |
| `asin_coverage_count` | Total number of ASINs covering this keyword |

### `cannibalization.csv` — Cannibalization Keywords

Same format as matrix, only retaining keywords with `asin_coverage_count ≥ cannibalization_threshold`.

---

## Notes

- Pass 1–10 catalog ASINs (excess is automatically truncated)
- Cannibalization detection threshold `cannibalization_threshold` defaults to 2
- Matrix column count equals the number of ASINs; with many ASINs the CSV can be wide, recommend opening with Excel

