"""
Pricing Strategy & Price Elasticity Analysis — MCP data processing (js_sales_estimates).

Fetches daily estimated units sold and price for ASINs, computes price
elasticity coefficients, detects promotional pricing patterns, calculates
promo uplift, and price-sales correlation for evidence-based pricing decisions.


"""

from __future__ import annotations

import json as _json
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


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MA_WINDOW = 7
DEFAULT_PROMO_THRESHOLD = 0.9
ELASTICITY_OUTLIER_LIMIT = 10.0


def _add_elasticity_columns(df: pd.DataFrame, promo_threshold: float) -> pd.DataFrame:
    """Add price/units change %, point elasticity, promo detection, MA7."""
    result_frames = []
    for asin, group in df.groupby('asin'):
        g = group.sort_values('date').copy()
        prices = g['price']
        units = g['estimated_units_sold']

        # Day-over-day change %
        g['price_change_pct'] = prices.pct_change().mul(100).round(2).fillna(0.0)
        g['units_change_pct'] = units.pct_change().mul(100).round(2).fillna(0.0)

        # Point elasticity = units_change_pct / price_change_pct
        # When price doesn't change, elasticity is 0 (undefined → 0)
        g['point_elasticity'] = np.where(
            g['price_change_pct'].abs() > 0.01,
            (g['units_change_pct'] / g['price_change_pct']).round(3),
            0.0,
        )

        # Promo detection: price < mean_price * promo_threshold
        mean_price = prices.mean()
        g['on_promo'] = prices < (mean_price * promo_threshold)

        # 7-day moving average
        g['ma7_units'] = units.rolling(window=MA_WINDOW, min_periods=1).mean().round(1)

        result_frames.append(g)

    return pd.concat(result_frames, ignore_index=True)


def _compute_pricing_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Compute per-ASIN pricing and elasticity summary."""
    summaries = []
    for asin, group in df.groupby('asin'):
        g = group.sort_values('date').reset_index(drop=True)
        prices = g['price']
        units = g['estimated_units_sold']

        # Filter extreme elasticity values for median calculation
        valid_e = g['point_elasticity'][
            (g['point_elasticity'] != 0.0) &
            (g['point_elasticity'].abs() <= ELASTICITY_OUTLIER_LIMIT)
        ]
        median_elasticity = round(float(valid_e.median()), 3) if len(valid_e) > 0 else 0.0

        # Price-sales Pearson correlation
        if len(g) >= 3 and prices.std() > 0 and units.std() > 0:
            corr = round(float(np.corrcoef(prices, units)[0, 1]), 3)
        else:
            corr = 0.0

        # Promo analysis
        promo_mask = g['on_promo']
        promo_days = int(promo_mask.sum())
        promo_pct = round(promo_days / len(g) * 100, 1) if len(g) > 0 else 0.0
        promo_avg = round(float(units[promo_mask].mean()), 1) if promo_days > 0 else 0.0
        non_promo_avg = round(float(units[~promo_mask].mean()), 1) if (~promo_mask).sum() > 0 else 0.0
        promo_uplift = (
            round((promo_avg - non_promo_avg) / non_promo_avg * 100, 1)
            if non_promo_avg > 0 and promo_days > 0 else 0.0
        )

        summaries.append({
            'asin': asin,
            'total_days': len(g),
            'mean_price': round(float(prices.mean()), 2),
            'price_range': f'{prices.min():.2f}–{prices.max():.2f}',
            'price_std': round(float(prices.std()), 2),
            'mean_daily_units': round(float(units.mean()), 1),
            'median_elasticity': median_elasticity,
            'price_sales_correlation': corr,
            'promo_days': promo_days,
            'promo_pct': promo_pct,
            'promo_avg_units': promo_avg,
            'non_promo_avg_units': non_promo_avg,
            'promo_uplift_pct': promo_uplift,
        })

    return pd.DataFrame(summaries)


def analyze_pricing_elasticity(
    mcp_data,
    output_dir: str | None = None,
    asin: str = '',
    promo_threshold: float = DEFAULT_PROMO_THRESHOLD,
) -> dict[str, Any]:
    """Process MCP response from js_sales_estimates for pricing elasticity analysis."""
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
                'columns': [], 'pricing_elasticity_csv': '', 'pricing_summary_csv': ''}

    df = pd.DataFrame(all_rows)
    df = _add_elasticity_columns(df, promo_threshold)

    csv_path = os.path.join(data_dir, 'pricing_elasticity.csv')
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')

    summary_df = _compute_pricing_summary(df)
    summary_path = os.path.join(data_dir, 'pricing_summary.csv')
    summary_df.to_csv(summary_path, index=False, encoding='utf-8-sig')

    return {
        'output_dir': data_dir, 'total_rows': len(df),
        'rows_per_asin': {asin: len(all_rows)},
        'columns': list(df.columns),
        'pricing_elasticity_csv': csv_path, 'pricing_summary_csv': summary_path,
    }

