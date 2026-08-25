---
name: jungle-scout-deep-dive-analyzer
description: >-
  Jungle Scout API-powered deep market analysis for Amazon product selection. Uses real
  keyword, competitor, trend and brand-share data to compute an Indicator Data Framework,
  produce an 8-dimension deep-dive, 3-tier product recommendations (~50 products CSV) and
  B2B supply sourcing. Bilingual (zh/en). Mandatory deliverable: `final_report.md`.
  Use when the user wants a data-driven Amazon market analysis backed by Jungle Scout —
  category opportunity evaluation, competitive deep-dive, or end-to-end product selection.
  Do NOT use for cross-platform trending/hotselling products or general market trends
  (use `market-insight-product-selection`); do NOT use for a single Jungle Scout data
  point (use `jungle_scout_search` in `info_search`).
workflow: |
  Deep-dive analysis pipeline:
    Step 1: Detect query language (zh/en)
    Step 2: Collect Jungle Scout data via ONE jungle_scout_collect call → CSVs
    Step 3: Compute Indicator Data Framework → JSON
    Step 4: Detect anomalies → generate 8 decision-oriented sub-questions
    Step 5: Read CSVs + indicators → write 8 SubQuestionAnswer objects with calculations
    Step 6: 3-tier product recommendations → ~50 products CSV + charts
    Step 7: B2B supplier search → Phase A read inputs → Phase B assemble report → Phase C verify → write final_report.md + alibaba_supply.csv
enabled: true
---

# Product Selection Deep Research — Real Data Intelligence Pipeline

> **Path convention**: skill-internal paths are relative to the installation directory in `<skills_library>`; output paths are relative to the workspace root in `<workspace_directory>`.

> **Core rule — `final_report.md` is the deliverable.**
> 1. `final_report.md` MUST be written by the agent via `write_file`.
> 2. If any step fails, still write `final_report.md` with whatever data is available — partial report > no report.

### Bilingual Support

CJK characters (U+4E00–U+9FFF) → `zh`, otherwise → `en`. All outputs follow detected language.

### Data Source Badges

See `references/data_source_badges.md` for badge definitions and usage.

---

## When to Use

| Question Type | Example (EN) | Example (ZH) |
|--------------|-------------|-------------|
| Market Opportunity | "Find blue ocean opportunities in Home & Kitchen" | "寻找家居厨房品类的蓝海机会" |
| Competitive Analysis | "Analyze competitor ASIN B0XXXXXX traffic keywords" | "分析竞品 ASIN B0XXXXXX 的流量关键词" |
| Product Validation | "Is the $25-$35 yoga mat market worth entering?" | "瑜伽垫 $25-$35 价位值得进入吗？" |
| Ad & Traffic | "What's the PPC bid for 'portable blender'?" | "便携式搅拌机的 PPC 竞价是什么？" |
| Trend & Seasonality | "Is 'christmas lights' a seasonal product?" | "圣诞灯饰是季节性产品吗？" |

### When NOT to Use

If the question can be answered by a single API call, do NOT activate this skill.

| User Intent | Correct Tool |
|-------------|-------------|
| Keyword search volume | `jungle_scout_search(api_type="keywords_by_keyword_query")` |
| ASIN sales estimates | `jungle_scout_search(api_type="sales_estimates_query")` |
| Keyword ranking for ASIN | `jungle_scout_search(api_type="keywords_by_asin_query")` |
| Brand share of voice | `jungle_scout_search(api_type="share_of_voice")` |
| Product database browse | `jungle_scout_search(api_type="product_database_query")` |
| Search volume trend | `jungle_scout_search(api_type="historical_search_volume")` |
| Quick product search | `info_search(mode="shopping")` |
| General web/trend lookup | `info_search(mode="web/trend")` |

---

## How to Use

> ⚠️ **Round Directory**: All paths use `round-{N}`. Do NOT hardcode `round-1`.

### Overview

