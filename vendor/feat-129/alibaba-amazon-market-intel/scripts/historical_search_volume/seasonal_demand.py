"""
Seasonal Demand Profiling — MCP data processing (js_historical_search_volume).

Fetches weekly exact search volume for each keyword over a date range,
computes seasonal metrics (peak/trough week, CV, peak-trough ratio),
and outputs two CSVs: raw time-series + keyword-level summary.


"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
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


def _compute_seasonal_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Compute per-keyword seasonal metrics from the raw time-series."""
    summaries = []
    for keyword, group in df.groupby('keyword'):
        volumes = group['estimated_exact_search_volume']
        max_idx = volumes.idxmax()
        min_idx = volumes.idxmin()
        mean_vol = volumes.mean()
        std_vol = volumes.std()
        summaries.append({
            'keyword': keyword,
            'total_weeks': len(group),
            'mean_weekly_volume': round(mean_vol, 1),
            'max_volume': int(volumes.max()),
            'max_volume_week': group.loc[max_idx, 'estimate_start_date'],
            'min_volume': int(volumes.min()),
            'min_volume_week': group.loc[min_idx, 'estimate_start_date'],
            'std_dev': round(std_vol, 1),
            'cv': round(std_vol / mean_vol, 3) if mean_vol > 0 else 0.0,
            'peak_trough_ratio': round(volumes.max() / volumes.min(), 2) if volumes.min() > 0 else float('inf'),
        })
    return pd.DataFrame(summaries)


def seasonal_demand_profile(
    mcp_data,
    output_dir: str | None = None,
    keyword: str = '',
) -> dict[str, Any]:
    """
    Process MCP response from js_historical_search_volume.

    Args:
        mcp_data:    Pre-fetched MCP response data.
        output_dir:  Directory for output CSVs.
        keyword:     The keyword label for rows.

    Returns:
        dict with output paths and metrics.
    """
    items = _unwrap_response(mcp_data)
    data_dir = output_dir or '.'
    os.makedirs(data_dir, exist_ok=True)

    all_rows = []
    for item in (items or []):
        attrs = item.get('attributes', item)
        row = {'keyword': keyword}
        row.update(attrs)
        all_rows.append(row)

    if not all_rows:
        return {
            'output_dir': data_dir,
            'total_rows': 0,
            'columns': [],
            'seasonal_demand_csv': '',
            'seasonal_summary_csv': '',
        }

    df = pd.DataFrame(all_rows)

    csv_path = os.path.join(data_dir, 'seasonal_demand.csv')
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')

    summary_path = os.path.join(data_dir, 'seasonal_summary.csv')
    summary_df = _compute_seasonal_summary(df)
    summary_df.to_csv(summary_path, index=False, encoding='utf-8-sig')

    return {
        'output_dir': data_dir,
        'total_rows': len(df),
        'columns': list(df.columns),
        'seasonal_demand_csv': csv_path,
        'seasonal_summary_csv': summary_path,
    }

