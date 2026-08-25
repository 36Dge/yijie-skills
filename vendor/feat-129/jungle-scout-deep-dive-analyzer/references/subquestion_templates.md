# Sub-Question Templates

Template library for sub-question generation, organized by question type.

> This document expands on the SKILL.md Quick Reference with complete sub-question templates and answering workflows.

---

## Sub-Question Generation Flow

```
Indicator Framework → Identify Question Type → Generate 8 Sub-Questions → Save subquestions.json
```

1. **Identify Type**: Detect question type from user query keywords
2. **Generate Questions**: Generate 8 sub-questions (one per standard dimension defined in SKILL.md Step 4)
3. **Save**: Save to `round-{N}/reports/subquestions.json`
4. **Answer (Step 5)**: Agent reads CSV data + indicators → constructs SubQuestionAnswer objects directly
5. **Output**: Structured answers (`subquestion_answers.json`) feed into `final_report.md` Section 3 (Deep-Dive Analysis)

---

## Question Type Detection

Identify question type based on keywords in user query:

| Type | Trigger Keywords (EN) | Trigger Keywords (ZH) | Focus Areas |
|------|----------------------|----------------------|-------------|
| **Market Opportunity** | blue ocean, opportunity, potential, discover, find, niche | 蓝海, 机会, 潜力, 发现, 寻找, 利基, 商机 | Demand gaps, low-competition niches, growth trends |
| **Competitive Analysis** | competitor, ASIN, rival, analyze, compare | 竞争, 竞品, 对手, 分析, 对比, 比较 | Competitor keywords, brand share, sales trends |
| **Product Validation** | validate, worth, feasible, enter, evaluate | 验证, 值得, 可行, 进入, 评估, 能不能做, 能做吗 | Market size, competition level, profit margins |
| **Ad & Traffic** | ads, PPC, traffic, bid, conversion, promote | 广告, 流量, 竞价, 转化, 推广, 投放 | Traffic structure, ad costs, organic opportunities |
| **Trend & Seasonality** | trend, seasonal, growth, change, cycle, fluctuation | 趋势, 季节, 增长, 变化, 周期, 波动 | Search volume trends, peak/trough timing |

Default: **Product Validation**.

---

## Dimension-to-Indicator Mapping

When generating sub-questions, use indicator anomalies to inspire targeted questions:

| Dimension | Indicator Pattern | Inspired Sub-Question |
|-----------|-------------------|----------------------|
| Market Size & Demand | Search Volume = 148K, YoY +12% | "What is the 12-month search volume trend and long-tail keyword potential?" |
| Competitive Landscape | Monopoly = 🔴 (Top1 > 30%) | "How concentrated is brand share? Is there room for a new entrant?" |
| Demand Seasonality & Stability | Seasonality CV > 0.5 | "What are the peak and trough months? Seasonal or year-round strategy?" |
| Margin Analysis | Avg Price = $30.35, FBA = $5.42 | "Given avg price and FBA fees, what is the estimated net margin?" |
| Barrier to Entry | Avg Reviews > 1000 | "Is the review barrier too high? Can new entrants compete?" |
| Marketing & Traffic | PPC Bid range wide ($0.42–$4.71) | "What explains the wide PPC bid spread? Are there low-cost long-tail keywords?" |
| Niche Opportunities | Multiple sub-categories detected | "Are there underserved sub-niches with lower competition?" |
| User Pain-Points | Low avg rating in segment | "What are the common pain points from negative reviews?" |

---

## Type 1: Market Opportunity Discovery

### Core Focus
- Where are the demand gaps?
- Which segments have lower competition?
- What are the growth trends?

### Sub-Question Templates

#### Q1: Keyword Search Volume Trend Analysis
**Question**: For products in {category} with {filters}, are the core keyword search volumes trending up or down?

**Data Sources**: 
- `historical_search_volume` → keyword_trends.csv

**Analysis Steps**:
1. Extract target keyword list
2. Get 12-month search volume time series
3. Calculate growth rate = (recent 3-month avg - prior 3-month avg) / prior 3-month avg
4. Plot trend chart, annotate growth/decline periods

**Output**: Trend chart + growth rate classification (growing/stable/declining)

---

#### Q2: Brand Concentration Analysis
**Question**: In the search results for these keywords, is the top brand share highly concentrated?

**Data Sources**: 
- `share_of_voice` → market_concentration.csv