1. **Step 1** — Detect language → `zh` or `en`
2. **Step 2** — Collect Jungle Scout API data (ONE batch call) → CSVs
3. **Step 3** — Compute Indicator Data Framework → JSON
4. **Step 4** — Detect anomalies → generate 8 decision-oriented sub-questions
5. **Step 5** — Extract CSV data → analyze each dimension with cross-referencing → structured answers + analysis-driven product recommendations
6. **Step 6** — 3-tier product recommendations (analysis-driven → data-filtered → search supplement) → `final_recommendations.csv` + charts. Section 4 of the report depends on this step.
7. **Step 7** — B2B supplier search → Phase A: 4× `read_file` → Phase B: assemble report → Phase C: verify → ONE `write_file` for `final_report.md` + `alibaba_supply.csv`

> **Failure recovery**: if any step (2–6) errors, continue and still write `final_report.md` in Step 7.
> **Turn budget**: the pipeline needs ~20 turns. If you are past turn 25 and have not started Step 7, skip remaining steps and proceed directly to Step 7. The report is always the final action.


---

## Step 1: Detect Language

`detect_language()` in `scripts/models.py` — CJK → `zh`, else → `en`. Pass to all subsequent steps.

---

## Step 2: Collect Jungle Scout API Data <cite>[Jungle Scout](https://www.junglescout.com)</cite>

Use the `jungle_scout_collect` tool to fetch ALL Jungle Scout data in a single call.
The tool automatically calls 4 mandatory APIs (keywords_by_keyword, historical_search_volume,
product_database, share_of_voice) concurrently, saves raw JSON files to `output_dir`,
and returns a summary. If `asin` is provided, it also calls keywords_by_asin and sales_estimates.

### 2a. Call APIs (ONE tool call)

```
jungle_scout_collect(keyword="<user_keyword>", output_dir="/round-{N}/data")
```

**With optional ASIN** (adds 2 extra API calls automatically):
```
jungle_scout_collect(keyword="<user_keyword>", output_dir="/round-{N}/data", asin="<ASIN>")
```

The tool returns a summary like:
```
jungle_scout_collect: 4/4 APIs succeeded for keyword='portable blender'.
  ✅ keywords_by_keyword: 50 records → `/round-{N}/data/raw_keywords.json`
  ✅ historical_search_volume: 51 records → `/round-{N}/data/raw_historical.json`
  ✅ product_database: 50 records → `/round-{N}/data/raw_products.json`
  ✅ share_of_voice: 1 records → `/round-{N}/data/raw_sov.json`
```

### 2b. Convert JSON → CSV

`bash_command`:
```bash
python -c "import sys; sys.path.insert(0,'/jungle-scout-deep-dive-analyzer/scripts'); from collect_js_data import convert_all; convert_all('/round-{N}/data','<user_keyword>')"
```

**APIs** → CSV outputs:

| API | Output CSV |
|-----|-----------|
| `keywords_by_keyword` | `keywords_market.csv` |
| `historical_search_volume` | `keyword_trends.csv` |
| `product_database` | `competitors.csv` |
| `share_of_voice` | `market_concentration.csv` |
| `keywords_by_asin` (optional) | `asin_keywords.csv` |
| `sales_estimates` (optional) | `asin_sales.csv` |

---

## Step 3: Compute Indicator Data Framework <cite>[Jungle Scout](https://www.junglescout.com)</cite>

**Script**: `scripts/analyze_indicators.py`

```bash
python scripts/analyze_indicators.py --keyword "<keyword>" --input_dir /round-{N}/data --output_file /round-{N}/data/indicator_framework.json
```

Computes 11 indicators: Main Keyword, Category, Search Volume, Top 1 Revenue, $5K+ Listings, Avg Price/Weight/FBA, Avg Reviews/Rating, Monopoly, Seasonality, Traffic Ratio, PPC Bid/Conversion.

> See `references/indicator_definitions.md` for detailed formulas, thresholds, and edge case handling.
> See `references/analysis_criteria.md` for qualitative threshold standards used in narrative analysis.

**Output**: `round-{N}/data/indicator_framework.json`

---

## Step 4: Sub-Question Generation (8 Dimensions) <cite>[Jungle Scout](https://www.junglescout.com)</cite>

**No script** — agent generates directly. Models in `scripts/models.py`.

Generate exactly **8 sub-questions**, one per dimension:

