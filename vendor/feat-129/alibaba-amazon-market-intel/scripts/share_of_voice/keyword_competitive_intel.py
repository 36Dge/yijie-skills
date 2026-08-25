"""Keyword Competitive Intel — MCP data processing. Analyze brand concentration per keyword."""

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
    """Process MCP response from js_share_of_voice for keyword competitive intel."""
    items = _unwrap_response(mcp_data)
    data_dir = output_dir or '.'
    os.makedirs(data_dir, exist_ok=True)

    if isinstance(items, dict):
        items = [items]

    keyword_intel = []
    brand_rows = []

    for item in (items or []):
        attrs = item.get('attributes', item)
        search_volume = attrs.get('estimated_30_day_search_volume')
        brands = attrs.get('brands', []) or []

        brands_data = []
        for brand_item in brands:
            sov = brand_item.get('combined_weighted_sov', 0) or 0
            brands_data.append({'brand': brand_item.get('brand'), 'sov': sov})
            brand_rows.append({
                'keyword': keyword,
                'brand': brand_item.get('brand'),
                'combined_sov_weighted': sov,
                'organic_sov_weighted': brand_item.get('organic_weighted_sov'),
                'sponsored_sov_weighted': brand_item.get('sponsored_weighted_sov'),
                'search_volume_30d': search_volume,
            })

        sorted_brands = sorted(brands_data, key=lambda x: x['sov'], reverse=True)
        top3_share = sum(b['sov'] for b in sorted_brands[:3])
        keyword_intel.append({
            'keyword': keyword,
            'total_brands': len(sorted_brands),
            'top3_brand_share': top3_share,
            'concentration': (
                'dominated' if top3_share > 0.6
                else 'fragmented' if top3_share < 0.3
                else 'moderate'),
            'top_brand': sorted_brands[0]['brand'] if sorted_brands else None,
            'top_brand_sov': sorted_brands[0]['sov'] if sorted_brands else None,
        })

    intel_csv = os.path.join(data_dir, 'keyword_competitive_intel.csv')
    pd.DataFrame(keyword_intel).to_csv(intel_csv, index=False, encoding='utf-8-sig')

    detail_csv = os.path.join(data_dir, 'keyword_brand_detail.csv')
    pd.DataFrame(brand_rows).to_csv(detail_csv, index=False, encoding='utf-8-sig')

    return {
        'output_dir': data_dir,
        'total_rows': len(brand_rows),
        'intel_csv': intel_csv,
        'detail_csv': detail_csv,
    }

