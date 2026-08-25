"""Market Opportunity Discovery — Filter by category, revenue, and review count to find high-revenue, low-competition blue-ocean niches."""

from __future__ import annotations

import os
from typing import Any

import pandas as pd


def _unwrap_response(data):
    """Unwrap MCP response envelope if present."""
    if isinstance(data, str):
        import json as _json
        data = _json.loads(data)
    if isinstance(data, dict) and 'data' in data:
        return data['data']
    return data


def analyze(mcp_data, output_dir=None):
    """Process MCP response from js_product_database."""
    items = _unwrap_response(mcp_data)
    data_dir = output_dir or '.'
    os.makedirs(data_dir, exist_ok=True)

    rows = []
    for item in (items or []):
        attrs = item.get('attributes', item)
        bare_asin = item.get('id', '').split('/')[-1]
        revenue = attrs.get('approximate_30_day_revenue') or 0
        reviews = attrs.get('reviews') or 0
        if revenue < 10000 or reviews > 200:
            continue
        rows.append({
            'asin': bare_asin, 'title': attrs.get('title'),
            'brand': attrs.get('brand'), 'price': attrs.get('price'),
            'sales_cnt_30d': attrs.get('approximate_30_day_units_sold'),
            'revenue_30d': revenue, 'reviews': reviews,
            'rating': attrs.get('rating'),
            'seller_type': attrs.get('seller_type'),
            'category': attrs.get('category'),
            'lqs': attrs.get('listing_quality_score'),
            'imageUrl': attrs.get('image_url'),
            'prodUrl': f'https://www.amazon.com/dp/{bare_asin}',
        })

    if not rows:
        return {'output_dir': data_dir, 'total_rows': 0, 'csv_path': ''}

    csv_path = os.path.join(data_dir, 'niche_candidates.csv')
    pd.DataFrame(rows).to_csv(csv_path, index=False, encoding='utf-8-sig')

    return {
        'output_dir': data_dir,
        'total_rows': len(rows),
        'csv_path': csv_path,
    }