| # | Dimension (EN) | Dimension (ZH) | target_dimension key |
|---|----------------|----------------|---------------------|
| 1 | Market Size & Demand | 需求规模分析 | `market_size_demand` |
| 2 | Competitive Landscape | 竞争格局分析 | `competitive_landscape` |
| 3 | Demand Seasonality & Stability | 稳定性分析 | `demand_seasonality` |
| 4 | Margin Analysis & Price Positioning | 利润空间 | `margin_analysis` |
| 5 | Barrier to Entry | 进入壁垒分析 | `entry_barrier` |
| 6 | Marketing & Traffic | 营销难度分析 | `marketing_traffic` |
| 7 | Niche Opportunities | 细分机会挖掘 | `niche_opportunities` |
| 8 | User Pain-Points | 痛点挖掘分析 | `pain_points` |

### Sub-Question Quality Requirements

> See `references/subquestion_templates.md` for full template library, anomaly detection rules, per-type examples, and detailed good/bad examples.

**Every sub-question MUST satisfy ALL 5 criteria**: Data-Premised (start with a specific number from indicators), Cross-Referential (reference ≥2 CSV sources), Decision-Oriented (end with decision implication), Calculable (require computation, not restating), Non-Obvious (not answerable by reading one value).

### Anomaly-Driven Generation Process

**Step 4a**: Read `indicator_framework.json` and detect anomalies (see `references/subquestion_templates.md` for full anomaly→question mapping rules).

**Step 4b**: Detect question type from user query keywords (see `references/subquestion_templates.md`).

**Step 4c**: Generate 8 questions using the type-specific templates, injecting detected anomaly values as premises. **At least 3 of the 8 questions MUST be directly triggered by detected anomalies.**

**Action**: Read indicators → detect anomalies → detect language → detect question type → generate 8 questions → save:

```python
import sys
sys.path.insert(0, '/jungle-scout-deep-dive-analyzer/scripts')
from models import SubQuestion, SubQuestionList, detect_language
from pipeline import save_subquestions

subquestions = SubQuestionList(
    question_type="Market Opportunity",
    user_query=user_query,
    language=detect_language(user_query),
    questions=[
        SubQuestion(
            question_id="1",
            question_text="Main keyword volume is only 442, but 50 related keywords exist. Calculate the aggregate search volume of the top 20 related keywords from keywords_market.csv. If the aggregate exceeds 5,000, the market has sufficient long-tail demand despite the low main keyword. Also identify the top 3 keywords by volume-to-competition ratio.",
            target_dimension="market_size_demand",
            expected_answer_format="table + aggregate_calculation",
            source_indicators=["search_volume", "related_keyword_count"],
        ),
        # ... 7 more questions, each with specific data premises and cross-references
    ],
)
save_subquestions(subquestions, base_dir="/round-{N}")
```

**Output**: `round-{N}/reports/subquestions.json`

> ⚠️ **VERIFICATION**: After saving, `read_file` the JSON and confirm all 8 questions contain specific numbers from indicators. If any question is just a dimension name rephrased (e.g., "Analyze the competitive landscape"), regenerate it.


---

## Step 5: Real Data Answers <cite>[Jungle Scout](https://www.junglescout.com)</cite>

> **The agent itself is the analyst.** Do NOT call an external LLM inside `bash_command` — read the data, reason over it, and write structured answers directly.
>
> This step produces `subquestion_answers.json`, the analytical backbone of Section 3. Shallow answers here = shallow report.

### 5a. Extract data for all 8 dimensions

Write and run a single script to load subquestions + CSV data and print the extracted context:

```python
import sys, os, json
sys.path.insert(0, '/jungle-scout-deep-dive-analyzer/scripts')
from answer_with_js_data import set_data_dir, extract_relevant_data
from pipeline import load_subquestions

base_dir = '/round-{N}'
set_data_dir(os.path.join(base_dir, 'data'))

with open(os.path.join(base_dir, 'data/indicator_framework.json')) as f:
    indicators = json.load(f)

subquestions = load_subquestions(base_dir)

print("=== INDICATOR FRAMEWORK ===")
print(json.dumps(indicators, indent=2, default=str))

for q in subquestions.questions:
    data = extract_relevant_data(q)
    print(f"\n=== Q{q.question_id}: {q.target_dimension} ===")
    print(f"Question: {q.question_text}")
    # ⚠️ Use q.question_id (NOT q.id) — SubQuestion model field is "question_id"
    print(f"Data keys: {list(data.keys())}")
    # Print summary stats, not full CSV rows
    for csv_name, csv_data in data.items():
        if isinstance(csv_data, dict):
            for k, v in csv_data.items():
                if k.startswith('top_') or k == 'all_brands' or k == 'trend_data':
                    print(f"  {csv_name}.{k}: [{len(v)} rows]")
                else:
                    print(f"  {csv_name}.{k}: {v}")
```