**Analysis Steps**:
1. Get share_of_voice data for each keyword
2. Calculate Top 1 brand share and Top 3 cumulative share
3. Determine concentration: Top1 > 30% = high; Top3 > 60% = medium; else = dispersed

**Output**: Brand share bar chart + concentration rating

---

#### Q3: Low-Rating Opportunity Mining
**Question**: Among keywords with {threshold}+ search volume and sustained growth, which have products with average rating below 4.2 in the top 3 pages?

**Data Sources**: 
- `keywords_by_keyword` → keywords_market.csv
- `product_database` → competitors.csv

**Analysis Steps**:
1. Filter keywords with search volume > threshold
2. Cross-validate growth trend (from Q1)
3. Get product list for these keywords
4. Calculate average rating, filter < 4.2

**Output**: Low-rating opportunity list (keyword + avg rating + search volume)

---

#### Q4: Ad Competition Analysis
**Question**: What are the paid search bids for these keywords, and what's the top brand paid share?

**Data Sources**: 
- `share_of_voice` → market_concentration.csv
- `keywords_by_keyword` → keywords_market.csv

**Analysis Steps**:
1. Get ppc_bid_exact for each keyword
2. Get sponsored_click_share distribution
3. Calculate ad dependency = sponsored / (organic + sponsored)

**Output**: PPC bid range + ad dependency rating

---

#### Q5: Long-Tail Keyword Breakthrough
**Question**: Which long-tail keywords have high search volume but low competition that could serve as traffic entry points?

**Data Sources**: 
- `keywords_by_keyword` → keywords_market.csv

**Analysis Steps**:
1. Get expanded keyword list
2. Calculate opportunity score = search_volume / organic_product_count
3. Filter keywords with ease_of_ranking_score > 5
4. Plot scatter chart (X: competition, Y: search volume)

**Output**: Keyword opportunity scatter plot + Top 5 breakthrough list

---

#### Q6: Margin & Price Positioning
**Question**: Given the average price, FBA fees, and estimated COGS, what is the net margin for products in this category?

**Data Sources**: 
- `product_database` → competitors.csv

**Analysis Steps**:
1. Calculate average price from competitor pool
2. Estimate FBA fee from weight/dimensions
3. Estimate COGS at 30% of price
4. Calculate net margin = (price - FBA - COGS) / price

**Output**: Three-tier margin table (25th/50th/75th percentile) + 25% threshold flag

---

#### Q7: Entry Barrier Assessment
**Question**: What is the average review count and rating for the top 20 products? How high is the barrier for a new entrant?

**Data Sources**: 
- `product_database` → competitors.csv

**Analysis Steps**:
1. Get Top 20 products by sales
2. Calculate average reviews and rating
3. Assess barrier: <500 reviews = low, 500-2000 = medium, >2000 = high

**Output**: Review/rating distribution + barrier rating

---

#### Q8: User Pain-Point Mining
**Question**: Among the top products, which have ratings below 4.2? What common complaints might indicate differentiation opportunities?

**Data Sources**: 
- `product_database` → competitors.csv

**Analysis Steps**:
1. Filter products with rating < 4.2
2. Cross-reference with sales volume (high sales + low rating = pain-point opportunity)
3. Identify product categories with consistent low ratings

**Output**: Pain-point opportunity list (product + rating + sales volume)

---

## Type 2: Competitive Analysis

### Core Focus
- What are the competitor's traffic sources?
- What are the competitor's sales and pricing strategies?
- Which keywords are not covered by competitors?

### Sub-Question Templates

#### Q1: Competitor Keyword Matrix
**Question**: What are the top-ranking keywords for competitor {ASIN}? What's this competitor's organic search share rank for these keywords?

**Data Sources**: 
- `keywords_by_asin` → asin_keywords.csv
- `share_of_voice` → market_concentration.csv

**Analysis Steps**:
1. Call keywords_by_asin to get competitor keywords
2. Sort by organic_rank
3. Call share_of_voice for Top 10 keywords
4. Locate competitor's share rank for each keyword

**Output**: Keyword traffic matrix table

---

#### Q2: Sales & Price Fluctuation
**Question**: How did this ASIN's sales and price fluctuate over the past 30 days? Are there signs of a price war?

**Data Sources**: 
- `sales_estimates` → asin_sales.csv

