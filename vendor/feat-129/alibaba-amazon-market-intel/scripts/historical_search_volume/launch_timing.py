"""
Product Launch Timing Optimization — MCP data processing (js_historical_search_volume).

Fetches weekly search volume, identifies demand ramp-up points and peak weeks,
computes the ideal pre-peak launch window, and classifies demand stability
(evergreen vs seasonal vs highly_seasonal).


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
DEFAULT_PRE_PEAK_WEEKS = 6
RAMP_CONSECUTIVE_WEEKS = 3
# CV thresholds for demand classification
CV_EVERGREEN = 0.3
CV_SEASONAL = 0.6


def _add_launch_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Add pct_of_peak, wow_change_pct, and demand phase columns per keyword."""
    result_frames = []
    for keyword, group in df.groupby('keyword'):
        g = group.sort_values('estimate_start_date').copy()
        vol = g['estimated_exact_search_volume']
        peak = vol.max()

        # Percentage of peak
        g['pct_of_peak'] = (vol / peak * 100).round(1) if peak > 0 else 0.0

        # Week-over-week change %
        g['wow_change_pct'] = vol.pct_change().mul(100).round(2).fillna(0.0)

        # Demand phase classification
        peak_idx = vol.idxmax()
        peak_pos = g.index.get_loc(peak_idx)
        phases = []
        for i, (idx, row) in enumerate(g.iterrows()):
            pct = row['pct_of_peak']
            if pct >= 90:
                phases.append('peak')
            elif i < peak_pos and row['wow_change_pct'] > 0:
                phases.append('ramp_up')
            elif i > peak_pos and row['wow_change_pct'] < 0:
                phases.append('decline')
            else:
                phases.append('trough')
        g['phase'] = phases
        result_frames.append(g)

    return pd.concat(result_frames, ignore_index=True)


def _find_ramp_up_start(wow_values, date_values) -> str:
    """Find the first week where N consecutive weeks have positive growth."""
    consecutive = 0
    start_idx = None
    for i, val in enumerate(wow_values):
        if val > 2.0:
            if consecutive == 0:
                start_idx = i
            consecutive += 1
            if consecutive >= RAMP_CONSECUTIVE_WEEKS:
                return str(date_values[start_idx])
        else:
            consecutive = 0
            start_idx = None
    return ''


def _classify_demand(cv: float) -> str:
    """Classify demand type based on coefficient of variation."""
    if cv < CV_EVERGREEN:
        return 'evergreen'
    if cv < CV_SEASONAL:
        return 'seasonal'
    return 'highly_seasonal'


def _compute_launch_summary(
    df: pd.DataFrame,
    pre_peak_weeks: int,
) -> pd.DataFrame:
    """Compute per-keyword launch timing summary."""
    summaries = []
    for keyword, group in df.groupby('keyword'):
        g = group.sort_values('estimate_start_date').reset_index(drop=True)
        volumes = g['estimated_exact_search_volume']
        peak_idx = volumes.idxmax()
        min_idx = volumes.idxmin()
        mean_vol = volumes.mean()
        std_vol = volumes.std()
        cv = std_vol / mean_vol if mean_vol > 0 else 0.0

        ramp_up_start = _find_ramp_up_start(
            g['wow_change_pct'].values,
            g['estimate_start_date'].values,
        )

        # Ideal launch window: pre_peak_weeks before peak to 2 weeks before peak
        launch_start_idx = max(0, peak_idx - pre_peak_weeks)
        launch_end_idx = max(0, peak_idx - 2)
        launch_start = str(g.loc[launch_start_idx, 'estimate_start_date'])
        launch_end = str(g.loc[launch_end_idx, 'estimate_start_date'])
        weeks_until_peak = peak_idx - launch_start_idx

        min_vol = int(volumes.min())
        peak_vol = int(volumes.max())

        summaries.append({
            'keyword': keyword,
            'total_weeks': len(g),
            'demand_type': _classify_demand(cv),
            'stability_score': round(1.0 / (1.0 + cv), 3),
            'peak_volume': peak_vol,
            'peak_week': str(g.loc[peak_idx, 'estimate_start_date']),
            'ramp_up_start': ramp_up_start,
            'ideal_launch_window_start': launch_start,
            'ideal_launch_window_end': launch_end,
            'weeks_until_peak': weeks_until_peak,
            'trough_volume': min_vol,
            'peak_trough_ratio': round(peak_vol / min_vol, 2) if min_vol > 0 else float('inf'),
        })
    return pd.DataFrame(summaries)


def analyze_launch_timing(
    mcp_data,
    output_dir: str | None = None,
    keyword: str = '',
    pre_peak_weeks: int = 6,
) -> dict[str, Any]:
    """
    Process MCP response from js_historical_search_volume.

    Args:
        mcp_data:    Pre-fetched MCP response data.
        output_dir:  Directory for output CSVs.
        keyword:     The keyword label for rows.
        pre_peak_weeks: int = 6

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
            'launch_timing_csv': '',
            'launch_summary_csv': '',
        }

    df = pd.DataFrame(all_rows)
    df = _add_launch_columns(df)

    csv_path = os.path.join(data_dir, 'launch_timing.csv')
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')

    summary_path = os.path.join(data_dir, 'launch_summary.csv')
    summary_df = _compute_launch_summary(df, pre_peak_weeks)
    summary_df.to_csv(summary_path, index=False, encoding='utf-8-sig')

    return {
        'output_dir': data_dir,
        'total_rows': len(df),
        'columns': list(df.columns),
        'launch_timing_csv': csv_path,
        'launch_summary_csv': summary_path,
    }

