"""
Data Collection Module for Product Selection Deep Research.

Step 2: Convert raw JSON data from jungle_scout_collect tool into CSV files.
The tool calls Jungle Scout APIs from the main process and saves raw JSON to files;
this script only handles JSON → CSV transformation inside the sandbox.

Usage:
  import sys
  sys.path.insert(0, '/jungle-scout-deep-dive-analyzer/scripts')
  from collect_js_data import convert_all
  convert_all(data_dir="/round-{N}/data", keyword="portable blender")
"""
import csv
import json
import os
from typing import Any, Dict, List, Optional


def _write_csv(rows: List[Dict], columns: List[str], filepath: str) -> int:
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction='ignore')
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    return len(rows)


def save_keywords_csv(data, output_dir):
    columns = ['keyword', 'monthly_search_volume_exact', 'monthly_search_volume_broad',
                'ppc_bid_exact', 'ease_of_ranking_score', 'organic_product_count']
    rows = []
    for item in (data or []):
        attrs = item.get('attributes', item)
        rows.append({
            'keyword': attrs.get('name') or attrs.get('keyword'),
            'monthly_search_volume_exact': attrs.get('monthly_search_volume_exact'),
            'monthly_search_volume_broad': attrs.get('monthly_search_volume_broad'),
            'ppc_bid_exact': attrs.get('ppc_bid_exact'),
            'ease_of_ranking_score': attrs.get('ease_of_ranking_score'),
            'organic_product_count': attrs.get('organic_product_count'),
        })
    return _write_csv(rows, columns, f'{output_dir}/keywords_market.csv')


def save_historical_csv(data, keyword, output_dir):
    columns = ['keyword', 'date', 'estimated_exact_search_volume']
    rows = []
    for item in (data or []):
        attrs = item.get('attributes', item)
        rows.append({
            'keyword': keyword,
            'date': attrs.get('estimate_start_date') or attrs.get('date'),
            'estimated_exact_search_volume': attrs.get('estimated_exact_search_volume'),
        })
    return _write_csv(rows, columns, f'{output_dir}/keyword_trends.csv')


def save_product_database_csv(data, output_dir):
    columns = ['asin', 'title', 'brand', 'price', 'sales_cnt_30d', 'revenue_30d',
               'reviews', 'rating', 'lqs', 'seller_type', 'weight', 'dimensions',
               'category', 'imageUrl', 'prodUrl']
    rows = []
    for item in (data or []):
        attrs = item.get('attributes', item)
        raw_id = item.get('id', '')
        bare_asin = raw_id.split('/')[-1] if raw_id else ''
        weight_val = attrs.get('weight_value')
        weight_unit = attrs.get('weight_unit', '')
        weight = f"{weight_val} {weight_unit}".strip() if weight_val is not None else None
        dims = []
        for d in ('length_value', 'width_value', 'height_value'):
            v = attrs.get(d)
            if v is not None:
                dims.append(str(v))
        dims_unit = attrs.get('dimensions_unit', '')
        dimensions = f"{' x '.join(dims)} {dims_unit}".strip() if dims else None
        rows.append({
            'asin': bare_asin,
            'title': attrs.get('title') or attrs.get('product_name'),
            'brand': attrs.get('brand'),
            'price': attrs.get('price'),
            'sales_cnt_30d': attrs.get('approximate_30_day_units_sold'),
            'revenue_30d': attrs.get('approximate_30_day_revenue'),
            'reviews': attrs.get('reviews'),
            'rating': attrs.get('rating'),
            'lqs': attrs.get('listing_quality_score'),
            'seller_type': attrs.get('seller_type'),
            'weight': weight,
            'dimensions': dimensions,
            'category': attrs.get('category'),
            'imageUrl': attrs.get('image_url'),
            'prodUrl': f'https://www.amazon.com/dp/{bare_asin}' if bare_asin else None,
        })
    return _write_csv(rows, columns, f'{output_dir}/competitors.csv')