**Analysis Steps**:
1. Get 30-day sales and price time series
2. Calculate price volatility = std(price) / mean(price)
3. Detect price decline trend
4. Plot dual-axis chart (sales + price)

**Output**: Sales/price fluctuation chart + price war risk assessment

---

#### Q3: Keyword Gap Analysis
**Question**: What related long-tail keywords are not covered by this competitor?

**Data Sources**: 
- `keywords_by_keyword` → keywords_market.csv
- `keywords_by_asin` → asin_keywords.csv

**Analysis Steps**:
1. Get expanded keyword list for main keyword
2. Get keywords already covered by competitor
3. Calculate difference = expanded keywords - competitor keywords
4. Sort by search volume

**Output**: Keyword gap list (uncovered keywords + search volume)

---

#### Q4: Multi-Competitor Comparison
**Question**: Comparing ASIN A and ASIN B, what keywords do they both cover? How different are their search rankings on these shared keywords?

**Data Sources**: 
- `keywords_by_asin` (multiple ASINs)

**Analysis Steps**:
1. Get keywords for both ASINs separately
2. Calculate intersection
3. Compare organic_rank for each shared keyword
4. Calculate ranking difference

**Output**: Keyword overlap analysis table

---

#### Q5: Listing Quality Assessment
**Question**: What's the competitor's Listing Quality Score? What optimization opportunities exist?

**Data Sources**: 
- `product_database` → competitors.csv

**Analysis Steps**:
1. Get competitor's listing_quality_score
2. Compare with category average
3. Identify dimensions below average

**Output**: LQS score + optimization recommendations

---

#### Q6: Seasonality & Demand Stability
**Question**: Does the competitor's product category show seasonal demand patterns? How stable is search volume over 12 months?

**Data Sources**: 
- `historical_search_volume` → keyword_trends.csv

**Analysis Steps**:
1. Get 12-month search volume for competitor's main keywords
2. Calculate CV (coefficient of variation)
3. Classify: CV > 0.5 = seasonal, CV ≤ 0.5 = non-seasonal

**Output**: Seasonality classification + trend chart

---

#### Q7: Niche Sub-Category Opportunities
**Question**: Are there sub-niches within the competitor's category that have lower competition but meaningful search volume?

**Data Sources**: 
- `keywords_by_keyword` → keywords_market.csv
- `product_database` → competitors.csv

**Analysis Steps**:
1. Expand keyword list for the category
2. Identify long-tail keywords with high volume but low organic_product_count
3. Cross-reference with competitor's keyword coverage

**Output**: Niche keyword opportunity list

---

#### Q8: Margin & Pricing Strategy
**Question**: What is the competitor's pricing strategy relative to the category average? Is there margin room for a new entrant?

**Data Sources**: 
- `product_database` → competitors.csv

**Analysis Steps**:
1. Compare competitor price vs category average
2. Estimate FBA fees and COGS
3. Calculate margin at different price points

**Output**: Pricing comparison table + margin estimate

---

## Type 3: Product Validation

### Core Focus
- Is the market size large enough?
- How high is the competition barrier?
- Is the profit margin sufficient?

### Sub-Question Templates

#### Q1: Search Volume Trend Validation
**Question**: What's the search volume trend for '{keyword}' over the past 6 months? Is it growing, stable, or declining?

**Data Sources**: 
- `historical_search_volume` → keyword_trends.csv

**Analysis Steps**:
1. Get 6-12 months of search volume data
2. Calculate trend slope
3. Classify: slope > 0.1 = growing; -0.1~0.1 = stable; < -0.1 = declining

**Output**: Trend chart + trend classification

---

#### Q2: Market Monopoly Assessment
**Question**: In the current top 3 pages of search results, what's the Top 3 brand combined share? Is the market monopolized?

**Data Sources**: 
- `share_of_voice` → market_concentration.csv

**Analysis Steps**:
1. Get share_of_voice data
2. Calculate Top 3 cumulative share
3. Check for Amazon presence

**Output**: Brand share pie chart + monopoly rating

---

#### Q3: Entry Barrier Analysis
**Question**: What's the monthly sales and review count distribution for Top 10 products? How high is the entry barrier?

**Data Sources**: 
- `product_database` → competitors.csv
- `sales_estimates` → asin_sales.csv

**Analysis Steps**:
1. Get Top 10 product data
2. Calculate monthly sales distribution
3. Calculate review count distribution
4. Assess entry barrier

**Output**: Sales/review distribution chart + barrier rating

