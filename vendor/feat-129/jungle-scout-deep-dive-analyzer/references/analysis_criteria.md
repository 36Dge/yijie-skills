# Analysis Criteria

Qualitative thresholds for market analysis dimensions. Used in the narrative report and sub-question analysis.

---

## Market/Customer

| Metric | Large | Medium | Small |
|--------|-------|--------|-------|
| Search Volume | >10K/mo | 5K-10K | <5K |
| Top Seller Revenue | >$100K/mo | $50K-$100K | <$50K |

- Pain points clear and fixable? → Strong demand
- Unmet needs in reviews? → Differentiation opportunity

**Verdict**: Market Size + Customer Demand (Strong/Moderate/Weak) + Market Health (Healthy/Moderate/Risky)

---

## Competition

| Metric | Low | Medium | High |
|--------|-----|--------|------|
| Effective Competitors | <50 | 50-200 | >200 |
| Top 5 Market Share | <40% | 40-60% | >60% |
| Top 10 Avg Reviews | <500 | 500-1000 | >1000 |
| PPC CPC | <$1 | $1-$2 | >$2 |

- Amazon in Top 10 → Higher barrier
- Low LQS (<7) in Top 10 → Listing optimization opportunity

**Verdict**: Competition Level + Entry Barriers + Top 3 Differentiation Opportunities

---

## Trends

| YoY Change | Classification |
|------------|----------------|
| >10% growth | Growing |
| -5% to +10% | Stable |
| <-5% | Declining |

| Seasonal Variance (CV) | Assessment |
|------------------------|------------|
| CV ≤ 0.5 | Non-seasonal (year-round demand) |
| CV > 0.5 | Seasonal |
| < 12 data points | Insufficient data |

> CV = standard deviation / mean of weekly search volumes over 12+ months.
> Matches the threshold in `analyze_indicators.py` (`CV_THRESHOLD = 0.5`).

**Verdict**: Growth Trend + Seasonality + Market Stage (Introduction/Growth/Maturity/Decline)

---

## Internal Capability

| DDP % of Price | Assessment |
|----------------|------------|
| <30% | Good margins |
| 30-40% | Acceptable |
| >40% | Risky |

| Risk | Low | Medium | High |
|------|-----|--------|------|
| Inventory | MOQ <500 | 500-2000 | >2000 |
| Capital | <$5K | $5K-$15K | >$15K |

**Verdict**: Sourcing Feasibility + Capital Requirement + Risk Level

