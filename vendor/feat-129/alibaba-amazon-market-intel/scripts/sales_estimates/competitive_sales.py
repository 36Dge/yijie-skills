"""
Competitive Sales Tracking — MCP data processing (js_sales_estimates).

Fetches daily estimated units sold and price for multiple ASINs,
computes market share, 7-day moving average, DoD change, promotion
spike detection, and price change signals for competitive benchmarking.


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
SPIKE_MULTIPLIER = 2.0
MA_WINDOW = 7


def _add_competitive_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Add market_share, ma7, dod_change, spike detection, price_changed columns."""
    result_frames = []
    for asin, group in df.groupby('asin'):
        g = group.sort_values('date').copy()
        units = g['estimated_units_sold']

        # 7-day moving average
        g['ma7_units'] = units.rolling(window=MA_WINDOW, min_periods=1).mean().round(1)

        # Day-over-day change %
        g['dod_change_pct'] = units.pct_change().mul(100).round(2).fillna(0.0)

        # Spike detection: daily units > MA7 * SPIKE_MULTIPLIER
        g['is_spike'] = units > (g['ma7_units'] * SPIKE_MULTIPLIER)

        # Price changed vs previous day
        g['price_changed'] = g['price'].ne(g['price'].shift(1)) & g['price'].shift(1).notna()

        result_frames.append(g)

    df = pd.concat(result_frames, ignore_index=True)

    # Market share: per day, each ASIN's units / total units across all ASINs
    daily_total = (
        df.groupby('date')['estimated_units_sold']
        .transform('sum')
    )
    df['market_share'] = (
        df['estimated_units_sold'] / daily_total.replace(0, float('nan')) * 100
    ).round(2).fillna(0.0)

    return df


def _compute_sales_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Compute per-ASIN competitive sales summary."""
    # Total units across all ASINs for market share calculation
    grand_total = df['estimated_units_sold'].sum()

    summaries = []
    for asin, group in df.groupby('asin'):
        g = group.sort_values('date').reset_index(drop=True)
        units = g['estimated_units_sold']
        prices = g['price']
        peak_idx = units.idxmax()

        total_units = int(units.sum())
        market_share_pct = round(total_units / grand_total * 100, 2) if grand_total > 0 else 0.0

        summaries.append({
            'asin': asin,
            'total_days': len(g),
            'total_units_sold': total_units,
            'mean_daily_units': round(units.mean(), 1),
            'peak_daily_units': int(units.max()),
            'peak_date': str(g.loc[peak_idx, 'date']),
            'mean_price': round(prices.mean(), 2),
            'price_range': f'{prices.min():.2f}–{prices.max():.2f}',
            'market_share_pct': market_share_pct,
            'spike_days': int(g['is_spike'].sum()),
            'price_change_count': int(g['price_changed'].sum()),
        })

    return pd.DataFrame(summaries)


def analyze_competitive_sales(
    mcp_data,
    output_dir: str | None = None,
    asin: str = '',
) -> dict[str, Any]:
    """Process MCP response from js_sales_estimates for competitive sales tracking."""
    items = _unwrap_response(mcp_data)
    data_dir = output_dir or '.'
    os.makedirs(data_dir, exist_ok=True)

    all_rows = []
    for item in (items or []):
        attrs = item.get('attributes', item)
        nested_data = attrs.get('data', None)
        if isinstance(nested_data, list):
            for daily in nested_data:
                row = {
                    'asin': asin,
                    'date': str(daily.get('date', '')),
                    'estimated_units_sold': daily.get('estimated_units_sold', 0),
                    'price': daily.get('last_known_price') or 0.0,
                }
                all_rows.append(row)
        else:
            row = {
                'asin': asin,
                'date': str(attrs.get('date', '')),
                'estimated_units_sold': attrs.get('estimated_units_sold', 0),
                'price': attrs.get('last_known_price') or 0.0,
            }
            all_rows.append(row)

    if not all_rows:
        return {'output_dir': data_dir, 'total_rows': 0, 'rows_per_asin': {asin: 0},
                'columns': [], 'competitive_sales_csv': '', 'sales_summary_csv': ''}

    df = pd.DataFrame(all_rows)
    df = _add_competitive_columns(df)

    csv_path = os.path.join(data_dir, 'competitive_sales.csv')
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')

    summary_df = _compute_sales_summary(df)
    summary_path = os.path.join(data_dir, 'sales_summary.csv')
    summary_df.to_csv(summary_path, index=False, encoding='utf-8-sig')

    return {
        'output_dir': data_dir, 'total_rows': len(df),
        'rows_per_asin': {asin: len(all_rows)},
        'columns': list(df.columns),
        'competitive_sales_csv': csv_path, 'sales_summary_csv': summary_path,
    }

