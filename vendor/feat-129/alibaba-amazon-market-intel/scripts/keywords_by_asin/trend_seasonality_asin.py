"""
Trend & Seasonality Detection Script — MCP data processing (js_keywords_by_asin).

Collects keywords for target ASINs, extracts monthly and quarterly trend data,
and identifies:
  - Rising trend keywords (significant month-over-month or quarter-over-quarter growth)
  - Declining trend keywords (significant month-over-month or quarter-over-quarter decline)
  - Seasonal peak keywords (quarterly trend significantly higher than monthly trend)


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


def trend_seasonality_asin(
    mcp_data,
    output_dir: str | None = None,
    asin: str = '',
    rising_threshold: float = 0.1,
    falling_threshold: float = -0.1,
    min_search_volume: int = 200,
) -> dict[str, Any]:
    """Process MCP response from js_keywords_by_asin for trend/seasonality detection."""
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
                'rising_count': 0, 'falling_count': 0, 'seasonal_count': 0,
                'raw_csv': '', 'rising_csv': '', 'falling_csv': '', 'seasonal_csv': ''}

    df = pd.DataFrame(all_rows)
    vol_col = 'monthly_search_volume_exact'
    mo_col = 'monthly_trend'
    qt_col = 'quarterly_trend'

    raw_csv = os.path.join(data_dir, 'trend_raw.csv')
    df.to_csv(raw_csv, index=False, encoding='utf-8-sig')

    for c in (vol_col, mo_col, qt_col):
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')

    if vol_col in df.columns:
        df = df[df[vol_col].fillna(0) >= min_search_volume].copy()

    def _save(mask_df, path):
        if vol_col in mask_df.columns:
            mask_df = mask_df.sort_values(vol_col, ascending=False)
        mask_df.reset_index(drop=True).to_csv(path, index=False, encoding='utf-8-sig')

    rising_mask = pd.Series([False] * len(df), index=df.index)
    if mo_col in df.columns: rising_mask |= df[mo_col].fillna(0) > rising_threshold
    if qt_col in df.columns: rising_mask |= df[qt_col].fillna(0) > rising_threshold
    rising_df = df[rising_mask].copy()
    rising_csv = os.path.join(data_dir, 'rising_keywords.csv')
    _save(rising_df, rising_csv)

    falling_mask = pd.Series([False] * len(df), index=df.index)
    if mo_col in df.columns: falling_mask |= df[mo_col].fillna(0) < falling_threshold
    if qt_col in df.columns: falling_mask |= df[qt_col].fillna(0) < falling_threshold
    falling_df = df[falling_mask].copy()
    falling_csv = os.path.join(data_dir, 'falling_keywords.csv')
    _save(falling_df, falling_csv)

    seasonal_mask = pd.Series([False] * len(df), index=df.index)
    if mo_col in df.columns and qt_col in df.columns:
        seasonal_mask = (df[qt_col].fillna(0) - df[mo_col].fillna(0)) > 0.15
    seasonal_df = df[seasonal_mask].copy()
    seasonal_csv = os.path.join(data_dir, 'seasonal_keywords.csv')
    _save(seasonal_df, seasonal_csv)

    return {
        'output_dir': data_dir, 'total_keywords': len(df),
        'rising_count': len(rising_df), 'falling_count': len(falling_df),
        'seasonal_count': len(seasonal_df),
        'raw_csv': raw_csv, 'rising_csv': rising_csv,
        'falling_csv': falling_csv, 'seasonal_csv': seasonal_csv,
    }

