# Indicator Definitions

Detailed definitions, calculation logic, and threshold standards for the Indicator Data Framework.

> This document expands on the SKILL.md Quick Reference with complete formulas and edge case handling.

---

## Indicator Computation Flow

```
User Query → Parse Scope → collect_js_data.py → analyze_indicators.py → indicator_framework.json
```

1. **Parse Scope**: Extract marketplace, category, keywords, ASINs, filters from user query
2. **Data Collection**: Run `scripts/collect_js_data.py` to call up to 6 JS APIs
3. **Indicator Computation**: Run `scripts/analyze_indicators.py` to compute 11 indicators
4. **Output**: `indicator_framework.json` (single JSON file with all 11 indicators)

---

## 11 Core Indicators

### 1. Main KW (Primary Keyword)

| Attribute | Detail |
|-----------|--------|
| **Definition** | The core search keyword for the category/product |
| **Data Source** | `keywords_by_keyword` → `keywords_market.csv` |
| **Calculation** | User-specified keyword, or keyword with highest `monthly_search_volume_exact` |
| **Output Format** | String — e.g. `"yoga mat"` |

### 2. Category

| Attribute | Detail |
|-----------|--------|
| **Definition** | Amazon category the product belongs to |
| **Data Source** | `product_database` → `competitors.csv` |
| **Calculation** | Most frequent category (mode) from returned products |
| **Output Format** | String — e.g. `"Sports & Outdoors"` |

### 3. Search Volume

| Attribute | Detail |
|-----------|--------|
| **Definition** | Monthly exact search volume for the main keyword |
| **Data Source** | `keywords_by_keyword` → `keywords_market.csv` |
| **Calculation** | Read `monthly_search_volume_exact` for Main KW |
| **Thresholds** | >10K = large market; 5K-10K = medium; <5K = niche |
| **Output Format** | Integer — e.g. `148,000` |

### 4. Top 1 Seller Revenue

| Attribute | Detail |
|-----------|--------|
| **Definition** | Estimated monthly revenue of the current market leader |
| **Data Source** | `sales_estimates` + `product_database` |
| **Calculation** | `Revenue = Daily Sales × Price × 30`, take maximum |
| **Thresholds** | >$100K = large market; $50K-$100K = medium; <$50K = small |
| **Output Format** | USD — e.g. `$125,400` |

### 5. $5K+ Listings

| Attribute | Detail |
|-----------|--------|
| **Definition** | Number of active listings with monthly revenue > $5,000 |
| **Data Source** | `product_database` + `sales_estimates` |
| **Calculation** | Iterate product list, compute monthly revenue per ASIN, count where > $5,000 |
| **Business Meaning** | Measures long-tail market viability — higher count means small sellers can profit |
| **Output Format** | Integer — e.g. `42` |

### 6. Avg Price / Weight / FBA Fee

| Attribute | Detail |
|-----------|--------|
| **Definition** | Average selling price, weight, and FBA fee from competitor pool |
| **Data Source** | `product_database` → `competitors.csv` |
| **Calculation** | `mean(price)`, `mean(weight)`, FBA estimated from weight + dimensions |
| **Business Meaning** | Baseline values for profit calculation |
| **Output Format** | USD / lbs / USD — e.g. `$29.99 / 2.1 lbs / $5.42` |

### 7. Avg Reviews / Rating

| Attribute | Detail |
|-----------|--------|
| **Definition** | Average review count and rating from Top 10-50 products |
| **Data Source** | `product_database` → `competitors.csv` |
| **Calculation** | `mean(reviews)` and `mean(rating)` from Top 10-50 products |
| **Thresholds** | Reviews <500 = low barrier; 500-2000 = medium; >2000 = high barrier |
| **Output Format** | Integer / Float — e.g. `1,245 / 4.3` |

### 8. Monopoly

| Attribute | Detail |
|-----------|--------|
| **Definition** | Market brand concentration assessment |
| **Data Source** | `share_of_voice` → `market_concentration.csv` |
| **Calculation** | See algorithm below |
| **Output Format** | Traffic light — 🔴 / 🟡 / 🟢 + description |

