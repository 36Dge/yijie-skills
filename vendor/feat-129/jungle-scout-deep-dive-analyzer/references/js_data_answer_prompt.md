# Real Data Answer — Output Schema & Quality Rules

> **Context**: In Step 5, the Agent itself IS the analyst. The Agent reads CSV data
> extracted by `answer_with_js_data.extract_relevant_data()` plus `indicator_framework.json`,
> then directly constructs `SubQuestionAnswer` objects. There is NO external LLM call.
>
> This document defines the **output JSON schema** and **quality rules** that every
> `SubQuestionAnswer` must satisfy.

## Output JSON Schema

Each `SubQuestionAnswer` must match this structure (see `scripts/models.py`).

Choose the best `presentation_format`:
- `"table"` — structured numeric data points (e.g. search volume, market share, pricing)
- `"text"` — primarily qualitative analysis or narrative (e.g. pain points, barriers)
- `"chart"` — trends or comparisons over time (include `chart_suggestion`)
- `"mixed"` — both a data table and significant narrative explanation

```json
{
  "question_id": "{question_id}",
  "presentation_format": "table | text | chart | mixed",
  "answer_text": "A data-driven answer citing real numbers from the Jungle Scout data. Example: 'Monthly search volume for \"yoga mat\" is 148,000 from keywords_market.csv. The top brand holds 33.1% market share from market_concentration.csv. Historical trend shows 12.3% YoY growth from keyword_trends.csv.'",
  "data_points": [
    {
      "metric": "Monthly Search Volume",
      "value": "148000",
      "unit": "searches/month",
      "source": "keywords_market.csv"
    },
    {
      "metric": "Top Brand Market Share",
      "value": "33.1",
      "unit": "%",
      "source": "market_concentration.csv"
    },
    {
      "metric": "YoY Search Growth",
      "value": "12.3",
      "unit": "%",
      "source": "keyword_trends.csv"
    }
  ],
  "chart_suggestion": "(Only when presentation_format is 'chart' or 'mixed') Describe the ideal chart, e.g. 'Line chart: monthly search volume over 12 months, X=month, Y=volume'",
  "confidence_level": "high | medium | low",
  "analysis_reasoning": "Step-by-step calculation referencing specific real data values. Example: 'From competitors.csv: avg price = $30.35 across 45 products. Top 20 products avg reviews = 1,247. From keywords_market.csv: main keyword volume = 148,000, top 5 related keywords total = 312,000. Growth rate = (Dec volume 155K - Jan volume 138K) / 138K = 12.3%.'",
  "conclusion": "One-sentence conclusion with the key number. Example: 'The market shows healthy 12.3% growth with moderate brand concentration (Top1: 33.1%), indicating viable entry opportunity.'",
  "citations": ["keywords_market.csv", "market_concentration.csv", "keyword_trends.csv"],
  "recommended_asins": [
    {"asin": "B0XXXXXX", "reason": "Lowest review count (234) among top-10 revenue products — weak incumbent"},
    {"asin": "B0YYYYYY", "reason": "Only brand in $45+ tier with rating < 4.0 — quality gap opportunity"}
  ]
}
```

## Output Rules

- `presentation_format` MUST be one of: `table`, `text`, `chart`, `mixed`. Choose the format that best fits the data and question.
- `answer_text` MUST contain specific numbers from the real data. Do NOT write vague statements — cite actual values.
- `data_points` — required for `table` and `mixed` formats (at least 3 entries with numeric `value`). Optional for `text` and `chart` formats. ⚠️ NEVER output an empty `data_points` array when `presentation_format` is `table` or `mixed` — if data is insufficient, switch to `text` format instead.
- `chart_suggestion` — required for `chart` and `mixed` formats. Describe the chart type, axes, and data series.
- `analysis_reasoning` MUST show calculations referencing real data values. Do NOT just restate facts.
- `confidence_level` MUST be exactly one of: `high`, `medium`, `low`.
- `citations` MUST include the specific data sources used (e.g., `"keywords_market.csv"`, `"market_concentration.csv"`, `"competitors.csv"`).
- `recommended_asins` is OPTIONAL per dimension. Include only when the analysis naturally identifies specific products from `competitors.csv` (e.g., competition gaps, entry barriers, pain-point opportunities). Typical dimensions: `competitive_landscape`, `entry_barrier`, `niche_opportunities`, `pain_points`. Do NOT force product recommendations for dimensions like `demand_seasonality` or `market_size_demand` where product-level mapping is unnatural.

---

## Data Extraction Helper

The script `answer_with_js_data.py` provides data extraction only — no LLM calls.

```python
from answer_with_js_data import set_data_dir, extract_relevant_data

set_data_dir("/round-{N}/data")
relevant_data = extract_relevant_data(question)  # returns dict of CSV summaries
```

The `_DIMENSION_DATA_MAP` in `answer_with_js_data.py` maps `target_dimension` values to CSV files. If no specific match, all core CSVs are loaded as fallback.

## Quality Rules

- **Data-First**: Every answer MUST lead with concrete numbers. `answer_text` must cite specific CSV values. For `table`/`mixed` formats, `data_points` must have ≥3 entries with numeric values and a `source` field.
- **Non-Empty Table/Chart**: If `presentation_format` is `table`/`mixed`, `data_points` MUST contain real numeric rows. If data is insufficient, switch to `text` format.
- **Agent IS the Analyst**: The Agent reads the extracted data, reasons over it, and directly constructs `SubQuestionAnswer` objects. There is NO `call_llm()` or nested LLM invocation in this step.

