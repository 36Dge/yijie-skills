"""
Revenue Estimation & Financial Modeling — MCP data processing (js_sales_estimates).

Combines daily estimated units sold with pricing data to build revenue
timelines.  Computes daily / weekly / monthly revenue, cumulative revenue,
MA7, revenue share across ASINs, and trend direction.


"""

from __future__ import annotations

import json as _json
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
MA_WINDOW = 7
TREND_THRESHOLD = 0.10  # ±10 % to classify growing / declining


def _add_revenue_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Add daily_revenue, ma7_revenue, cumulative_revenue, week, month."""
    result_frames = []
    for asin, group in df.groupby('asin'):
        g = group.sort_values('date').copy()

        # Daily revenue
        g['daily_revenue'] = (g['estimated_units_sold'] * g['price']).round(2)

        # 7-day moving average revenue
        g['ma7_revenue'] = (
            g['daily_revenue']
            .rolling(window=MA_WINDOW, min_periods=1)
            .mean()
            .round(2)
        )

        # Cumulative revenue
        g['cumulative_revenue'] = g['daily_revenue'].cumsum().round(2)

        result_frames.append(g)

    df = pd.concat(result_frames, ignore_index=True)

    # Week and month labels
    dates = pd.to_datetime(df['date'])
    df['week'] = dates.dt.strftime('%G-W%V')
    df['month'] = dates.dt.strftime('%Y-%m')

    return df


def _determine_trend(daily_revenues: pd.Series) -> str:
    """Classify revenue trend as growing / declining / stable.

    Compares mean daily revenue of the first half vs second half.
    """
    n = len(daily_revenues)
    if n < 4:
        return 'stable'
    mid = n // 2
    first_half = daily_revenues.iloc[:mid].mean()
    second_half = daily_revenues.iloc[mid:].mean()
    if first_half == 0:
        return 'growing' if second_half > 0 else 'stable'
    change = (second_half - first_half) / first_half
    if change > TREND_THRESHOLD:
        return 'growing'
    if change < -TREND_THRESHOLD:
        return 'declining'
    return 'stable'


def _compute_revenue_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Compute per-ASIN revenue summary."""
    grand_total_revenue = df['daily_revenue'].sum()

    summaries = []
    for asin, group in df.groupby('asin'):
        g = group.sort_values('date').reset_index(drop=True)
        rev = g['daily_revenue']
        units = g['estimated_units_sold']
        prices = g['price']

        total_revenue = round(float(rev.sum()), 2)
        total_units = int(units.sum())
        peak_idx = rev.idxmax()

        # Monthly average revenue
        monthly_rev = g.groupby('month')['daily_revenue'].sum()
        monthly_avg = round(float(monthly_rev.mean()), 2) if len(monthly_rev) > 0 else 0.0

        # Revenue share
        share = round(total_revenue / grand_total_revenue * 100, 2) if grand_total_revenue > 0 else 0.0

        # Trend
        trend = _determine_trend(rev)

        summaries.append({
            'asin': asin,
            'total_days': len(g),
            'total_revenue': total_revenue,
            'total_units': total_units,
            'mean_daily_revenue': round(float(rev.mean()), 2),
            'mean_price': round(float(prices.mean()), 2),
            'peak_daily_revenue': round(float(rev.max()), 2),
            'peak_date': str(g.loc[peak_idx, 'date']),
            'monthly_avg_revenue': monthly_avg,
            'revenue_share_pct': share,
            'revenue_trend': trend,
        })

    return pd.DataFrame(summaries)


def analyze_revenue(
    mcp_data,
    output_dir: str | None = None,
    asin: str = '',
) -> dict[str, Any]:
    """Process MCP response from js_sales_estimates for revenue modeling."""
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
                'columns': [], 'revenue_daily_csv': '', 'revenue_summary_csv': ''}

    df = pd.DataFrame(all_rows)
    df = _add_revenue_columns(df)

    csv_path = os.path.join(data_dir, 'revenue_daily.csv')
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')

    summary_df = _compute_revenue_summary(df)
    summary_path = os.path.join(data_dir, 'revenue_summary.csv')
    summary_df.to_csv(summary_path, index=False, encoding='utf-8-sig')

    return {
        'output_dir': data_dir, 'total_rows': len(df),
        'rows_per_asin': {asin: len(all_rows)},
        'columns': list(df.columns),
        'revenue_daily_csv': csv_path, 'revenue_summary_csv': summary_path,
    }

