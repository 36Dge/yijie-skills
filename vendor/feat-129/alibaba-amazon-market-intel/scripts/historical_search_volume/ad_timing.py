"""
Advertising Campaign Timing & Budget Allocation — MCP data processing (js_historical_search_volume).

Fetches weekly search volume, classifies each week into demand tiers
(high/medium/low), assigns budget weights and ad actions (boost/maintain/reduce),
and identifies the longest boost and reduce windows for campaign planning.


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
# Demand tier thresholds (percentage of peak)
HIGH_TIER_PCT = 70
LOW_TIER_PCT = 30
# Budget weights per tier
WEIGHT_HIGH = 1.5
WEIGHT_MEDIUM = 1.0
WEIGHT_LOW = 0.5


def _add_ad_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Add pct_of_peak, wow_change_pct, demand_tier, budget_weight, ad_action per keyword."""
    result_frames = []
    for keyword, group in df.groupby('keyword'):
        g = group.sort_values('estimate_start_date').copy()
        vol = g['estimated_exact_search_volume']
        peak = vol.max()

        # Percentage of peak
        g['pct_of_peak'] = (vol / peak * 100).round(1) if peak > 0 else 0.0

        # Week-over-week change %
        g['wow_change_pct'] = vol.pct_change().mul(100).round(2).fillna(0.0)

        # Demand tier
        g['demand_tier'] = g['pct_of_peak'].apply(
            lambda p: 'high' if p >= HIGH_TIER_PCT else ('low' if p < LOW_TIER_PCT else 'medium')
        )

        # Budget weight
        tier_weight = {'high': WEIGHT_HIGH, 'medium': WEIGHT_MEDIUM, 'low': WEIGHT_LOW}
        g['budget_weight'] = g['demand_tier'].map(tier_weight)

        # Ad action
        tier_action = {'high': 'boost', 'medium': 'maintain', 'low': 'reduce'}
        g['ad_action'] = g['demand_tier'].map(tier_action)

        result_frames.append(g)

    return pd.concat(result_frames, ignore_index=True)


def _find_longest_window(
    tiers: list[str],
    dates: list[str],
    target_tier: str,
) -> tuple[str, str]:
    """Find the longest consecutive run of target_tier and return (start_date, end_date)."""
    best_start = ''
    best_end = ''
    best_len = 0
    cur_start = 0
    cur_len = 0

    for i, tier in enumerate(tiers):
        if tier == target_tier:
            if cur_len == 0:
                cur_start = i
            cur_len += 1
            if cur_len > best_len:
                best_len = cur_len
                best_start = dates[cur_start]
                best_end = dates[i]
        else:
            cur_len = 0

    return best_start, best_end


def _compute_ad_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Compute per-keyword ad timing summary."""
    summaries = []
    for keyword, group in df.groupby('keyword'):
        g = group.sort_values('estimate_start_date').reset_index(drop=True)
        volumes = g['estimated_exact_search_volume']
        tiers = g['demand_tier'].tolist()
        dates = g['estimate_start_date'].tolist()

        high_weeks = tiers.count('high')
        medium_weeks = tiers.count('medium')
        low_weeks = tiers.count('low')
        total = len(tiers)

        boost_start, boost_end = _find_longest_window(tiers, dates, 'high')
        reduce_start, reduce_end = _find_longest_window(tiers, dates, 'low')

        peak_idx = volumes.idxmax()

        # Suggested budget split
        high_pct = round(high_weeks / total * WEIGHT_HIGH / (
            high_weeks * WEIGHT_HIGH + medium_weeks * WEIGHT_MEDIUM + low_weeks * WEIGHT_LOW
        ) * 100) if total > 0 else 0
        low_pct = round(low_weeks / total * WEIGHT_LOW / (
            high_weeks * WEIGHT_HIGH + medium_weeks * WEIGHT_MEDIUM + low_weeks * WEIGHT_LOW
        ) * 100) if total > 0 else 0
        medium_pct = 100 - high_pct - low_pct

        summaries.append({
            'keyword': keyword,
            'total_weeks': total,
            'high_demand_weeks': high_weeks,
            'medium_demand_weeks': medium_weeks,
            'low_demand_weeks': low_weeks,
            'high_demand_pct': round(high_weeks / total * 100, 1) if total > 0 else 0,
            'boost_window_start': boost_start,
            'boost_window_end': boost_end,
            'reduce_window_start': reduce_start,
            'reduce_window_end': reduce_end,
            'peak_volume': int(volumes.max()),
            'peak_week': str(g.loc[peak_idx, 'estimate_start_date']),
            'suggested_budget_split': f'high:{high_pct}% medium:{medium_pct}% low:{low_pct}%',
        })
    return pd.DataFrame(summaries)


def analyze_ad_timing(
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
            'ad_timing_csv': '',
            'ad_summary_csv': '',
        }

    df = pd.DataFrame(all_rows)
    df = _add_ad_columns(df)

    csv_path = os.path.join(data_dir, 'ad_timing.csv')
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')

    summary_path = os.path.join(data_dir, 'ad_summary.csv')
    summary_df = _compute_ad_summary(df)
    summary_df.to_csv(summary_path, index=False, encoding='utf-8-sig')

    return {
        'output_dir': data_dir,
        'total_rows': len(df),
        'columns': list(df.columns),
        'ad_timing_csv': csv_path,
        'ad_summary_csv': summary_path,
    }

