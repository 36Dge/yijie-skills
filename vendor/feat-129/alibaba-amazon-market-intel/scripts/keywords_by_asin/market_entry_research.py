"""
Market Entry Research Script — MCP data processing (js_keywords_by_asin).

Batch-collect keywords from top seller ASINs in a new category to quickly build a category keyword landscape.
Outputs: full keyword universe, high-volume core keywords, low-competition entry keywords.


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


def market_entry_research(
    mcp_data,
    output_dir: str | None = None,
    source_asin: str = '',
    category_name: str = 'unknown_category',
    core_kw_vol_threshold: int = 1000,
    entry_ease_threshold: int = 65,
    entry_vol_min: int = 300,
) -> dict[str, Any]:
    """Process MCP response from js_keywords_by_asin for market entry research."""
    items = _unwrap_response(mcp_data)
    data_dir = output_dir or '.'
    os.makedirs(data_dir, exist_ok=True)

    all_rows = []
    for item in (items or []):
        attrs = item.get('attributes', item)
        row = {'source_asin': source_asin, 'category': category_name}
        row.update(attrs)
        all_rows.append(row)

    if not all_rows:
        return {'output_dir': data_dir, 'category_name': category_name,
                'total_unique_keywords': 0, 'core_keyword_count': 0,
                'entry_opportunity_count': 0, 'rows_per_asin': {},
                'raw_csv': '', 'universe_csv': '', 'core_csv': '', 'entry_csv': ''}

    df = pd.DataFrame(all_rows)
    kw_col = 'name'
    vol_col = 'monthly_search_volume_exact'
    eas_col = 'ease_of_ranking_score'

    raw_csv = os.path.join(data_dir, 'market_keywords_raw.csv')
    df.to_csv(raw_csv, index=False, encoding='utf-8-sig')

    if vol_col in df.columns:
        df[vol_col] = pd.to_numeric(df[vol_col], errors='coerce')
        universe_df = df.sort_values(vol_col, ascending=False).drop_duplicates(subset=[kw_col]).reset_index(drop=True)
    else:
        universe_df = df.drop_duplicates(subset=[kw_col]).reset_index(drop=True)

    universe_csv = os.path.join(data_dir, 'category_keyword_universe.csv')
    universe_df.to_csv(universe_csv, index=False, encoding='utf-8-sig')

    core_df = pd.DataFrame()
    if vol_col in universe_df.columns:
        core_df = universe_df[universe_df[vol_col].fillna(0) >= core_kw_vol_threshold].copy()
    core_csv = os.path.join(data_dir, 'core_keywords.csv')
    core_df.to_csv(core_csv, index=False, encoding='utf-8-sig')

    if eas_col in universe_df.columns:
        universe_df[eas_col] = pd.to_numeric(universe_df[eas_col], errors='coerce')
    entry_mask = pd.Series([True] * len(universe_df), index=universe_df.index)
    if vol_col in universe_df.columns:
        entry_mask &= universe_df[vol_col].fillna(0) >= entry_vol_min
    if eas_col in universe_df.columns:
        entry_mask &= universe_df[eas_col].fillna(0) >= entry_ease_threshold
    entry_df = universe_df[entry_mask].copy()
    entry_csv = os.path.join(data_dir, 'entry_opportunity.csv')
    entry_df.to_csv(entry_csv, index=False, encoding='utf-8-sig')

    return {
        'output_dir': data_dir, 'category_name': category_name,
        'total_unique_keywords': len(universe_df), 'core_keyword_count': len(core_df),
        'entry_opportunity_count': len(entry_df), 'rows_per_asin': {source_asin: len(all_rows)},
        'raw_csv': raw_csv, 'universe_csv': universe_csv,
        'core_csv': core_csv, 'entry_csv': entry_csv,
    }

