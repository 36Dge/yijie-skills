# Jungle Scout API Reference

Field definitions and search parameters.

---

## Authentication

Authentication is handled automatically by the `jungle_scout_collect` tool.
No credentials or API keys are needed in sandbox scripts.

> See `sdk_pitfalls.md` § 0b-1 for the full Gateway request structure details.

---

## 1. Product Database

**Use for**: Finding products by category, keywords, price, sales volume.

### Filters

| Parameter | Type | Example |
|-----------|------|---------|
| `include_keywords` | list[str] | `['yoga mat']` |
| `exclude_keywords` | list[str] | `['used']` |
| `categories` | list[str] | `['Sports & Outdoors']` |
| `page_size` | int (max 50) | `50` |

### ProductFilterOptions

| Filter | Type |
|--------|------|
| `min_price` / `max_price` | float |
| `min_sales` / `max_sales` | int |
| `min_reviews` / `max_reviews` | int |
| `min_rating` / `max_rating` | float (1.0-5.0) |
| `min_rank` / `max_rank` | int |
| `min_listing_quality_score` / `max_listing_quality_score` | float (1-10) |

### SDK Response Fields (ProductDatabaseAttributes)

| Attribute | Type | Notes |
|-----------|------|-------|
| `title` | str | NOT `product_name` |
| `brand` | str | |
| `price` | float | USD |
| `approximate_30_day_units_sold` | int | NOT `monthly_sales` |
| `approximate_30_day_revenue` | float | |
| `reviews` | int | |
| `rating` | float | 1.0-5.0 |
| `listing_quality_score` | float | 0-10 |
| `seller_type` | str | AMZ/FBA/FBM |
| `image_url` | str | Exists |
| `product_rank` | int | BSR |
| `category` | str | |
| `date_first_available` | str | |
| `number_of_sellers` | int | |
| `fee_breakdown` | object | FBA fees |

`product_url` does NOT exist. `product.id` returns `"us/B0F1M6LB5R"` — see `sdk_pitfalls.md`.

---

## 2. Keywords by Keyword

**Use for**: Keyword research, search volume, PPC bids.

| Parameter | Required | Type |
|-----------|----------|------|
| `search_terms` | Yes | str |
| `page_size` | No | int (max 50) |

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | str | Keyword phrase |
| `monthly_search_volume_exact` | int | Exact match volume |
| `monthly_search_volume_broad` | int | Broad match volume |
| `ppc_bid_exact` | float | PPC bid USD |
| `ease_of_ranking_score` | float | 1-10, 10=easiest |
| `organic_product_count` | int | Competing products |

---

## 3. Historical Search Volume

**Use for**: Keyword search volume trends over time, seasonality analysis.

| Parameter | Required | Type |
|-----------|----------|------|
| `keyword` | Yes | str |
| `start_date` | Yes | str YYYY-MM-DD |
| `end_date` | Yes | str YYYY-MM-DD |
| `marketplace` | Yes | `Marketplace` enum (e.g. `Marketplace.US`) — NOT a string |

Response: `point.attributes.model_dump()` with `date`, `estimated_exact_search_volume`

Returns weekly (7-day) granularity data points.

⚠️ `marketplace` must be `Marketplace.US` (enum), not `'us'` (string). See `sdk_pitfalls.md`.

---

## 4. Sales Estimates

**Use for**: Historical sales trends, daily granularity.

| Parameter | Required | Type |
|-----------|----------|------|
| `asin` | Yes | str (bare, no prefix) |
| `start_date` | Yes | str YYYY-MM-DD |
| `end_date` | Yes | str YYYY-MM-DD |

Response: `estimate.attributes.data[]` with `date`, `estimated_units_sold`, `last_known_price`

Not all ASINs have data — may return 422.

---

## 5. Share of Voice

**Use for**: Brand dominance, market concentration.

| Parameter | Required | Type |
|-----------|----------|------|
| `keyword` | Yes | str |

Response: `response.data.attributes.brands[]` with `brand`, `combined_weighted_sov`, `organic_products`, `sponsored_products`

---

## Errors

| Code | Action |
|------|--------|
| 400 | Check filters |
| 401 | Check credentials |
| 422 | Try other ASIN/params |
| 429 | Backoff + retry |

Rate: 10 req/s, burst 20, daily 10K.

## Marketplaces

`us`, `uk`, `ca`, `de`, `fr`, `in`, `it`, `es`, `mx`, `jp`

