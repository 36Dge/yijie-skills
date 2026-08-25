"""
Year-over-Year Growth Analysis — MCP data processing (js_historical_search_volume).

Aligns weekly search volume data by week index, computes YoY growth rate, CAGR,
and growth acceleration to measure category expansion or contraction.
"""

from __future__ import annotations

import math
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


def _compute_yoy_summary(df: pd.DataFrame, years: list[int]) -> pd.DataFrame:
    """Compute per-keyword per-year summary with YoY growth, CAGR, and trend."""
    sorted_years = sorted(years)
    summaries = []

    for keyword, kw_group in df.groupby('keyword'):
        year_stats: dict[int, dict] = {}

        for year in sorted_years:
            yr_data = kw_group[kw_group['year'] == year].sort_values('week_index')
            if yr_data.empty:
                continue
            volumes = yr_data['estimated_exact_search_volume']
            peak_idx = volumes.idxmax()
            year_stats[year] = {
                'keyword': keyword,
                'year': year,
                'total_volume': int(volumes.sum()),
                'mean_weekly_volume': round(volumes.mean(), 1),
                'peak_volume': int(volumes.max()),
                'peak_week_date': str(yr_data.loc[peak_idx, 'estimate_start_date']),
            }

        prev_yoy: float | None = None
        for i, year in enumerate(sorted_years):
            if year not in year_stats:
                continue
            stats = year_stats[year]

            yoy_growth: float | None = None
            if i > 0 and sorted_years[i - 1] in year_stats:
                prev_vol = year_stats[sorted_years[i - 1]]['total_volume']
                if prev_vol > 0:
                    yoy_growth = round(
                        (stats['total_volume'] - prev_vol) / prev_vol * 100, 2
                    )

            cagr: float | None = None
            first_year = sorted_years[0]
            if year != first_year and first_year in year_stats:
                first_vol = year_stats[first_year]['total_volume']
                n_years = year - first_year
                if first_vol > 0 and n_years > 0:
                    cagr = round(
                        (math.pow(stats['total_volume'] / first_vol, 1 / n_years) - 1) * 100, 2
                    )

            growth_trend = 'insufficient_data'
            if yoy_growth is not None and prev_yoy is not None:
                diff = yoy_growth - prev_yoy
                if diff > 2:
                    growth_trend = 'accelerating'
                elif diff < -2:
                    growth_trend = 'decelerating'
                else:
                    growth_trend = 'stable'

            stats['yoy_growth_pct'] = yoy_growth
            stats['cagr_pct'] = cagr
            stats['growth_trend'] = growth_trend
            summaries.append(stats)
            prev_yoy = yoy_growth

    return pd.DataFrame(summaries)


def analyze_yoy_growth(
    mcp_data,
    output_dir: str | None = None,
    keyword: str = '',
) -> dict[str, Any]:
    """
    Process MCP response from js_historical_search_volume for YoY analysis.

    Args:
        mcp_data:    Pre-fetched MCP response data (items should include year, week_index fields).
        output_dir:  Directory for output CSVs.
        keyword:     The keyword label for rows.
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
            'yoy_growth_csv': '',
            'yoy_summary_csv': '',
        }

    df = pd.DataFrame(all_rows)

    csv_path = os.path.join(data_dir, 'yoy_growth.csv')
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')

    years = sorted(df['year'].unique().tolist()) if 'year' in df.columns else []
    summary_df = _compute_yoy_summary(df, years)
    summary_path = os.path.join(data_dir, 'yoy_summary.csv')
    summary_df.to_csv(summary_path, index=False, encoding='utf-8-sig')

    return {
        'output_dir': data_dir,
        'total_rows': len(df),
        'columns': list(df.columns),
        'yoy_growth_csv': csv_path,
        'yoy_summary_csv': summary_path,
    }