---

#### Q4: Keyword Expansion
**Question**: What other related keywords (like '{variant_1}', '{variant_2}') have notable search volume worth attention?

**Data Sources**: 
- `keywords_by_keyword` → keywords_market.csv

**Analysis Steps**:
1. Expand search for related keywords
2. Sort by search volume
3. Identify high-potential variant keywords

**Output**: Keyword expansion table

---

#### Q5: Profit Calculation
**Question**: Based on current price range and cost structure, what's the estimated net margin? Does it exceed the 25% threshold?

**Data Sources**: 
- `product_database` → competitors.csv
- `product_supplier_search` → sourcing cost
- `tariff-search` → tariff rates

**Analysis Steps**:
1. Calculate three price tiers (25th/50th/75th percentile)
2. Estimate landing cost (EXW + shipping + tariff)
3. Calculate FBA fee
4. Calculate net margin

**Output**: Three-tier profit calculation table + 25% threshold flag

---

#### Q6: Demand Seasonality
**Question**: Is '{keyword}' a seasonal product? What are the peak and trough months?

**Data Sources**: 
- `historical_search_volume` → keyword_trends.csv

**Analysis Steps**:
1. Get 12-month search volume time series
2. Calculate CV (coefficient of variation)
3. Identify peak and trough months
4. Classify: CV > 0.5 = seasonal, CV ≤ 0.5 = non-seasonal

**Output**: Seasonality classification + peak/trough months + trend chart

---

#### Q7: Niche Differentiation Opportunities
**Question**: Are there underserved sub-niches within the '{keyword}' market with lower competition?

**Data Sources**: 
- `keywords_by_keyword` → keywords_market.csv
- `product_database` → competitors.csv

**Analysis Steps**:
1. Identify long-tail keyword variants
2. Filter by high search volume + low organic_product_count
3. Check if existing products in these niches have low ratings (< 4.2)

**Output**: Niche opportunity list (keyword + volume + competition + avg rating)

---

#### Q8: User Pain-Points & Review Analysis
**Question**: What are the common pain points among top-selling products? Are there quality gaps a new entrant could exploit?

**Data Sources**: 
- `product_database` → competitors.csv

**Analysis Steps**:
1. Identify products with high sales but rating < 4.3
2. Calculate the gap between best-rated and worst-rated products
3. Assess whether quality differentiation is viable

**Output**: Pain-point opportunity assessment + differentiation recommendations

---

## Type 4: Ad & Traffic Strategy

### Sub-Question Templates

#### Q1: PPC Bid Analysis
**Question**: What's the paid search bid range for keyword '{keyword}'?

**Data Sources**: 
- `keywords_by_keyword` → keywords_market.csv

**Output**: PPC bid range + competition rating

---

#### Q2: Organic vs Paid Brand Comparison
**Question**: Are the Top 3 organic search brands the same as the Top 3 paid search brands?

**Data Sources**: 
- `share_of_voice` → market_concentration.csv

**Output**: Brand comparison table + difference analysis

---

#### Q3: Top Converter Analysis
**Question**: What's the monthly sales and price for the ASIN with the highest conversion rate in the past week?

**Data Sources**: 
- `sales_estimates` + `product_database`

**Output**: Top converter ASIN details

---

#### Q4: Low-Competition Long-Tail Keywords
**Question**: Among related long-tail keywords, which have decent search volume but lower paid competition?

**Data Sources**: 
- `keywords_by_keyword` → keywords_market.csv

**Output**: Low-competition keyword list

---

#### Q5: ACOS Estimation
**Question**: If entering this market through advertising, what's the estimated ACOS?

**Data Sources**: 
- `share_of_voice` + profit calculation

**Output**: ACOS estimate + break-even analysis

---

#### Q6: Entry Barrier via Reviews
**Question**: What is the average review count for the top 20 products? How long would it take a new entrant to reach competitive review levels?

**Data Sources**: 
- `product_database` → competitors.csv

**Analysis Steps**:
1. Get Top 20 products by sales
2. Calculate average and median review counts
3. Estimate time to reach competitive review count at typical review velocity

**Output**: Review barrier assessment + timeline estimate

---

#### Q7: Niche Keyword Opportunities for Ads
**Question**: Are there niche long-tail keywords with low PPC bids that could serve as cost-effective ad entry points?

**Data Sources**: 
- `keywords_by_keyword` → keywords_market.csv

