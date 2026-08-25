# Merge Tiers Script — Reference Implementation

> This is the reference implementation for Step 6d (merge all tiers and save CSV).
> The Agent should `write_file` this script to `/round-{N}/data/merge_tiers.py`, then `bash_command` to execute.

```python
import sys, os, csv, json, re
sys.path.insert(0, '/jungle-scout-deep-dive-analyzer/scripts')
from pipeline import save_recommendations_csv

base_dir = '/round-{N}'

# --- Tier 1: analysis-driven ---
with open(f'{base_dir}/reports/product_recommendations_ranked.json') as f:
    tier1_products = json.load(f)
for p in tier1_products:
    p['recommendation_source'] = 'analysis-driven'
tier1_asins = {p['asin'] for p in tier1_products}

# --- Tier 2: data-filtered ---
with open(f'{base_dir}/reports/_tier2_products.json') as f:
    tier2_products = json.load(f)
tier2_asins = {p['asin'] for p in tier2_products}

existing_asins = tier1_asins | tier2_asins

# --- Tier 3: read ALL shopping CSV files from info_search ---
shopping_dir = f'{base_dir}/info_search/shopping_search'
tier3_products = []
ref_id_map = {}  # asin -> reference_id (for backfilling Tier 1/2)

if os.path.isdir(shopping_dir):
    for fname in os.listdir(shopping_dir):
        if not fname.endswith('.csv'):
            continue
        fpath = os.path.join(shopping_dir, fname)
        with open(fpath, encoding='utf-8-sig') as f:
            for row in csv.DictReader(f):
                url = row.get('Product URL') or ''
                m = re.search(r'/dp/([A-Z0-9]{10})', url)
                asin = m.group(1) if m else ''
                if not asin:
                    continue
                ref_id = row.get('Reference id') or ''
                if ref_id:
                    ref_id_map[asin] = ref_id

                if asin in existing_asins:
                    continue  # dedup, but ref_id already captured above
                existing_asins.add(asin)

                # Parse rating: "4.2 (573 reviews)" -> rating=4.2, reviews=573
                rating_str = row.get('Rating') or ''
                rating = 0.0
                reviews = 0
                rm = re.match(r'([\d.]+)', rating_str)
                if rm:
                    rating = float(rm.group(1))
                rvm = re.search(r'\((\d+)', rating_str)
                if rvm:
                    reviews = int(rvm.group(1))

                # Parse price: "$29.99" or "N/A"
                price_str = row.get('Price') or ''
                price = 0.0
                pm = re.search(r'[\d.]+', price_str)
                if pm:
                    price = float(pm.group(0))

                # Parse sales: "1916" or "N/A"
                sales_str = row.get('Last Month Sales') or '0'
                try:
                    sales = int(float(sales_str))
                except (ValueError, TypeError):
                    sales = 0

                tier3_products.append({
                    'asin': asin,
                    'title': row.get('Product Name') or '',
                    'price': price,
                    'rating': rating,
                    'reviews': reviews,
                    'sales_cnt_30d': sales,
                    'prodUrl': url,
                    'imageUrl': row.get('Image URL') or '',
                    'reference_id': ref_id,
                    'recommendation_source': 'search',
                    'recommendation_reason': fname.replace('shopping_', '').replace('.csv', '').replace('_', ' '),
                })

# Backfill reference_ids for Tier 1/2 products
for p in tier1_products + tier2_products:
    if p['asin'] in ref_id_map and not p.get('reference_id'):
        p['reference_id'] = ref_id_map[p['asin']]

all_products = tier1_products + tier2_products + tier3_products
save_recommendations_csv(all_products, base_dir=base_dir)
print(f"Tier 1: {len(tier1_products)}, Tier 2: {len(tier2_products)}, Tier 3: {len(tier3_products)}")
print(f"Total: {len(all_products)} products saved to final_recommendations.csv")
```

## Key behaviors

- Reads ALL CSV files from `shopping_search/` directory — do NOT manually construct a small product list
- Backfills `reference_id` from Tier 3 search results to Tier 1/2 products (they need it for report tags)
- Deduplicates by ASIN across all tiers
- Parses rating/reviews/price/sales from info_search CSV format
- Expected output: 40–80+ products total

