"""
Search Volume Benchmark — Demand Validation Script.

Step 2–4 of the search-volume-benchmark skill:
  - Calls keywords_by_keyword for each product concept
  - Calls historical_search_volume for the top keyword per concept
  - Computes: exact/broad volume, specificity ratio, market size signal,
    YoY trend signal, and composite demand score
  - Ranks concepts by demand score
  - Outputs demand_benchmark.csv + volume_trend.csv


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


# Market size thresholds (exact monthly search volume)
_LARGE_THRESHOLD = 100_000
_MEDIUM_THRESHOLD = 10_000
_SMALL_THRESHOLD = 1_000

# Trend thresholds (YoY % change)
_GROWING_THRESHOLD = 10.0   # > +10% → GROWING
_DECLINING_THRESHOLD = -10.0  # < -10% → DECLINING

_BENCHMARK_COLS = [
    'rank',
    'product_concept',
    'primary_keyword',
    'exact_volume',
    'broad_volume',
    'specificity_ratio',
    'keyword_count',
    'market_size_signal',
    'trend_signal',
    'yoy_change_pct',
    'demand_score',
]

_TREND_COLS = [
    'product_concept',
    'keyword',
    'date',
    'estimated_exact_search_volume',
]


def _market_size_signal(exact_volume: int | None) -> str:
    if exact_volume is None:
        return 'INSUFFICIENT_DATA'
    if exact_volume >= _LARGE_THRESHOLD:
        return 'LARGE'
    if exact_volume >= _MEDIUM_THRESHOLD:
        return 'MEDIUM'
    if exact_volume >= _SMALL_THRESHOLD:
        return 'SMALL'
    return 'NICHE'


def _trend_signal(yoy_pct: float | None) -> str:
    if yoy_pct is None:
        return 'INSUFFICIENT_DATA'
    if yoy_pct > _GROWING_THRESHOLD:
        return 'GROWING'
    if yoy_pct < _DECLINING_THRESHOLD:
        return 'DECLINING'
    return 'STABLE'


def _demand_score(exact_volume: int | None, yoy_pct: float | None) -> float:
    """Composite demand score: volume adjusted by trend."""
    vol = exact_volume or 0
    adj = 1.0 + (yoy_pct / 100.0 if yoy_pct is not None else 0.0)
    return round(vol * adj, 2)


def _compute_yoy(monthly_series: list[dict]) -> float | None:
    """Compute YoY % change from a list of {date, estimated_exact_search_volume} dicts.

    Uses: recent_avg (last 3 months) vs prior_avg (months 10-12 from oldest).
    Returns None if not enough data points.
    """
    if len(monthly_series) < 6:
        return None

    # Sort by date ascending
    sorted_series = sorted(monthly_series, key=lambda r: r.get('date', ''))
    volumes = [r.get('estimated_exact_search_volume') or 0 for r in sorted_series]

    recent_avg = sum(volumes[-3:]) / 3
    prior_avg = sum(volumes[:3]) / 3

    if prior_avg == 0:
        return None
    return round((recent_avg - prior_avg) / prior_avg * 100, 2)


def benchmark_demand(
    mcp_kw_data,
    mcp_hsv_data=None,
    output_dir: str | None = None,
    product_concept: str = '',
) -> dict[str, Any]:
    """
    Process MCP responses from js_keywords_by_keyword and js_historical_search_volume.
    Benchmark search demand for a product concept.

    Args:
        mcp_kw_data:      MCP response from js_keywords_by_keyword.
        mcp_hsv_data:     MCP response from js_historical_search_volume (optional, for trend).
        output_dir:       Directory for CSV output.
        product_concept:  Product concept name for labeling.
    """
    data_dir = output_dir or '.'
    os.makedirs(data_dir, exist_ok=True)

    # Phase A: Process keyword data
    kw_items = _unwrap_response(mcp_kw_data)
    metrics = {
        'product_concept': product_concept,
        'primary_keyword': product_concept,
        'exact_volume': None, 'broad_volume': None,
        'specificity_ratio': None, 'keyword_count': 0,
        'market_size_signal': 'INSUFFICIENT_DATA',
        'trend_signal': 'INSUFFICIENT_DATA',
        'yoy_change_pct': None, 'demand_score': 0.0,
    }

    if kw_items:
        kw_rows_raw = []
        for item in kw_items:
            attrs = item.get('attributes', item)
            kw_rows_raw.append({
                'keyword': attrs.get('name') or attrs.get('keyword') or '',
                'exact': attrs.get('monthly_search_volume_exact') or 0,
                'broad': attrs.get('monthly_search_volume_broad') or 0,
            })
        metrics['keyword_count'] = len(kw_rows_raw)
        primary = max(kw_rows_raw, key=lambda r: r['exact'])
        metrics['primary_keyword'] = primary['keyword'] or product_concept
        metrics['exact_volume'] = primary['exact'] or None
        metrics['broad_volume'] = primary['broad'] or None
        if metrics['broad_volume'] and metrics['broad_volume'] > 0:
            metrics['specificity_ratio'] = round(
                (metrics['exact_volume'] or 0) / metrics['broad_volume'], 4)
        metrics['market_size_signal'] = _market_size_signal(metrics['exact_volume'])

    # Phase B: Process historical trend data
    trend_rows = []
    monthly_series = []
    if mcp_hsv_data:
        hsv_items = _unwrap_response(mcp_hsv_data)
        for item in (hsv_items or []):
            attrs = item.get('attributes', item)
            monthly_series.append({
                'date': attrs.get('date'),
                'estimated_exact_search_volume': attrs.get('estimated_exact_search_volume'),
            })
            trend_rows.append({
                'product_concept': product_concept,
                'keyword': metrics['primary_keyword'],
                'date': attrs.get('date'),
                'estimated_exact_search_volume': attrs.get('estimated_exact_search_volume'),
            })

    yoy = _compute_yoy(monthly_series)
    metrics['yoy_change_pct'] = yoy
    metrics['trend_signal'] = _trend_signal(yoy)
    metrics['demand_score'] = _demand_score(metrics['exact_volume'], yoy)
    metrics['rank'] = 1

    benchmark_csv = os.path.join(data_dir, 'demand_benchmark.csv')
    pd.DataFrame([metrics], columns=_BENCHMARK_COLS).to_csv(
        benchmark_csv, index=False, encoding='utf-8-sig')

    trend_csv = os.path.join(data_dir, 'volume_trend.csv')
    pd.DataFrame(trend_rows, columns=_TREND_COLS).to_csv(
        trend_csv, index=False, encoding='utf-8-sig')

    return {
        'output_dir': data_dir,
        'concepts': [metrics],
        'ranked_concepts': [product_concept],
        'demand_benchmark_csv': benchmark_csv,
        'volume_trend_csv': trend_csv,
    }