**Analysis Steps**:
1. Filter keywords with ppc_bid_exact < category median
2. Sort by search volume descending
3. Calculate opportunity score = volume / bid

**Output**: Low-cost keyword list for ad targeting

---

#### Q8: Market Pain-Points & Demand Gaps
**Question**: Are there product quality gaps (low ratings, high sales) that indicate unmet customer needs worth targeting through ads?

**Data Sources**: 
- `product_database` → competitors.csv

**Analysis Steps**:
1. Filter products with high sales + rating < 4.2
2. Identify categories with consistent quality complaints
3. Assess ad opportunity for differentiated products

**Output**: Pain-point driven ad opportunity list

---

## Type 5: Trend & Seasonality

### Sub-Question Templates

#### Q1: 12-Month Search Curve
**Question**: What does the search volume curve for keyword '{keyword}' look like over the past 12 months?

**Data Sources**: 
- `historical_search_volume` → keyword_trends.csv

**Output**: 12-month trend chart + peak/trough annotations

---

#### Q2: Seasonal Brand Shift
**Question**: During peak search periods, how does the top brand share distribution compare to off-season?

**Data Sources**: 
- `share_of_voice` (multiple time points)

**Output**: Peak vs off-season brand share comparison

---

#### Q3: Peak vs Trough Sales Comparison
**Question**: How much did sales drop for top-ranking ASINs during peak season compared to off-season?

**Data Sources**: 
- `sales_estimates` → asin_sales.csv

**Output**: Peak vs trough sales comparison table

---

#### Q4: Seasonality Coefficient
**Question**: What's the seasonality coefficient for this category? Is it suitable for year-round operation or seasonal stocking?

**Data Sources**: 
- `historical_search_volume` → keyword_trends.csv

**Output**: CV value + operational recommendation

---

#### Q5: Counter-Seasonal Keywords
**Question**: Are there counter-seasonal related keywords that could balance year-round sales?

**Data Sources**: 
- `keywords_by_keyword` + `historical_search_volume`

**Output**: Counter-seasonal keyword list

---

#### Q6: Competitive Landscape Shifts
**Question**: Has the brand concentration changed over the past year? Are new brands gaining share?

**Data Sources**: 
- `share_of_voice` → market_concentration.csv

**Analysis Steps**:
1. Get current brand share distribution
2. Identify brands with low share but high growth signals (new entrants)
3. Assess whether market is consolidating or fragmenting

**Output**: Brand share trend analysis + new entrant assessment

---

#### Q7: Margin Stability Across Seasons
**Question**: How does pricing fluctuate between peak and off-season? Does margin remain viable year-round?

**Data Sources**: 
- `product_database` → competitors.csv
- `historical_search_volume` → keyword_trends.csv

**Analysis Steps**:
1. Identify peak and off-season periods from search volume data
2. Compare average prices during peak vs off-season (if historical price data available)
3. Estimate margin impact of seasonal price changes

**Output**: Seasonal pricing analysis + margin stability assessment

---

#### Q8: Pain-Points & Quality Gaps
**Question**: Do top products show quality issues (low ratings) that a new entrant could address with better product design?

**Data Sources**: 
- `product_database` → competitors.csv

**Analysis Steps**:
1. Filter top 20 products by sales
2. Identify those with rating < 4.3
3. Calculate the rating gap between category leaders and laggards

**Output**: Quality gap analysis + differentiation opportunity

---

## Sub-Question Generation Rules

1. **Quantity Control**: Generate exactly 8 sub-questions (one per standard dimension defined in SKILL.md Step 4)
2. **Fixed Dimension Order**: Follow the dimension order defined in SKILL.md Step 4 (1=market_size_demand, 2=competitive_landscape, ..., 8=pain_points). Do NOT reorder by importance.
3. **Data Feasibility**: Ensure each question can be answered with available CSV data from Step 2
4. **Avoid Overlap**: Sub-questions should not have redundant coverage
5. **Actionability**: Each answer should lead to specific action recommendations
6. **Product-Level Conclusions**: Where the analysis naturally points to specific products in `competitors.csv` (e.g., weak incumbents, quality gaps, niche leaders), the sub-question should be phrased to guide the Agent toward identifying those ASINs. This is NOT forced for every dimension — only where product-level mapping is natural (typically: competitive_landscape, entry_barrier, niche_opportunities, pain_points).

