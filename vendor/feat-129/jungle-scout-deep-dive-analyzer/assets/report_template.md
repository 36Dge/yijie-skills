# {product} — Amazon Market Intelligence Report

> **Methodology**: Real Data Intelligence Pipeline (Jungle Scout API)

---

## 1. Executive Summary

[Brief overview: analysis scope, question type, 8 dimensions covered, confidence distribution, top-line recommendation]

---

## 2. Indicator Data Framework <cite>[Jungle Scout](https://www.junglescout.com)</cite>

The 11 core metrics below form the analytical foundation. Anomalies and extremes in these indicators directly drove the sub-question generation in the next section.

**Format**: markdown table with 3 columns — Indicator | Value | Explanation. Do NOT use bullet list.

Use inline citation syntax (per `<markdown_formatting_protocol>`) to reference the data source files.

---

## 3. Deep-Dive Analysis <cite>[Jungle Scout](https://www.junglescout.com)</cite>

8 dimension sections (3.1 through 3.8), each with the full analytical chain below.

⚠️ Use standard dimension names as section headers, NOT the full question text.
⚠️ Number 3.1, 3.2, 3.3, … in order. Never skip, duplicate, or reorder.
⚠️ Use English dimension names for `en` reports, Chinese for `zh` reports.

### Dimension Template

```markdown
### 3.X [Dimension Name]

**Core Question**: [The specific question being answered]

**Why this dimension**: [Why this matters for the entry decision]

**Data Acquisition**: <cite>[Jungle Scout](https://www.junglescout.com)</cite> [cite data source files per <markdown_formatting_protocol>]
- Source: [e.g., historical_search_volume, keywords_by_keyword]
- Expected format: [e.g., 12-month time series + long-tail keyword list]

**Key Data Points**:
| Metric | Value | Unit |
|--------|-------|------|
| [metric] | [NUMERIC value] | [unit] |
| [metric] | [NUMERIC value] | [unit] |
| [metric] | [NUMERIC value] | [unit] |

(Minimum 3 rows with numeric values. If data insufficient, omit table and use narrative.)

**Analysis**:
[2-4 sentences with calculations. Show derivations.]

[Insert chart image using image display syntax per <markdown_formatting_protocol>]

**Conclusion** (Confidence: 🟢/🟡/🔴 High/Medium/Low):
[One clear sentence with the key number.]

**Decision Impact**: [One sentence on how this affects the entry decision]
```

Do NOT compress dimensions into one-line summaries — each must have the full structure above.

### Analysis Summary

After all 8 dimensions (3.1–3.8), add a summary table:

| Dimension | Confidence | Key Finding | Decision Impact |
|-----------|------------|-------------|-----------------|
| 3.1 [name] | 🟢/🟡/🔴 | One sentence with key number | One sentence on entry decision |
| 3.2 [name] | ... | ... | ... |
| ... | ... | ... | ... |

All 8 rows required.

---

## 4. Product Search & Positioning <cite>[Amazon](https://www.amazon.com)</cite> <cite>[Jungle Scout](https://www.junglescout.com)</cite> <cite>[Web](https://www.google.com)</cite>

> ⚠️ Do NOT expose the internal 3-tier filtering mechanism (Tier 1/2/3) to the reader.
> Instead, synthesize the analysis findings into a natural narrative that leads to product recommendations.

### Writing approach

1. **Market positioning summary** (1–2 paragraphs): Synthesize key findings from Section 3 — price tiers, competitive gaps, niche opportunities, pain points — into a cohesive market landscape picture. Identify the strategic entry windows.

2. **Analysis-driven product table** (heading: "### Recommended Products"): Naturally introduce the top recommended products as evidence of the opportunities identified above. Use a single unified table grouped by strategic theme (e.g., "Budget entry opportunity", "Premium gap", "Niche leader to study"), NOT by data source.

   ⚠️ Product data MUST come from `final_recommendations.csv` (≥10 products), NOT hand-picked examples from analysis text.

   Each row with markdown image from `imageUrl` and inline product citation (per `<markdown_formatting_protocol>`):
   ```markdown
   | Image | ASIN | Product Title | Price | Monthly Sales | Rating | Strategic Insight |
   |-------|------|---------------|-------|---------------|--------|-------------------|
   | ![](imageUrl) | B0XXXXXXXXX | Product Name [CITE:turnXproductY] | $XX.XX | X,XXX | 4.X | Why this product matters |
   ```

3. **Positioning recommendation** (1 paragraph): Based on the products above, recommend specific positioning strategy (price point, differentiation angle, target customer segment).

4. Reference to `final_recommendations.csv` for the complete product list.

---

## 5. Conclusions & Actionable Recommendations

### Top Picks Decision Table

Distill the analysis into 1–3 most investable directions. Each column = one candidate strategy with a representative product image.

| | Pick 1 | Pick 2 | Pick 3 |
|---|---|---|---|
| Representative Product | ![](imageUrl) Product Name | ![](imageUrl) Product Name | ![](imageUrl) Product Name |
| Core Business Value | Why worth pursuing | ... | ... |
| Target Margin | Est. gross margin % | ... | ... |
| Key Risks | Top 1–2 risks | ... | ... |
| Confidence | 🟢/🟡/🔴 | ... | ... |

### Actionable Next Steps

Concrete 4-step action plan:
- Step 1 (Sampling): Which suppliers to sample from, what to test
- Step 2 (Cost Calculation): Landed cost estimation (shipping + tariff)
- Step 3 (Small Batch Test): Recommended MOQ, fulfillment channel
- Step 4 (Branding): Logo printing, private label, packaging

---

## 6. Risk Assessment

Data gaps, monopoly risks, low-confidence areas, API data coverage limitations.

---

## 7. B2B Supply Search Recommendations

Organize by recommended direction from Section 5. For each direction:

### Direction N: [Direction Name]

1. Brief sourcing strategy for this direction
2. Product carousel tag with this direction's supplier product reference IDs (MANDATORY, on its own line, per `<markdown_formatting_protocol>`)
3. Supplier product markdown table (MANDATORY, **4 rows per direction**) — each row with product image URL and inline product citation (per `<markdown_formatting_protocol>`):
   ```markdown
   | Image | Product Title | Platform | Price | MOQ |
   |-------|---------------|----------|-------|-----|
   | ![](product_image_url) | Product Name [CITE:turnXproductY] | Platform | $0.52-0.99 | 100 pcs |
   ```
4. Sourcing insight connecting supplier prices to Amazon margins for this direction

Repeat for each direction (1–3 total). End with reference to `alibaba_supply.csv`.