### 5b. Agent analyzes each dimension and writes answers

After reading the data output from 5a, the Agent constructs **all 8** `SubQuestionAnswer` objects.

> See `references/js_data_answer_prompt.md` for the complete output JSON schema, quality rules, depth requirements, and anti-patterns.

**Key rules**: You ARE the analyst (no external LLM calls). Every `answer_text` ≥150 words with ≥3 specific numbers. Every `analysis_reasoning` ≥100 words with calculations. Include `recommended_asins` when analysis naturally identifies specific products. Filter out accessories.

**Save all 8 answers** (use `write_file` + `bash_command` pattern):

```python
import sys, os, json
sys.path.insert(0, '/jungle-scout-deep-dive-analyzer/scripts')
from models import SubQuestionAnswer, SubQuestionAnswerList
from pipeline import save_subquestion_answers

answers = SubQuestionAnswerList(answers=[
    SubQuestionAnswer(
        question_id="1",
        answer_text="...",  # ≥150 words with ≥3 specific numbers from CSV data
        data_points=[...],  # ≥3 entries for table/mixed format
        confidence_level="high",
        analysis_reasoning="...",  # ≥100 words with step-by-step calculations
        conclusion="...",  # One sentence with THE key number
        citations=["keywords_market.csv", "indicator_framework"],
        presentation_format="mixed",
        chart_suggestion="",
        recommended_asins=[],  # Include when analysis identifies specific products
    ),
    # ... repeat for all 8 questions with EQUAL depth
])
save_subquestion_answers(answers, base_dir="/round-{N}")
```

**Output**: `round-{N}/reports/subquestion_answers.json`

> ⚠️ **VERIFICATION (MANDATORY)**: After saving, run `read_file` on `subquestion_answers.json` and verify:
> 1. Exactly 8 answers exist
> 2. Every `answer_text` contains ≥3 specific numbers
> 3. Every `analysis_reasoning` contains at least one calculation
> 4. No `answer_text` is shorter than 150 words
> If any answer fails these checks, rewrite it before proceeding to Step 6.

### 5c. Aggregate analysis-driven product recommendations

After saving `subquestion_answers.json`, run `generate_ranked_recommendations()` to collect all
`recommended_asins` across dimensions, cross-match with `competitors.csv`, and rank by how many
dimensions recommended each ASIN.

> ⚠️ **IMPORTANT**: `pipeline.py` is a library, NOT a CLI script. You MUST use the two-step
> pattern: first `write_file` a runner script, then `bash_command` to execute it.
> Do NOT run `python pipeline.py --generate_ranked_recommendations` — it will produce no output.

**Step 1** — `write_file` to create the runner script:
```python
# File: /round-{N}/data/run_tier1.py
import sys
sys.path.insert(0, '/jungle-scout-deep-dive-analyzer/scripts')
from pipeline import generate_ranked_recommendations

ranked = generate_ranked_recommendations(base_dir="/round-{N}")
print(f"Analysis-driven recommendations: {len(ranked)} products")
for r in ranked[:10]:
    print(f"  {r['asin']} — {r['dimension_count']} dimensions — {r['title'][:60]}")
```

**Step 2** — `bash_command` to execute:
```bash
python /round-{N}/data/run_tier1.py
```

**Output**: `round-{N}/reports/product_recommendations_ranked.json`

> This is the **Tier-1** recommendation source. Products here were identified by the analysis itself,
> not by a generic search. They carry the highest recommendation weight in the final report.

---

## Step 6: Product Recommendations — 3-Tier Strategy <cite>[Amazon](https://www.amazon.com)</cite> <cite>[Jungle Scout](https://www.junglescout.com)</cite> <cite>[Web](https://www.google.com)</cite> <cite>[matplotlib](https://matplotlib.org)</cite>