**Monopoly Detection Algorithm**:
```
top_brand_share = max(combined_weighted_sov)
top3_share = sum(top 3 combined_weighted_sov)

top_brand_share > 0.30 → 🔴 "Single brand monopoly"
top3_share > 0.60      → 🟡 "Concentrated market"
otherwise              → 🟢 "Fragmented market"

If top brand == "Amazon" → "Amazon monopoly"
Else                     → "Third-party brand monopoly"
```

### 9. Seasonality

| Attribute | Detail |
|-----------|--------|
| **Definition** | Whether product demand has seasonal fluctuations |
| **Data Source** | `historical_search_volume` → `keyword_trends.csv` |
| **Calculation** | See algorithm below |
| **Output Format** | Classification — `"Seasonal"` / `"Non-seasonal"` / `"Insufficient data"` |

**Seasonality Variance Algorithm**:
```
mean = sum(values) / N
std  = sqrt(sum((vi - mean)²) / N)
cv   = std / mean

cv > 0.5  → "Seasonal"
cv ≤ 0.5  → "Non-seasonal"
N < 12    → "Insufficient data"
mean == 0 → "No search volume"
```

### 10. Traffic Ratio (Organic vs Paid)

| Attribute | Detail |
|-----------|--------|
| **Definition** | Ratio of organic search vs paid ads in first-page traffic |
| **Data Source** | `share_of_voice` → `market_concentration.csv` |
| **Calculation** | `sponsored_ratio = sponsored_click_share / (organic + sponsored)` |
| **Thresholds** | sponsored_ratio > 0.80 → ⚠️ High ad dependency (profit erosion risk) |
| **Output Format** | Percentage — e.g. `"Organic 35% / Paid 65%"` |

### 11. PPC Bid / Conversion

| Attribute | Detail |
|-----------|--------|
| **Definition** | PPC bid range and category average conversion rate |
| **Data Source** | `share_of_voice` + `keywords_market.csv` |
| **Calculation** | `min/max(ppc_bid_exact)` + category average conversion rate |
| **Business Meaning** | Sets upper bound for marketing cost (ACOS) in profit calculation |
| **Output Format** | USD range + percentage — e.g. `"$0.85 - $2.30 / Conv. 12.5%"` |

---

## Indicator Data Framework Template

```markdown
| Indicator | Value | Derivation Logic |
|-----------|-------|------------------|
| **Main KW** | "{keyword}" | {derivation} [cite source per <markdown_formatting_protocol>] |
| **Category** | {category} | Dominant category from product_database. |
| **Search Volume** | {volume} | `monthly_search_volume_exact` for Main KW. [cite source] |
| **Top 1 Seller Revenue** | ${revenue} | Daily Sales ({daily}) × Price (${price}) × 30. [cite source] |
| **$5K+ Listings** | {count} | Count of ASINs with monthly revenue > $5,000. |
| **Avg Price / Weight / FBA** | ${price} / {weight} lbs / ${fba} | Mean values from competitors.csv. |
| **Avg Reviews / Rating** | {reviews} / {rating} | Mean from Top {n} products. |
| **Monopoly** | {emoji} {classification} (Top 1: {share}%) | {description} [cite source] |
| **Seasonality** | {classification} (CV: {cv}) | CV = {cv} {comparison} 0.5 threshold. |
| **Traffic Ratio** | Organic {organic}% / Paid {paid}% | From share_of_voice click shares. |
| **PPC Bid / Conv.** | ${min} - ${max} / {conv}% | Bid range from keywords_market.csv. |
```

---

## Data Quality Checks

Perform these data quality checks when computing each indicator:

| Check | Action |
|-------|--------|
| Empty data | Mark as "Data unavailable", do not force calculation |
| Insufficient data points | Mark as "Insufficient data", explain required count |
| Outliers | Exclude price=0, extreme high values, etc. |
| Data inconsistency | Cross-validate multiple sources, note discrepancies |

---

## Implementation Reference

- Indicator calculation script → `scripts/analyze_indicators.py`
- Data collection script → `scripts/collect_js_data.py`

