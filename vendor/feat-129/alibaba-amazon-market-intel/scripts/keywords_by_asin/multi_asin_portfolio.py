"""
Multi-ASIN Keyword Portfolio Script — MCP data processing (js_keywords_by_asin).

Batch-collect keywords for multiple ASINs in a brand catalog, build a keyword × ASIN matrix,
identify:
  - Keyword coverage gaps (high-value keywords with no ASIN ranking)
  - Keyword overlap/cannibalization (multiple ASINs competing for the same keyword)
  - Unique keywords per ASIN


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


def multi_asin_portfolio(
    mcp_data,
    output_dir: str | None = None,
    asin: str = '',
    cannibalization_threshold: int = 2,
) -> dict[str, Any]:
    """Process MCP response from js_keywords_by_asin for multi-ASIN portfolio."""
    items = _unwrap_response(mcp_data)
    data_dir = output_dir or '.'
    os.makedirs(data_dir, exist_ok=True)

    all_rows = []
    for item in (items or []):
        attrs = item.get('attributes', item)
        row = {'asin': asin or attrs.get('asin', '')}
        row.update(attrs)
        all_rows.append(row)

    if not all_rows:
        return {'output_dir': data_dir, 'total_unique_keywords': 0,
                'cannibalization_count': 0, 'rows_per_asin': {},
                'raw_csv': '', 'matrix_csv': '', 'cannibalization_csv': ''}

    df = pd.DataFrame(all_rows)
    kw_col = 'name'
    vol_col = 'monthly_search_volume_exact'

    raw_csv = os.path.join(data_dir, 'portfolio_raw.csv')
    df.to_csv(raw_csv, index=False, encoding='utf-8-sig')

    matrix_csv = ''
    cannibal_csv = ''
    cannibal_df = pd.DataFrame()
    if kw_col in df.columns:
        matrix_df = df.groupby([kw_col, 'asin']).size().unstack(fill_value=0).clip(upper=1).reset_index()
        if vol_col in df.columns:
            vol_map = df.groupby(kw_col)[vol_col].max()
            matrix_df = matrix_df.merge(vol_map.rename(vol_col), on=kw_col, how='left')
            matrix_df = matrix_df.sort_values(vol_col, ascending=False).reset_index(drop=True)
        matrix_csv = os.path.join(data_dir, 'keyword_asin_matrix.csv')
        matrix_df.to_csv(matrix_csv, index=False, encoding='utf-8-sig')

        asin_cols = [c for c in matrix_df.columns if c not in (kw_col, vol_col)]
        matrix_df['asin_coverage_count'] = matrix_df[asin_cols].sum(axis=1)
        cannibal_df = matrix_df[matrix_df['asin_coverage_count'] >= cannibalization_threshold].copy()
        cannibal_df = cannibal_df.sort_values(vol_col if vol_col in cannibal_df.columns else 'asin_coverage_count', ascending=False).reset_index(drop=True)
        cannibal_csv = os.path.join(data_dir, 'cannibalization.csv')
        cannibal_df.to_csv(cannibal_csv, index=False, encoding='utf-8-sig')

    return {
        'output_dir': data_dir,
        'total_unique_keywords': df[kw_col].nunique() if kw_col in df.columns else 0,
        'cannibalization_count': len(cannibal_df),
        'rows_per_asin': {asin: len(all_rows)},
        'raw_csv': raw_csv, 'matrix_csv': matrix_csv, 'cannibalization_csv': cannibal_csv,
    }

