"""
PPC Keyword Harvesting Script — MCP data processing (js_keywords_by_asin).

Harvest keywords from competitor ASINs, prioritize by PPC bid and search volume tiers,
and output a keyword list ready for ad campaign setup.


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


def ppc_keyword_harvesting(
    mcp_data,
    output_dir: str | None = None,
    source_asin: str = '',
    min_search_volume: int = 100,
) -> dict[str, Any]:
    """Process MCP response from js_keywords_by_asin for PPC keyword harvesting."""
    items = _unwrap_response(mcp_data)
    data_dir = output_dir or '.'
    os.makedirs(data_dir, exist_ok=True)

    all_rows = []
    for item in (items or []):
        attrs = item.get('attributes', item)
        row = {'source_asin': source_asin}
        row.update(attrs)
        all_rows.append(row)

    if not all_rows:
        return {'output_dir': data_dir, 'total_unique_keywords': 0,
                'tier_counts': {}, 'raw_csv': '', 'tiered_csv': ''}

    df = pd.DataFrame(all_rows)
    kw_col = 'name'
    vol_col = 'monthly_search_volume_exact'
    bid_col = 'ppc_bid_exact'

    if vol_col in df.columns:
        df = df.sort_values(vol_col, ascending=False).drop_duplicates(subset=[kw_col]).reset_index(drop=True)
    if vol_col in df.columns:
        df = df[df[vol_col].fillna(0) >= min_search_volume].copy()

    raw_csv = os.path.join(data_dir, 'ppc_keywords_raw.csv')
    df.to_csv(raw_csv, index=False, encoding='utf-8-sig')

    def _tier(row):
        vol = row.get(vol_col, 0) or 0
        bid = row.get(bid_col, 999) or 999
        try: vol, bid = float(vol), float(bid)
        except (ValueError, TypeError): return 'low_priority'
        if vol >= 1000 and bid <= 2.5: return 'high_priority'
        if vol >= 500 or bid <= 1.5: return 'medium_priority'
        return 'low_priority'

    df['ppc_priority'] = df.apply(_tier, axis=1)
    tiered_csv = os.path.join(data_dir, 'ppc_keywords_tiered.csv')
    df_sorted = df.sort_values(['ppc_priority', vol_col if vol_col in df.columns else kw_col],
                               ascending=[True, False]).reset_index(drop=True)
    df_sorted.to_csv(tiered_csv, index=False, encoding='utf-8-sig')
    tier_counts = df['ppc_priority'].value_counts().to_dict()

    return {
        'output_dir': data_dir, 'total_unique_keywords': len(df),
        'tier_counts': tier_counts, 'raw_csv': raw_csv, 'tiered_csv': tiered_csv,
    }

