# Jungle Scout SDK Pitfalls

Verified runtime behaviors that differ from REST API docs. **Ignoring these causes script failures.**

---

## 0. CRITICAL: Use `ClientSync` with Context Manager — NOT `Client`

The `junglescout-client` package exports both `Client` (async) and `ClientSync` (sync). **You MUST use `ClientSync` as a context manager** (`with` statement). Using `Client` directly or instantiating `ClientSync` without `with` will result in **400 Bad Request: "Authorization header is not present or in a valid format"** because the auth headers are only set up during context manager entry.

### 0a. Import Path — MUST use top-level import

**Always import from the top-level package**, NOT from submodules. The submodule import path may fail to initialize auth headers correctly.

```python
# ❌ WRONG — submodule import, may cause silent auth failure → 400
from junglescout.client_sync import ClientSync

# ✅ CORRECT — top-level import
from junglescout import ClientSync
from junglescout.models.parameters import Marketplace
```

### 0b. Credentials — MUST use Gateway dispatch call

The sandbox environment does NOT have `JS_API_KEY` or `JS_KEY_NAME` pre-set as environment variables. Using `os.environ.get()` will return `None`, causing silent auth failure → 400 "Authorization header is not present".

**Always import from the top-level package**, NOT from submodules.

```

### 0b. Authentication — Handled by Tool

Authentication is handled automatically by the `jungle_scout_collect` tool.
No credentials, Gateway calls, or SDK client setup needed in sandbox scripts.

---

## 0d. CRITICAL: Correct SDK Method Names

The SDK method names do NOT match the REST API endpoint names. Using REST API names causes `AttributeError`.

| REST API Endpoint | ❌ Wrong SDK Call | ✅ Correct SDK Call |
|---|---|---|
| `keywords_by_keyword_query` | `client.keywords_by_keyword_query()` | `client.keywords_by_keyword()` |
| `product_database_query` | `client.product_database_query()` | `client.product_database()` |
| `keywords_by_asin_query` | `client.keywords_by_asin_query()` | `client.keywords_by_asin()` |
| `sales_estimates_query` | `client.sales_estimates_query()` | `client.sales_estimates()` |
| `historical_search_volume` | `client.historical_search_volume()` | `client.historical_search_volume()` ✅ (same) |
| `share_of_voice` | `client.share_of_voice()` | `client.share_of_voice()` ✅ (same) |

**Also**: there are NO sub-namespaces. Do NOT use `client.keywords.xxx()` or `client.products.xxx()` — all methods are directly on the client object.

```python
# ❌ WRONG — no sub-namespaces exist
client.keywords.keywords_by_keyword_query(...)
client.products.product_database_query(...)

# ✅ CORRECT — methods are directly on client
client.keywords_by_keyword(...)
client.product_database(...)
```

---

## 0e. CRITICAL: Correct SDK Parameter Names

Several SDK methods use different parameter names than you might expect. Using wrong parameter names causes `TypeError: got an unexpected keyword argument`.

| Method | ❌ Wrong Parameter | ✅ Correct Parameter | Notes |
|---|---|---|---|
| `product_database()` | `keywords="yoga mat"` | `include_keywords=["yoga mat"]` | Must be a **list**, not a string |
| `product_database()` | `category="Home"` | `categories=["Home"]` | Must be a **list**, not a string |
| `keywords_by_keyword()` | `keyword="yoga mat"` | `search_terms="yoga mat"` | String, not list |
| `keywords_by_asin()` | `asin_list=["B0XX"]` | `asin="B0XX"` | Single ASIN string |

```python
# ❌ WRONG — causes TypeError
client.product_database(keywords="yoga mat")
client.product_database(keyword="yoga mat")

# ✅ CORRECT — include_keywords takes a list
client.product_database(include_keywords=["yoga mat"], categories=["Home & Kitchen"])
```

---

## 1. ASIN Format: Marketplace Prefix

`product.id` returns `"us/B0F1M6LB5R"`, NOT a bare ASIN.

**Strip before using in `sales_estimates()`**:
```python
asin = product.id.split('/')[-1]  # "us/B0F1M6LB5R" → "B0F1M6LB5R"
```

In data collection: store raw `product.id` in CSV. In analysis script: strip prefix.
```python
df['asin'] = df['asin'].apply(lambda x: x.split('/')[-1] if isinstance(x, str) else x)
```

---

## 2. `product_url` Does NOT Exist

The SDK has no `product_url` field. Construct it:
```python
prod_url = f"https://www.amazon.com/dp/{asin}"
```

`image_url` **does** exist: `product.attributes.image_url`

---

## 3. Use `model_dump()` + `data.get()` Pattern

SDK responses are Pydantic models. **Never use `.to_dict()`**.
```python
data = product.attributes.model_dump()
title = data.get('title', '')
```

---

## 4. Actual SDK Attribute Names

- `title` (not `product_name`)
- `approximate_30_day_units_sold` (not `monthly_sales`)
- `approximate_30_day_revenue`
- `listing_quality_score` (0-10 scale)
- No `product_tier` field

See `api_reference.md` for the complete verified field list.

---

## 5. Marketplace Must Be Enum, NOT String

`historical_search_volume()` accepts a `marketplace` parameter. It **must** be `Marketplace.US` (the enum), NOT the string `'us'`. Using a string causes `"Marketplace cannot be resolved"` error.

```python
# ❌ WRONG — causes "Marketplace cannot be resolved"
client.historical_search_volume(keyword='yoga mat', ..., marketplace='us')

# ✅ CORRECT
from junglescout.models.parameters import Marketplace
client.historical_search_volume(keyword='yoga mat', ..., marketplace=Marketplace.US)
```

The `ClientSync` constructor also requires `Marketplace.US` (already correct in the template).

---

## 6. `sales_estimates()` Requires Date Parameters

`start_date` and `end_date` are mandatory. Not all ASINs have data.
```python
from datetime import datetime, timedelta
end_date = datetime.now().strftime('%Y-%m-%d')
start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
try:
    response = client.sales_estimates(asin=asin, start_date=start_date, end_date=end_date)
except Exception as e:
    print(f"Skipping {asin}: {e}")
```

---

## 7. Pandas int64/float64 Not JSON Serializable

When building `data_points` from CSV data, pandas returns `int64`/`float64` types that `json.dumps` cannot serialize. Always cast to native Python types:

```python
# ❌ WRONG — causes TypeError: Object of type int64 is not JSON serializable
data_points=[{"label": "Search Volume", "value": row['monthly_search_volume_exact'], ...}]

# ✅ CORRECT — cast to int/float
data_points=[{"label": "Search Volume", "value": int(row['monthly_search_volume_exact']), ...}]
```

