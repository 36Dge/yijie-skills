# Amazon Market Intel — Module Selection Guide

This skill contains 6 APIs and 42 sub-modules. Pick the right API first, then choose a specific module.

---

## Step 1: Choose an API

> Key decision factor: What data does the user already have (ASINs? keywords? categories?) and what result do they want?

### ① Historical Search Volume API
- Input: 1–5 keywords + date range (max 366 days)
- Output: Weekly aggregated search volume time series
- Use when: User wants to see how keyword search volume changes over time — seasonal curves, YoY growth, trend inflection points, ad timing windows, inventory planning
- Do NOT use when: User wants to expand/discover new keywords (→ ④), or see which keywords an ASIN ranks for (→ ②)

### ② Keywords by ASIN API
- Input: 1–10 ASINs
- Output: Keywords each ASIN ranks for (with rank position, search volume, PPC bid)
- Use when: User already has specific ASINs and wants to know "what keywords does this product rank on" — reverse keyword research, competitive keyword gaps, Listing SEO, share of search tracking
- Do NOT use when: User has no ASINs, only keywords to expand (→ ④), or wants historical search volume trends (→ ①)
- Key difference from ④: ② = "from ASIN → find keywords", ④ = "from keyword → find more keywords"

### ③ Sales Estimates API
- Input: 1–10 ASINs + date range (max 365 days)
- Output: Daily granularity sales, price, and revenue estimates
- Use when: User wants to quantify specific ASIN sales performance — competitor sales tracking, promotion impact, stock-out detection, revenue modeling, price elasticity
- Do NOT use when: User wants keyword-level data (→ ①②④), or wants to bulk-filter products (→ ⑤)

### ④ Keywords by Keyword API
- Input: 1–10 seed keywords
- Output: Related/expanded keyword list (with search volume, PPC bid, category, relevancy score)
- Use when: User has seed keywords and wants to discover more related terms — keyword expansion, demand validation, PPC budget planning, category mapping, cross-market comparison, trend detection
- Do NOT use when: User has ASINs and wants to see their keyword rankings (→ ②), or wants historical search volume time series (→ ①)
- Key difference from ②: ④ = "from keyword → find more keywords", ② = "from ASIN → find keywords"

### ⑤ Product Database API
- Input: Category, keywords, price range, review count, seller type, and other filters
- Output: Product list matching filters (with estimated sales, revenue, BSR, LQS, brand, seller type)
- Use when: User wants to bulk-filter/discover products — product research, competitive landscape, category market sizing, brand intelligence, new product monitoring, listing quality audit
- Do NOT use when: User already has specific ASINs for keyword or sales analysis (→ ②③), or wants keyword analysis (→ ①④)

### ⑥ Share of Voice API
- Input: 1+ keywords
- Output: Brand share of voice per keyword (organic/sponsored/combined SOV) + Top 3 ASIN click & conversion data
- Use when: User wants to know "who dominates the search results page" — brand market share, ad incremental lift, competitive threat monitoring, conversion performance
- Do NOT use when: User wants keyword search volume trends (→ ①), keyword expansion (→ ④), or specific ASIN sales data (→ ③)

---

## Step 2: Choose a Sub-Module

### Historical Search Volume API (6 modules)

| User Intent | Module | Example & Impact | Reference |
|-------------|--------|-------------------|-----------|
| Seasonal search volume curve, peak/trough weeks, volatility | Seasonal Demand Profiling | Map ramp/peak/decline to align inventory & ad budgets to actual demand timing | `read_file('reference/historical_search_volume/seasonal-demand-profiling.md')` |
| YoY search volume comparison, category growth/decline, CAGR | Year-over-Year Growth | Calculate YoY growth rates for long-term strategic planning | `read_file('reference/historical_search_volume/year-over-year-growth.md')` |
| PPC bid timing, ad budget allocation, spend increase/decrease windows | Ad Campaign Timing | Concentrate ad spend during rising search weeks to improve ROI | `read_file('reference/historical_search_volume/ad-campaign-timing.md')` |
| Compare category vs brand keyword share, monitor competitor dynamics | Competitive Benchmarking | Quantify brand awareness shifts and competitive dynamics | `read_file('reference/historical_search_volume/competitive-benchmarking.md')` |
| Demand inflection points, lead time calculation, inventory coverage | Inventory & Demand Forecasting | Reduce stockout risk during peaks and overstock during troughs | `read_file('reference/historical_search_volume/inventory-demand-forecasting.md')` |
| Best launch window, demand stability, multi-category launch timing | Product Launch Timing | Identify the 4–6 weeks before peak demand as the ideal launch window | `read_file('reference/historical_search_volume/product-launch-timing.md')` |

