"""
Deal & Promotion Impact Measurement — MCP data processing (js_sales_estimates).

Compares daily sales during a promotional period against a pre-promo baseline
and a post-promo recovery window.  Computes lift %, discount %, incremental
units, and recovery-vs-baseline metrics for evidence-based deal evaluation.


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
DEFAULT_BASELINE_DAYS = 14
DEFAULT_RECOVERY_DAYS = 7


def _label_phase(date_str: str, promo_start: str, promo_end: str) -> str:
    """Return 'baseline', 'promo', or 'recovery' for a given date."""
    if date_str < promo_start:
        return 'baseline'
    if date_str <= promo_end:
        return 'promo'
    return 'recovery'


def _add_impact_columns(
    df: pd.DataFrame,
    promo_start: str,
    promo_end: str,
) -> pd.DataFrame:
    """Add phase labels, baseline references, lift %, discount %, MA7."""
    result_frames = []
    for asin, group in df.groupby('asin'):
        g = group.sort_values('date').copy()

        # Phase label
        g['phase'] = g['date'].apply(lambda d: _label_phase(d, promo_start, promo_end))

        # 7-day moving average
        g['ma7_units'] = (
            g['estimated_units_sold']
            .rolling(window=MA_WINDOW, min_periods=1)
            .mean()
            .round(1)
        )

        # Baseline averages
        baseline_mask = g['phase'] == 'baseline'
        baseline_units = g.loc[baseline_mask, 'estimated_units_sold']
        baseline_prices = g.loc[baseline_mask, 'price']

        baseline_avg_units = round(float(baseline_units.mean()), 1) if len(baseline_units) > 0 else 0.0
        baseline_avg_price = round(float(baseline_prices.mean()), 2) if len(baseline_prices) > 0 else 0.0

        g['baseline_avg_units'] = baseline_avg_units
        g['baseline_avg_price'] = baseline_avg_price

        # Lift %: (daily_units - baseline_avg) / baseline_avg * 100
        g['lift_pct'] = (
            ((g['estimated_units_sold'] - baseline_avg_units) / baseline_avg_units * 100).round(1)
            if baseline_avg_units > 0 else 0.0
        )

        # Discount %: (baseline_avg_price - daily_price) / baseline_avg_price * 100
        # Positive = price is lower than baseline (discount)
        g['discount_pct'] = (
            ((baseline_avg_price - g['price']) / baseline_avg_price * 100).round(1)
            if baseline_avg_price > 0 else 0.0
        )

        result_frames.append(g)

    return pd.concat(result_frames, ignore_index=True)


def _compute_promotion_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Compute per-ASIN promotion impact summary."""
    summaries = []
    for asin, group in df.groupby('asin'):
        g = group.sort_values('date').reset_index(drop=True)

        baseline = g[g['phase'] == 'baseline']
        promo = g[g['phase'] == 'promo']
        recovery = g[g['phase'] == 'recovery']

        baseline_avg_units = round(float(baseline['estimated_units_sold'].mean()), 1) if len(baseline) > 0 else 0.0
        promo_avg_units = round(float(promo['estimated_units_sold'].mean()), 1) if len(promo) > 0 else 0.0
        recovery_avg_units = round(float(recovery['estimated_units_sold'].mean()), 1) if len(recovery) > 0 else 0.0

        baseline_avg_price = round(float(baseline['price'].mean()), 2) if len(baseline) > 0 else 0.0
        promo_avg_price = round(float(promo['price'].mean()), 2) if len(promo) > 0 else 0.0

        # Lift
        promo_lift_pct = (
            round((promo_avg_units - baseline_avg_units) / baseline_avg_units * 100, 1)
            if baseline_avg_units > 0 else 0.0
        )

        # Recovery vs baseline
        recovery_vs_baseline_pct = (
            round((recovery_avg_units - baseline_avg_units) / baseline_avg_units * 100, 1)
            if baseline_avg_units > 0 else 0.0
        )

        # Discount stats
        avg_discount_pct = (
            round((baseline_avg_price - promo_avg_price) / baseline_avg_price * 100, 1)
            if baseline_avg_price > 0 else 0.0
        )
        max_discount_pct = 0.0
        if len(promo) > 0 and baseline_avg_price > 0:
            max_discount_pct = round(
                float(((baseline_avg_price - promo['price'].min()) / baseline_avg_price * 100)), 1
            )

        # Incremental units
        promo_total = int(promo['estimated_units_sold'].sum()) if len(promo) > 0 else 0
        expected_units = round(baseline_avg_units * len(promo))
        incremental_units = promo_total - expected_units

        summaries.append({
            'asin': asin,
            'baseline_days': len(baseline),
            'promo_days': len(promo),
            'recovery_days': len(recovery),
            'baseline_avg_units': baseline_avg_units,
            'promo_avg_units': promo_avg_units,
            'recovery_avg_units': recovery_avg_units,
            'promo_lift_pct': promo_lift_pct,
            'recovery_vs_baseline_pct': recovery_vs_baseline_pct,
            'baseline_avg_price': baseline_avg_price,
            'promo_avg_price': promo_avg_price,
            'avg_discount_pct': avg_discount_pct,
            'max_discount_pct': max_discount_pct,
            'incremental_units': incremental_units,
            'total_promo_units': promo_total,
        })

    return pd.DataFrame(summaries)


def analyze_promotion_impact(
    mcp_data,
    promo_start: str = '',
    promo_end: str = '',
    output_dir: str | None = None,
    asin: str = '',
) -> dict[str, Any]:
    """Process MCP response from js_sales_estimates for promotion impact measurement."""
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
                'columns': [], 'promotion_impact_csv': '', 'promotion_summary_csv': ''}

    df = pd.DataFrame(all_rows)
    df = _add_impact_columns(df, promo_start, promo_end)

    csv_path = os.path.join(data_dir, 'promotion_impact.csv')
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')

    summary_df = _compute_promotion_summary(df)
    summary_path = os.path.join(data_dir, 'promotion_summary.csv')
    summary_df.to_csv(summary_path, index=False, encoding='utf-8-sig')

    return {
        'output_dir': data_dir, 'total_rows': len(df),
        'rows_per_asin': {asin: len(all_rows)},
        'columns': list(df.columns),
        'promotion_impact_csv': csv_path, 'promotion_summary_csv': summary_path,
    }

