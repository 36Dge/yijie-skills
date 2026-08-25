"""
Competitive Benchmarking Over Time — MCP data processing (js_historical_search_volume).

Fetches weekly search volume for multiple keywords (category + brand terms),
computes Share of Search, WoW change, Pearson correlation between keywords,
and total growth rate for competitive benchmarking.


"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Any

import numpy as np
import pandas as pd

def _unwrap_response(data):
    """Unwrap MCP response envelope if present."""
    if isinstance(data, str):
        import json as _json
        data = _json.loads(data)
    if isinstance(data, dict) and 'data' in data:
        return data['data']
    return data


def _add_benchmark_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Add share_of_search and wow_change_pct columns."""
    # WoW change per keyword
    result_frames = []
    for keyword, group in df.groupby('keyword'):
        g = group.sort_values('estimate_start_date').copy()
        vol = g['estimated_exact_search_volume']
        g['wow_change_pct'] = vol.pct_change().mul(100).round(2).fillna(0.0)
        result_frames.append(g)
    df = pd.concat(result_frames, ignore_index=True)

    # Share of Search: per week, each keyword's volume / total volume across all keywords
    weekly_total = (
        df.groupby('estimate_start_date')['estimated_exact_search_volume']
        .transform('sum')
    )
    df['share_of_search'] = (
        df['estimated_exact_search_volume'] / weekly_total.replace(0, np.nan) * 100
    ).round(2).fillna(0.0)

    return df


def _compute_benchmark_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Compute per-keyword competitive benchmark summary."""
    # Build a pivot table for correlation calculation
    pivot = df.pivot_table(
        index='estimate_start_date',
        columns='keyword',
        values='estimated_exact_search_volume',
        aggfunc='first',
    ).sort_index()

    all_keywords = list(pivot.columns)
    corr_matrix = pivot.corr()

    summaries = []
    for keyword in all_keywords:
        kw_data = df[df['keyword'] == keyword].sort_values('estimate_start_date').reset_index(drop=True)
        volumes = kw_data['estimated_exact_search_volume']
        shares = kw_data['share_of_search']
        peak_idx = volumes.idxmax()

        # Total growth: first week vs last week
        first_vol = volumes.iloc[0] if len(volumes) > 0 else 0
        last_vol = volumes.iloc[-1] if len(volumes) > 0 else 0
        total_growth = round((last_vol - first_vol) / first_vol * 100, 2) if first_vol > 0 else 0.0

        # Average correlation with other keywords
        other_kws = [k for k in all_keywords if k != keyword]
        if other_kws:
            avg_corr = round(corr_matrix.loc[keyword, other_kws].mean(), 3)
        else:
            avg_corr = 0.0

        summaries.append({
            'keyword': keyword,
            'total_weeks': len(kw_data),
            'mean_weekly_volume': round(volumes.mean(), 1),
            'mean_share_of_search': round(shares.mean(), 2),
            'peak_volume': int(volumes.max()),
            'peak_week': str(kw_data.loc[peak_idx, 'estimate_start_date']),
            'total_growth_pct': total_growth,
            'correlation_with_others': avg_corr,
        })
    return pd.DataFrame(summaries)


def analyze_competitive_benchmark(
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
            'competitive_benchmark_csv': '',
            'benchmark_summary_csv': '',
        }

    df = pd.DataFrame(all_rows)
    df = _add_benchmark_columns(df)

    csv_path = os.path.join(data_dir, 'competitive_benchmark.csv')
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')

    summary_path = os.path.join(data_dir, 'benchmark_summary.csv')
    summary_df = _compute_benchmark_summary(df)
    summary_df.to_csv(summary_path, index=False, encoding='utf-8-sig')

    return {
        'output_dir': data_dir,
        'total_rows': len(df),
        'columns': list(df.columns),
        'competitive_benchmark_csv': csv_path,
        'benchmark_summary_csv': summary_path,
    }