### Keywords by ASIN API (8 modules)

| User Intent | Module | Example & Impact | Reference |
|-------------|--------|-------------------|-----------|
| Full keyword profile of a competitor/own ASIN, discover traffic-driving keywords | Reverse ASIN Research | Uncover the keyword strategy behind any product's success | `read_file('reference/keywords_by_asin/reverse-asin-research.md')` |
| Find keywords competitors have that you don't, quantify coverage gap | Keyword Gap Analysis | Drive targeted listing optimization and PPC strategy | `read_file('reference/keywords_by_asin/keyword-gap-analysis.md')` |
| Optimize listing title/bullet keywords, find low-competition opportunities | Listing SEO Optimization | Ensure listing copy is optimized for the highest-traffic terms | `read_file('reference/keywords_by_asin/listing-seo-optimization.md')` |
| Pre-entry keyword research for a new category, build category keyword map | Market Entry Research | Accelerate market entry research from weeks to hours | `read_file('reference/keywords_by_asin/market-entry-research.md')` |
| Map full keyword universe across a catalog, identify cannibalization | Multi-ASIN Portfolio | Maximize organic reach by eliminating blind spots | `read_file('reference/keywords_by_asin/multi-asin-portfolio.md')` |
| Harvest PPC keywords from competitor ASINs, prioritize by tier | PPC Keyword Harvesting | Build PPC campaigns on proven data, improving ROAS from day one | `read_file('reference/keywords_by_asin/ppc-keyword-harvesting.md')` |
| Rank snapshot baseline, monitor rank changes, quantify search share | Share of Search Tracking | Continuous visibility into organic search health | `read_file('reference/keywords_by_asin/share-of-search-tracking.md')` |
| Identify rising/declining keywords, detect seasonal peaks | Trend & Seasonality Detection | Enable proactive inventory and ad spend decisions | `read_file('reference/keywords_by_asin/trend-seasonality-asin.md')` |

### Sales Estimates API (5 modules)

| User Intent | Module | Example & Impact | Reference |
|-------------|--------|-------------------|-----------|
| Track competitor daily sales, detect promotions/stock-outs, market share | Competitive Sales Tracking | Continuous intelligence for real-time strategic responses | `read_file('reference/sales_estimates/competitive-sales-tracking.md')` |
| Quantify promotion sales lift, compare pre/post baseline, Prime Day tracking | Deal & Promotion Impact | Measure exact sales lift from Lightning Deals, coupons, or Prime Day | `read_file('reference/sales_estimates/deal-and-promotion-impact.md')` |
| Price elasticity curve, discount pattern detection, optimal price point | Pricing Strategy & Elasticity | Plot daily price vs. daily sales for evidence-based pricing | `read_file('reference/sales_estimates/pricing-strategy-and-elasticity.md')` |
| Estimate ASIN/brand revenue, build revenue timeline, revenue share comparison | Revenue & Financial Modeling | Revenue intelligence for investment and financial analysis | `read_file('reference/sales_estimates/revenue-and-financial-modeling.md')` |
| Monitor competitor stock-outs, detect sudden sales drops, assess demand gap | Stock-Out Detection | Rapid response to capture demand when competitors run out | `read_file('reference/sales_estimates/stock-out-detection.md')` |

### Keywords by Keyword API (8 modules)

| User Intent | Module | Example & Impact | Reference |
|-------------|--------|-------------------|-----------|
| Expand seed keywords into full keyword universe, discover long-tail variants | Keyword Expansion | Discover 100+ related terms, reveal untapped demand pockets | `read_file('reference/keywords_by_keyword/keyword-expansion.md')` |
| Compare search demand across product concepts, validate product ideas | Search Volume Benchmark | Prevent investment in products with insufficient demand | `read_file('reference/keywords_by_keyword/search-volume-benchmark.md')` |
| Estimate PPC budget, find high-traffic low-CPC keywords, bid strategy | PPC Bid Strategy | Data-driven ad budget planning using bid estimates | `read_file('reference/keywords_by_keyword/ppc-bid-strategy.md')` |
| Understand category ownership of search traffic, cross-category opportunities | Category & Niche Mapping | Reveal the true competitive landscape beyond Amazon's taxonomy | `read_file('reference/keywords_by_keyword/category-niche-mapping.md')` |
| Keyword priority for detail pages, A+ content planning, easy-rank opportunities | Content & SEO Strategy | Ensure every word of listing copy is backed by search demand data | `read_file('reference/keywords_by_keyword/content-seo-strategy.md')` |
| Cross-market demand comparison, international expansion priority | Cross-Market Comparison | De-risk international expansion with demand-level comparison | `read_file('reference/keywords_by_keyword/cross-market-comparison.md')` |
| Build SP/SB/SD ad keyword portfolio, tiered match types, brand ad opportunities | Ad Keyword Portfolio | Create structured, scalable PPC architectures | `read_file('reference/keywords_by_keyword/ad-keyword-portfolio.md')` |
| Discover emerging keywords, identify declining trends, short-term signals | Trend Detection | Leading indicators of demand shifts (>20% quarterly growth) | `read_file('reference/keywords_by_keyword/trend-detection.md')` |

