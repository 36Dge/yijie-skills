"""
Listing SEO Keyword Optimization Script — MCP data processing (js_keywords_by_asin).

Collect keywords from a target ASIN, identify:
  - High search volume keywords (should appear in title/bullets)
  - High search volume + low ranking difficulty keywords (can drive incremental traffic after optimization)
  - Indexed but low-ranking keywords (worth prioritizing for optimization)


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


def listing_seo_optimization(
    mcp_data,
    output_dir: str | None = None,
    asin: str = '',
    high_vol_threshold: int = 1000,
    easy_rank_threshold: int = 60,
) -> dict[str, Any]:
    """Process MCP response from js_keywords_by_asin for SEO optimization."""
    items = _unwrap_response(mcp_data)
    data_dir = output_dir or '.'
    os.makedirs(data_dir, exist_ok=True)

    all_rows = []
    for item in (items or []):
        attrs = item.get('attributes', item)
        row = {'asin': asin}
        row.update(attrs)
        all_rows.append(row)

    if not all_rows:
        return {'output_dir': data_dir, 'total_keywords': 0,
                'title_bullet_count': 0, 'quick_win_count': 0, 'rank_improvement_count': 0,
                'raw_csv': '', 'title_bullet_csv': '', 'quick_win_csv': '', 'rank_improvement_csv': ''}

    df = pd.DataFrame(all_rows)
    vol_col = 'monthly_search_volume_exact'
    eas_col = 'ease_of_ranking_score'
    rank_col = 'organic_rank'

    raw_csv = os.path.join(data_dir, 'seo_keywords_raw.csv')
    df.to_csv(raw_csv, index=False, encoding='utf-8-sig')

    def _safe_float(df, col, default=0.0):
        if col not in df.columns:
            return pd.Series([default] * len(df), index=df.index)
        return pd.to_numeric(df[col], errors='coerce').fillna(default)

    vol_series = _safe_float(df, vol_col)
    eas_series = _safe_float(df, eas_col)
    rank_series = _safe_float(df, rank_col, default=999)

    title_mask = vol_series >= high_vol_threshold
    title_df = df[title_mask].sort_values(vol_col, ascending=False).reset_index(drop=True)
    title_csv = os.path.join(data_dir, 'title_bullet_keywords.csv')
    title_df.to_csv(title_csv, index=False, encoding='utf-8-sig')

    qw_mask = (vol_series >= 500) & (eas_series >= easy_rank_threshold)
    qw_df = df[qw_mask].sort_values(vol_col, ascending=False).reset_index(drop=True)
    qw_csv = os.path.join(data_dir, 'quick_win_keywords.csv')
    qw_df.to_csv(qw_csv, index=False, encoding='utf-8-sig')

    ri_mask = rank_series > 20
    ri_df = df[ri_mask].sort_values(vol_col, ascending=False).reset_index(drop=True) if rank_col in df.columns else pd.DataFrame()
    ri_csv = os.path.join(data_dir, 'rank_improvement_keywords.csv')
    ri_df.to_csv(ri_csv, index=False, encoding='utf-8-sig')

    return {
        'output_dir': data_dir, 'total_keywords': len(df),
        'title_bullet_count': len(title_df), 'quick_win_count': len(qw_df),
        'rank_improvement_count': len(ri_df),
        'raw_csv': raw_csv, 'title_bullet_csv': title_csv,
        'quick_win_csv': qw_csv, 'rank_improvement_csv': ri_csv,
    }

