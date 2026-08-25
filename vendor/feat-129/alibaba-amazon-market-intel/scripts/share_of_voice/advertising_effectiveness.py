"""Advertising Effectiveness — Measure incremental visibility from paid placements vs organic rankings.

SOV API response structure (returns one object per keyword):
  resp.data.attributes.brands          → list[dict]  Brand-level SOV data
  resp.data.attributes.top_asins       → list[dict]  Top 3 ASIN conversion data
  resp.data.attributes.estimated_30_day_search_volume → int
  resp.data.attributes.exact_suggested_bid_median     → float
"""

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


def analyze(mcp_data, output_dir=None, keyword=''):
    """Process MCP response from js_share_of_voice."""
    items = _unwrap_response(mcp_data)
    data_dir = output_dir or '.'
    os.makedirs(data_dir, exist_ok=True)

    all_rows = []
    if isinstance(items, dict):
        items = [items]

    for item in (items or []):
        attrs = item.get('attributes', item)
        if isinstance(attrs, dict) and isinstance(attrs, dict):
            attr_dict = attrs
        else:
            attr_dict = attrs

        search_volume = attr_dict.get('estimated_30_day_search_volume')
        ppc_bid = attr_dict.get('exact_suggested_bid_median')
        brands = attr_dict.get('brands', []) or []
        for brand_item in brands:
            organic_w = brand_item.get('organic_weighted_sov', 0) or 0
            sponsored_w = brand_item.get('sponsored_weighted_sov', 0) or 0
            all_rows.append({
                'keyword': keyword,
                'brand': brand_item.get('brand'),
                'organic_sov_weighted': organic_w,
                'sponsored_sov_weighted': sponsored_w,
                'combined_sov_weighted': brand_item.get('combined_weighted_sov'),
                'ad_incremental_lift': sponsored_w - organic_w,
                'organic_sov_basic': brand_item.get('organic_basic_sov'),
                'sponsored_sov_basic': brand_item.get('sponsored_basic_sov'),
                'ppc_bid': ppc_bid,
                'search_volume_30d': search_volume,
            })

    if not all_rows:
        return {'output_dir': data_dir, 'total_rows': 0, 'csv_path': ''}

    df = pd.DataFrame(all_rows)

    if not df.empty:
        df['ad_strategy'] = df.apply(
            lambda r: 'reduce_spend' if r['organic_sov_weighted'] > 0.1 and r['sponsored_sov_weighted'] < 0.02
            else 'increase_spend' if r['organic_sov_weighted'] < 0.02 and r['sponsored_sov_weighted'] > 0
            else 'maintain',
            axis=1,
        )

    csv_path = os.path.join(data_dir, 'advertising_effectiveness.csv')
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')

    return {'output_dir': data_dir, 'total_rows': len(df), 'csv_path': csv_path}