**Script**: `scripts/pipeline.py` (`save_recommendations_csv()`, `generate_ranked_recommendations()`)

Product recommendations come from three sources, in priority order:

### 6a. Tier 1 — Analysis-Driven (from Step 5c)

Already generated in Step 5c as `product_recommendations_ranked.json`. No additional action needed here.

- Ranked by `dimension_count`, enriched with `competitors.csv` data, marked `recommendation_source: "analysis-driven"`
- Typical yield: 5–15 products. If 0 products, that's OK — proceed to Tier 2 and Tier 3

### 6b. Tier 2 — Data-Filtered (from `competitors.csv`)

If Tier 1 yields fewer than ~20 products, supplement from `competitors.csv` using data-driven filtering. Compute distribution stats first, then set relative thresholds (do NOT hardcode). Use `write_file` + `bash_command` pattern.

**Requirements**: `write_file` → `/round-{N}/data/filter_tier2.py`, then `bash_command`:
1. Deduplicate against Tier 1 ASINs
2. Mark with `recommendation_source: "data-filtered"` and `recommendation_reason`
3. Save to `{base_dir}/reports/_tier2_products.json`

Typical yield: 10–20 additional products.

### 6c. Tier 3 — Search Supplement (info_search shopping)

Fill remaining quota to reach ~50 total products and obtain `reference_id` for report display tags:

1. Call `info_search` with `shopping: true, allowed_sites: ["amazon.com"]` using 4–6 queries from sub-question conclusions
2. Results auto-saved to `/round-{N}/info_search/shopping_search/shopping_<query_slug>.csv`
3. Deduplicate against Tier 1 + Tier 2 ASINs — keep `reference_id` for matching products
4. New products get `recommendation_source: "search"`

> ⚠️ **`reference_id` is CRITICAL**: Only `info_search` returns `reference_id` (`competitors.csv` does NOT).
> Back-fill Tier 1/2 products' `reference_id` from matching search results for report display tags.

### 6d. Merge all tiers and save CSV

**Action**: `read_file` → `references/merge_tiers_example.md`, copy the script to `/round-{N}/data/merge_tiers.py` (replace `{N}`), then `bash_command` to execute.

> ⚠️ **DO NOT write your own merge script.** The reference implementation handles CSV column name mismatches, rating/price parsing, and reference_id backfilling that custom scripts (especially pandas-based) often break on. Copy it as-is.

Expected output: 40–80+ products total.

### 6e. Generate Charts (per `assets/chart-design-guide.md`)

The final report (Section 3 dimension answers + Section 4 strategic narrative) embeds chart images from `round-{N}/charts/`. You MUST produce these PNGs before Step 7.

**Action**:
1. `read_file` → `assets/chart-design-guide.md` for chart-type selection rules, Seaborn v0.12+ styling, and Jungle Scout-specific code recipes (uses real JS API field names like `monthly_search_volume_exact`, `organic_product_count`).
2. Decide which chart types to generate based on what the 8 dimension answers and Tier 1 narrative actually need (do NOT mechanically produce all 7). Typical minimum set:
   - **Sales/Search Trend** (line + area) — supports Market Size / Seasonality dimensions
   - **Opportunity Matrix** (scatter: search volume × competition) — supports Section 4 strategic narrative
   - **Multi-Metric Comparison** (horizontal bar) — supports Tier 1 product ranking
   - Add Price Distribution / Market Share / Radar / Heatmap only when the corresponding dimension answer cites that view.
3. `write_file` → `/round-{N}/data/generate_charts.py` (compose using recipes from the guide), then `bash_command` to execute. PNGs land in `/round-{N}/charts/`.

> ⚠️ **Diversity requirement**: Do NOT produce only bar charts or only line charts. The guide's "Chart Diversity Requirements" section is mandatory — pick chart types that match the data's analytical purpose, not the easiest default.

**Output**: 3–6 PNGs in `round-{N}/charts/`, named by content (e.g. `search_volume_trend.png`, `opportunity_matrix.png`, `top_products_comparison.png`).

### Step 6 Completion Checkpoint