### Product Database API (9 modules)

| User Intent | Module | Example & Impact | Reference |
|-------------|--------|-------------------|-----------|
| Filter by category/revenue/reviews to find blue-ocean niches | Market Opportunity Discovery | Reduce product research from weeks to hours | `read_file('reference/product_database/market-opportunity-discovery.md')` |
| Analyze price/review/seller-type distribution, competitive positioning | Competitive Landscape Analysis | Competitive positioning grounded in real market data | `read_file('reference/product_database/competitive-landscape-analysis.md')` |
| Enrich ASIN data with sales/revenue/BSR, CRM data enrichment | ASIN Deep Dive & Enrichment | Automate per-ASIN data enrichment at scale | `read_file('reference/product_database/asin-deep-dive-enrichment.md')` |
| Filter by listing date for recent launches, monitor competitor new products | New Product Launch Monitoring | Early warning of competitive threats | `read_file('reference/product_database/new-product-launch-monitoring.md')` |
| Segment by price tier to compare sales/BSR, find optimal price band | Pricing Strategy & Elasticity | Data-driven pricing that maximizes revenue | `read_file('reference/product_database/pricing-strategy-elasticity.md')` |
| Track brand portfolio size/avg price/total revenue, seller intelligence | Brand & Seller Intelligence | Critical for brand protection and distribution strategy | `read_file('reference/product_database/brand-seller-intelligence.md')` |
| Sum category monthly revenue to extrapolate annual market size | Category Market Sizing | Support investment theses and category entry decisions | `read_file('reference/product_database/category-market-sizing.md')` |
| Filter lightweight small-dimension products with healthy sales, private label | Product Sourcing & Private Label | Streamline the sourcing pipeline | `read_file('reference/product_database/product-sourcing-private-label.md')` |
| Rank ASIN catalog by LQS, benchmark against top sellers, prioritize optimization | Listing Quality Auditing | Systematically improve organic visibility and conversion rates | `read_file('reference/product_database/listing-quality-auditing.md')` |

### Share of Voice API (6 modules)

| User Intent | Module | Example & Impact | Reference |
|-------------|--------|-------------------|-----------|
| Quantify brand SOV across core keywords, compare competitor brands, split organic vs paid | Brand Market Share | The single most important KPI for competitive positioning | `read_file('reference/share_of_voice/brand-market-share.md')` |
| Measure ad incremental visibility, identify keywords to increase/reduce ad spend | Advertising Effectiveness | Optimize spend by identifying where paid placements add real value | `read_file('reference/share_of_voice/advertising-effectiveness.md')` |
| Monitor competitor SOV changes, detect ad offensive escalation, identify new entrants | Competitive Threat Monitoring | Early warning of competitive threats via SOV spikes | `read_file('reference/share_of_voice/competitive-threat-monitoring.md')` |
| Analyze keyword brand concentration, identify fragmented market opportunities | Keyword Competitive Intel | Inform keyword prioritization based on competitive structure | `read_file('reference/share_of_voice/keyword-competitive-intel.md')` |
| Analyze Top 3 ASIN clicks & conversions per keyword, identify true traffic winners | Conversion Performance | Reveal the products that actually win on each keyword | `read_file('reference/share_of_voice/conversion-performance.md')` |
| Compare basic vs weighted SOV, assess page position quality, Amazon's Choice badge impact | Weighted Positioning Analysis | Account for the quality of page positions, not just quantity | `read_file('reference/share_of_voice/weighted-positioning-analysis.md')` |

> If the user's intent spans multiple dimensions, read multiple reference files in sequence.