def save_share_of_voice_csv(data, output_dir):
    columns = ['brand', 'combined_weighted_sov', 'organic_products',
               'sponsored_products', 'organic_click_share', 'sponsored_click_share']
    rows = []
    attrs = data.get('attributes', data) if isinstance(data, dict) else {}
    for brand in attrs.get('brands', []):
        rows.append({
            'brand': brand.get('brand'),
            'combined_weighted_sov': brand.get('combined_weighted_sov'),
            'organic_products': brand.get('organic_products'),
            'sponsored_products': brand.get('sponsored_products'),
            'organic_click_share': brand.get('organic_click_share'),
            'sponsored_click_share': brand.get('sponsored_click_share'),
        })
    return _write_csv(rows, columns, f'{output_dir}/market_concentration.csv')


def save_keywords_by_asin_csv(data, output_dir):
    columns = ['keyword', 'monthly_search_volume_exact', 'monthly_search_volume_broad',
               'ppc_bid_exact', 'ease_of_ranking_score', 'organic_product_count',
               'organic_rank', 'sponsored_rank', 'overall_rank']
    rows = []
    for item in (data or []):
        attrs = item.get('attributes', item)
        rows.append({
            'keyword': attrs.get('name'),
            'monthly_search_volume_exact': attrs.get('monthly_search_volume_exact'),
            'monthly_search_volume_broad': attrs.get('monthly_search_volume_broad'),
            'ppc_bid_exact': attrs.get('ppc_bid_exact'),
            'ease_of_ranking_score': attrs.get('ease_of_ranking_score'),
            'organic_product_count': attrs.get('organic_product_count'),
            'organic_rank': attrs.get('organic_rank'),
            'sponsored_rank': attrs.get('sponsored_rank'),
            'overall_rank': attrs.get('overall_rank'),
        })
    return _write_csv(rows, columns, f'{output_dir}/asin_keywords.csv')


def save_sales_estimates_csv(data, asin, output_dir):
    columns = ['asin', 'date', 'estimated_units_sold', 'last_known_price']
    rows = []
    for item in (data or []):
        attrs = item.get('attributes', item)
        item_asin = attrs.get('asin') or asin
        for dp in (attrs.get('data') or []):
            rows.append({
                'asin': item_asin,
                'date': dp.get('date'),
                'estimated_units_sold': dp.get('estimated_units_sold'),
                'last_known_price': dp.get('last_known_price'),
            })
    return _write_csv(rows, columns, f'{output_dir}/asin_sales.csv')


# ============================================================
# Batch conversion: read raw JSON files → CSV
# ============================================================

_RAW_FILE_MAP = {
    'raw_keywords.json': ('save_keywords_csv', []),
    'raw_historical.json': ('save_historical_csv', ['keyword']),
    'raw_products.json': ('save_product_database_csv', []),
    'raw_sov.json': ('save_share_of_voice_csv', []),
    'raw_asin_keywords.json': ('save_keywords_by_asin_csv', []),
    'raw_asin_sales.json': ('save_sales_estimates_csv', ['asin']),
}


def convert_all(data_dir: str, keyword: str = '', asin: str = '') -> dict:
    """Read all raw_*.json files from data_dir and convert to CSV."""
    converters = {
        'save_keywords_csv': save_keywords_csv,
        'save_historical_csv': save_historical_csv,
        'save_product_database_csv': save_product_database_csv,
        'save_share_of_voice_csv': save_share_of_voice_csv,
        'save_keywords_by_asin_csv': save_keywords_by_asin_csv,
        'save_sales_estimates_csv': save_sales_estimates_csv,
    }
    extra_args = {'keyword': keyword, 'asin': asin}
    results = {}
    for raw_file, (func_name, needed_args) in _RAW_FILE_MAP.items():
        raw_path = os.path.join(data_dir, raw_file)
        if not os.path.exists(raw_path):
            continue
        try:
            with open(raw_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            kwargs = {'data': data, 'output_dir': data_dir}
            for arg in needed_args:
                kwargs[arg] = extra_args.get(arg, '')
            row_count = converters[func_name](**kwargs)
            results[raw_file] = row_count
            print(f"  ✅ {raw_file} → {row_count} rows")
        except Exception as e:
            results[raw_file] = 0
            print(f"  ❌ {raw_file} failed: {e}")
    return results