Before proceeding to Step 7, verify ALL exist:
1. `round-{N}/reports/final_recommendations.csv` — `bash_command`: `wc -l` → must show ≥10 rows
2. `round-{N}/reports/product_recommendations_ranked.json` — Tier 1 products
3. `round-{N}/info_search/shopping_search/` — must contain ≥1 CSV file
4. `round-{N}/charts/` — `bash_command`: `ls round-{N}/charts/*.png | wc -l` → must show ≥3 PNGs

**If any is missing, go back and execute the corresponding Step 6 sub-step before proceeding.**

**Output**: `round-{N}/reports/final_recommendations.csv` + `round-{N}/charts/*.png`

---

## Step 7: B2B Supply Search + Write Final Report

> Execute AFTER Step 6.

### 7a. B2B Supply Search (per recommended direction)

Search suppliers **per direction** based on the Top 1–3 investable directions identified during analysis (from Step 5 answers and Section 3 conclusions). Each direction gets its own `product_supplier_search` call so results are grouped by recommendation.

**For each Top Pick direction**:
1. `product_supplier_search(intent_type="product", tasks=[{"query": "<direction-specific query>"}])` → collect `reference_id` for each product
2. If user explicitly asked for suppliers, also call `product_supplier_search(intent_type="supplier", tasks=[...])` for that direction. Default: product search only.

**Example** (2 directions):
```
# Direction 1: Premium Glass Blender
product_supplier_search(intent_type="product", tasks=[
  {"query": "premium high power portable blender glass bottle"}
])

# Direction 2: Mini USB-C Travel Blender  
product_supplier_search(intent_type="product", tasks=[
  {"query": "mini portable blender USB-C rechargeable travel"}
])
```

3. Generate `alibaba_supply.csv` from ALL directions combined (use `write_file` + `bash_command` pattern):
   ```python
   import sys
   sys.path.insert(0, '/jungle-scout-deep-dive-analyzer/scripts')
   from pipeline import save_alibaba_supply_csv
   save_alibaba_supply_csv(all_supplier_products, base_dir="/round-{N}")
   ```

### 7b. Write `final_report.md`

Use `write_file` directly — NOT `bash_command` (heredoc truncates content). Write the complete report in ONE call to avoid content loss from incremental edits. (Phase C may use `edit_file` to patch individual sections.)

### Phase A: Read ALL inputs (4 mandatory read_file calls)

You MUST execute ALL 4 `read_file` calls below BEFORE writing the report. Do NOT skip any.

