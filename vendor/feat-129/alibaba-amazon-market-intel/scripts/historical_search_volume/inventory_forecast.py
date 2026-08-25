"""
Inventory Planning & Demand Forecasting — MCP data processing (js_historical_search_volume).

Fetches weekly exact search volume, computes moving averages, WoW change,
demand ramp-up/ramp-down inflection points, and suggested stocking week
based on a configurable supply-chain lead time.


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


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DEFAULT_LEAD_TIME_WEEKS = 4
MA_WINDOW = 4
RAMP_CONSECUTIVE_WEEKS = 3


def _add_forecast_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Add MA4, WoW change %, and trend direction columns per keyword."""
    result_frames = []
    for keyword, group in df.groupby('keyword'):
        g = group.sort_values('estimate_start_date').copy()
        vol = g['estimated_exact_search_volume']

        # 4-week moving average
        g['ma4'] = vol.rolling(window=MA_WINDOW, min_periods=1).mean().round(1)

        # Week-over-week change %
        g['wow_change_pct'] = vol.pct_change().mul(100).round(2).fillna(0.0)

        # Trend direction
        g['trend_direction'] = g['wow_change_pct'].apply(
            lambda x: 'up' if x > 2 else ('down' if x < -2 else 'flat')
        )
        result_frames.append(g)

    return pd.concat(result_frames, ignore_index=True)


def _find_ramp_week(
    wow_series: pd.Series,
    dates_series: pd.Series,
    direction: str = 'up',
) -> str:
    """Find the first week where N consecutive weeks trend in the given direction.

    Args:
        wow_series: Series of wow_change_pct values, sorted chronologically.
        dates_series: Corresponding estimate_start_date values.
        direction: 'up' for ramp-up, 'down' for ramp-down.

    Returns:
        The estimate_start_date string of the inflection point, or '' if not found.
    """
    threshold = 2.0 if direction == 'up' else -2.0
    consecutive = 0
    start_idx = None

    for i, val in enumerate(wow_series):
        if (direction == 'up' and val > threshold) or (direction == 'down' and val < threshold):
            if consecutive == 0:
                start_idx = i
            consecutive += 1
            if consecutive >= RAMP_CONSECUTIVE_WEEKS:
                return str(dates_series.iloc[start_idx])
        else:
            consecutive = 0
            start_idx = None
    return ''


def _compute_forecast_summary(
    df: pd.DataFrame,
    lead_time_weeks: int,
) -> pd.DataFrame:
    """Compute per-keyword forecast summary with inflection points and stocking advice."""
    summaries = []
    for keyword, group in df.groupby('keyword'):
        g = group.sort_values('estimate_start_date').reset_index(drop=True)
        volumes = g['estimated_exact_search_volume']
        max_idx = volumes.idxmax()
        min_idx = volumes.idxmin()

        ramp_up = _find_ramp_week(
            g['wow_change_pct'].values,
            g['estimate_start_date'].values,
            direction='up',
        )
        ramp_down = _find_ramp_week(
            g['wow_change_pct'].values,
            g['estimate_start_date'].values,
            direction='down',
        )

        # Suggested stocking week = ramp_up - lead_time_weeks
        suggested_stock = ''
        if ramp_up:
            ramp_up_idx = g[g['estimate_start_date'] == ramp_up].index
            if len(ramp_up_idx) > 0:
                stock_idx = max(0, ramp_up_idx[0] - lead_time_weeks)
                suggested_stock = str(g.loc[stock_idx, 'estimate_start_date'])

        latest_trend = str(g.iloc[-1]['trend_direction']) if len(g) > 0 else ''

        summaries.append({
            'keyword': keyword,
            'total_weeks': len(g),
            'mean_weekly_volume': round(volumes.mean(), 1),
            'peak_volume': int(volumes.max()),
            'peak_week': str(g.loc[max_idx, 'estimate_start_date']),
            'trough_volume': int(volumes.min()),
            'trough_week': str(g.loc[min_idx, 'estimate_start_date']),
            'ramp_up_week': ramp_up,
            'ramp_down_week': ramp_down,
            'suggested_stock_week': suggested_stock,
            'latest_trend': latest_trend,
        })
    return pd.DataFrame(summaries)


def inventory_demand_forecast(
    mcp_data,
    output_dir: str | None = None,
    keyword: str = '',
    lead_time_weeks: int = 4,
) -> dict[str, Any]:
    """
    Process MCP response from js_historical_search_volume.

    Args:
        mcp_data:    Pre-fetched MCP response data.
        output_dir:  Directory for output CSVs.
        keyword:     The keyword label for rows.
        lead_time_weeks: int = 4

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
            'inventory_forecast_csv': '',
            'forecast_summary_csv': '',
        }

    df = pd.DataFrame(all_rows)
    df = _add_forecast_columns(df)

    csv_path = os.path.join(data_dir, 'inventory_forecast.csv')
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')

    summary_path = os.path.join(data_dir, 'forecast_summary.csv')
    summary_df = _compute_forecast_summary(df, lead_time_weeks)
    summary_df.to_csv(summary_path, index=False, encoding='utf-8-sig')

    return {
        'output_dir': data_dir,
        'total_rows': len(df),
        'columns': list(df.columns),
        'inventory_forecast_csv': csv_path,
        'forecast_summary_csv': summary_path,
    }