| # | `read_file` target | What you get | Used in |
|---|-------------------|--------------|---------|
| 1 | `assets/report_template_zh.md` (zh) or `assets/report_template.md` (en) | Section structure + dimension template (7 sub-fields) + Section 4/7 writing approach | ALL sections |
| 2 | `round-{N}/reports/subquestion_answers.json` | 8 SubQuestionAnswer objects — the analytical backbone | Section 3 (3.1–3.8) |
| 3 | `round-{N}/reports/final_recommendations.csv` | ALL product recommendations with `reference_id` | Section 4 + Section 5 |
| 4 | `round-{N}/reports/product_recommendations_ranked.json` | Tier 1 analysis-driven products (subset of #3) | Section 4 strategic narrative |

> ⚠️ **MANDATORY PRE-CHECK after reading #3**: If `final_recommendations.csv` does not exist or has < 5 rows,
> STOP and go back to execute Step 6. Do NOT write a report without product recommendation data.

### Phase B: Assemble report — Section-by-Section mapping

After reading all 4 inputs, write the COMPLETE report in ONE `write_file` call to `/round-{N}/reports/final_report.md`.

**Section-by-Section assembly rules** (follow the template structure EXACTLY):

**Section 1 — Executive Summary**: Synthesize overall findings. 1 paragraph.

**Section 2 — Indicator Data Framework**: Markdown table with 3 columns (Indicator | Value | Explanation). Source: `indicator_framework.json` values you already have from Step 3. Use inline citation syntax per `<markdown_formatting_protocol>`.

**Section 3 — Deep-Dive Analysis (3.1–3.8)**: This is the report's core. Each of the 8 dimensions MUST follow the template's 7-field structure. Map `subquestion_answers.json` fields as follows:

| Template field | Source from SubQuestionAnswer | Minimum requirement |
|---------------|------------------------------|-------------------|
| **Core Question** | `question_text` from the matching subquestion | Copy verbatim |
| **Why this dimension** | Agent writes based on dimension context | 1–2 sentences |
| **Data Acquisition** | `citations` array | List source CSV files with inline cite syntax |
| **Key Data Points** (table) | `data_points` array | ≥3 rows, each with numeric value + unit + source |
| **Analysis** | `answer_text` + `analysis_reasoning` | ≥2 paragraphs, expand (not compress) the answer, show calculations |
| **Conclusion** (with confidence emoji) | `conclusion` + `confidence_level` (high=🟢, medium=🟡, low=🔴) | 1 sentence with THE key number |
| **Decision Impact** | Agent derives from conclusion | 1 sentence on entry decision implication |

> ⚠️ **COMMON FAILURE**: Agent compresses a dimension into 2-3 sentences without the table or sub-fields.
> Every dimension MUST have ALL 7 fields. If you find yourself writing a dimension in < 200 words, you are compressing — go back and expand.
> **Do NOT discard the structured answers and write a shallow summary instead.**

**Section 3 — Summary Table (after 3.8)**: After all 8 dimensions, add a summary table so readers can quickly grasp the overall picture:

```markdown
### Analysis Summary

| Dimension | Confidence | Key Finding | Decision Impact |
|-----------|------------|-------------|-----------------|
| 3.1 Market Size & Demand | 🟢 High | Long-tail aggregate 19x head term | Target niche keywords |
| 3.2 Competitive Landscape | 🟡 Medium | Top brand vulnerable on quality | Differentiate on rating |
| ... | ... | ... | ... |
```

Each row: dimension name, confidence emoji, one-sentence key finding (with the key number), one-sentence decision impact. All 8 rows required.

**Section 4 — Product Search & Positioning**: Follow the template's 5-part writing approach:
1. Market positioning summary (1–2 paragraphs synthesizing Section 3 findings)
2. **Analysis-driven product table** (from `final_recommendations.csv`): Build ONE unified table grouped by strategic theme (e.g., "Budget entry", "Premium gap", "Niche leader"), NOT by Tier 1/2/3. **≥10 product rows REQUIRED**. Use inline product cite per `<markdown_formatting_protocol>` in the Title column. Image column uses markdown image syntax with `imageUrl` from CSV. Add a heading like "### Recommended Products" to label the data source.
   ```markdown
   | Image | ASIN | Product Title | Price | Monthly Sales | Rating | Strategic Insight |
   |-------|------|---------------|-------|---------------|--------|-------------------|
   | ![](imageUrl) | B0XXXXXXXXX | Product Name [CITE:turnXproductY] | $XX.XX | X,XXX | 4.X | Why this product matters |
   ```
   Products without `reference_id` → no inline product cite, mention by ASIN only. Products without `imageUrl` → leave Image cell empty.
   > ⚠️ **ASIN column must contain the actual Amazon ASIN** (e.g., `B0D6NNPYTJ`), NOT a reference ID like `turn1product2`. Reference IDs go ONLY in `[CITE:...]` inside the Title column.
3. Positioning recommendation (1 paragraph)
4. Reference to `final_recommendations.csv` for complete list

> ⚠️ **Section 4 products MUST come from `final_recommendations.csv`** — NOT hand-picked from analysis text.
> ⚠️ **NEVER fabricate reference_ids** — only use IDs actually returned by tools.
> ⚠️ **Inside tables**: use `[CITE:turnXproductY]` for product references. **Outside tables** (own line): use `[PRODUCT:turnXproductY]` for carousel. See `<markdown_formatting_protocol>` in the system prompt.

**Section 5 — Conclusions & Actionable Recommendations**: This is the decision section — help the user act, not just read.

1. **Top 1–3 Picks Decision Table**: Distill the entire analysis into a comparison table of the most investable directions. Each row = one candidate direction (not a single ASIN, but a product strategy). Use `imageUrl` from `final_recommendations.csv` for the best representative product of each direction.
   ```markdown
   | | Pick 1: [Direction Name] | Pick 2: [Direction Name] | Pick 3: [Direction Name] |
   |---|---|---|---|
   | Representative Product | ![](imageUrl) [Product Name] | ![](imageUrl) [Product Name] | ![](imageUrl) [Product Name] |
   | Core Business Value | [Why this is worth pursuing] | ... | ... |
   | Target Margin | [Est. gross margin %] | ... | ... |
   | Key Risks | [Top 1–2 risks] | ... | ... |
   | Confidence | 🟢/🟡/🔴 | ... | ... |
   ```

2. **Actionable Next Steps** (4 concrete steps, not vague advice):
   - Step 1 (Sampling): Which suppliers to sample from, what to test
   - Step 2 (Cost Calculation): Landed cost estimation (shipping + tariff)
   - Step 3 (Small Batch Test): Recommended MOQ, fulfillment channel (e.g., FBA)
   - Step 4 (Branding): Logo printing, private label, packaging

**Section 6 — Risk Assessment**: Data gaps, monopoly risks, low-confidence areas.

**Section 7 — B2B Supply Recommendations**: Organize by recommended direction from Section 5. For each direction:

1. Direction heading (e.g., "### Direction 1: Premium Glass Blender")
2. Brief sourcing strategy for this direction (1–2 sentences)
3. Product carousel tag with this direction's supplier product reference IDs (MANDATORY, own line, per `<markdown_formatting_protocol>`)
4. Supplier product markdown table — each row with product image URL from search results + inline product cite per `<markdown_formatting_protocol>`. Columns: Image | Product Title | Platform | Price | MOQ. **4 rows per direction** (pick representative products across price/MOQ range).
5. Sourcing insight connecting supplier prices to Amazon margins for this direction

After all directions, add a reference to `alibaba_supply.csv` for the complete list.

> ⚠️ **Inside tables**: Image column uses `![](product_image_url)` from search results (NOT `[CITE:turnXimageY]`). Product title uses `[CITE:turnXproductY]`. **Outside tables** (own line): use `[PRODUCT:...]` for carousel.

### Phase C: Post-write verification

After `write_file`, run `read_file` on `final_report.md` and verify this checklist:

| # | Check | How to verify | If FAIL |
|---|-------|--------------|---------|
| 1 | All 7 sections present (1–7) | Scan for `## 1.` through `## 7.` headers | Rewrite |
| 2 | Section 3 has 8 sub-sections (3.1–3.8) | Scan for `### 3.1` through `### 3.8` | Rewrite |
| 3 | Section 3 ends with Analysis Summary table | Look for `### Analysis Summary` with 8 rows | Add it |
| 4 | Each 3.X has Key Data Points table | Look for `\|` table rows under each 3.X | Rewrite missing ones |
| 5 | Each 3.X has Conclusion with emoji | Look for 🟢/🟡/🔴 in each 3.X | Add missing |
| 6 | Section 4 "Recommended Products" table has ≥10 rows | Count `\|` data rows in the analysis-driven table | Rewrite Section 4 |
| 7 | Section 5 has Top Picks Decision Table | Look for Pick 1/2/3 comparison table | Add it |
| 8 | Section 7 has supplier product table per direction | Look for direction headings + tables | Rewrite Section 7 |
| 9 | Total word count ≥ 4000 | Estimate from file length | Expand thin sections |

> If any check fails, use `edit_file` to fix ONLY the failing section — do NOT rewrite the entire report.

**Quality requirements summary**:
- Total report ≥ 4000 words
- Section 3: all 8 dimensions × 7 fields each, ≥200 words per dimension
- Section 4: ≥10 products from CSV, grouped by strategic theme
- Section 7: Supplier table with image/product citations
- Use reference tags per `<markdown_formatting_protocol>` throughout
- Partial report > no report. If `write_file` fails, retry once, then summarize what was produced.

**Output**: `round-{N}/reports/final_report.md` + `round-{N}/reports/alibaba_supply.csv`

After Phase C passes, the task is complete. Summarize the report in chat (3–5 sentences) and reference the file path — do NOT paste the full report.

---

## Mandatory artifacts

See `references/csv_schema.md`. Both required:
- `final_recommendations.csv` — 13 columns (including `reference_id` from info_search)
- `alibaba_supply.csv` — 8 columns
- `final_report.md` — the deliverable, per Step 7

