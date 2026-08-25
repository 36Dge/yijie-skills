"""
PPC Bid Strategy Script — MCP data processing (js_keywords_by_keyword).

Step 2–5 of the ppc-bid-strategy skill:
  - Collects PPC bid data for all seed keywords via keywords_by_keyword
  - Deduplicates across seeds
  - Computes CPC efficiency, estimated monthly spend, bid tier
  - Classifies each keyword: Quick Win / Competitive / Long-tail / High-Spend
  - Builds budget forecast (conservative / moderate / aggressive)
  - Outputs bid_strategy.csv + budget_forecast.csv


"""

from __future__ import annotations

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


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DEFAULT_CTR = 0.05          # 5% assumed click-through rate
DEFAULT_TARGET_CLICKS = 1000

# Bid tier thresholds (USD)
_BID_LOW_MAX = 1.00
_BID_MID_MAX = 3.00

# Category thresholds (percentile-based, computed at runtime)
_HIGH_VOL_PERCENTILE = 67    # top 33% by volume
_LOW_CPC_PERCENTILE = 33     # bottom 33% by bid

_STRATEGY_COLS = [
    'keyword',
    'seed_keyword',
    'exact_volume',
    'ppc_bid_exact',
    'ease_of_ranking_score',
    'organic_product_count',
    'cpc_efficiency',
    'estimated_monthly_spend',
    'bid_tier',
    'keyword_category',
]

_FORECAST_COLS = ['metric', 'value']


def _bid_tier(bid: float | None) -> str:
    if bid is None:
        return 'N/A'
    if bid < _BID_LOW_MAX:
        return 'LOW'
    if bid <= _BID_MID_MAX:
        return 'MID'
    return 'HIGH'


def _classify_keywords(rows: list[dict]) -> list[dict]:
    """Assign keyword_category using volume and bid percentile thresholds.

    Categories:
      - Quick Win    : high volume + low CPC  → prioritize for ROI
      - Competitive  : high volume + high CPC → brand awareness only
      - Long-tail    : lower volume + low CPC → niche targeting
      - High-Spend   : any volume + high CPC  → avoid unless brand-building
      - NO_BID_DATA  : ppc_bid_exact is None
    """
    # Filter rows that have both volume and bid for percentile computation
    valid = [r for r in rows if r['exact_volume'] and r['ppc_bid_exact']]
    if not valid:
        for r in rows:
            r['keyword_category'] = 'NO_BID_DATA' if not r['ppc_bid_exact'] else 'Long-tail'
        return rows

    volumes = sorted(r['exact_volume'] for r in valid)
    bids = sorted(r['ppc_bid_exact'] for r in valid)

    n = len(valid)
    high_vol_threshold = volumes[int(n * _HIGH_VOL_PERCENTILE / 100)]
    low_cpc_threshold = bids[int(n * _LOW_CPC_PERCENTILE / 100)]

    for r in rows:
        if r['ppc_bid_exact'] is None:
            r['keyword_category'] = 'NO_BID_DATA'
            continue
        is_high_vol = (r['exact_volume'] or 0) >= high_vol_threshold
        is_low_cpc = r['ppc_bid_exact'] <= low_cpc_threshold
        is_high_cpc = r['ppc_bid_exact'] > _BID_MID_MAX

        if is_high_vol and is_low_cpc:
            r['keyword_category'] = 'Quick Win'
        elif is_high_vol and is_high_cpc:
            r['keyword_category'] = 'Competitive'
        elif is_high_cpc:
            r['keyword_category'] = 'High-Spend'
        else:
            r['keyword_category'] = 'Long-tail'

    return rows


def _build_budget_forecast(
    rows: list[dict],
    target_monthly_clicks: int,
) -> list[dict]:
    """Compute budget forecast metrics from classified keyword rows."""
    rows_with_bid = [r for r in rows if r['ppc_bid_exact'] is not None]
    quick_wins = [r for r in rows if r.get('keyword_category') == 'Quick Win']

    # Total addressable spend = sum of all estimated monthly spend
    total_addressable = sum(r['estimated_monthly_spend'] or 0 for r in rows_with_bid)

    # Volume-weighted average CPC
    total_vol = sum(r['exact_volume'] or 0 for r in rows_with_bid)
    if total_vol > 0:
        weighted_avg_cpc = sum(
            (r['exact_volume'] or 0) * (r['ppc_bid_exact'] or 0)
            for r in rows_with_bid
        ) / total_vol
    else:
        weighted_avg_cpc = 0.0

    # Budget forecast for target clicks
    budget_moderate = round(target_monthly_clicks * weighted_avg_cpc, 2)
    budget_conservative = round(budget_moderate * 0.5, 2)
    budget_aggressive = round(budget_moderate * 2.0, 2)

    # Top Quick Win keywords by efficiency
    qw_sorted = sorted(quick_wins, key=lambda r: r['cpc_efficiency'] or 0, reverse=True)
    top_qw_names = ', '.join(r['keyword'] for r in qw_sorted[:10])

    return [
        {'metric': 'total_keywords_analyzed', 'value': str(len(rows))},
        {'metric': 'keywords_with_bid_data', 'value': str(len(rows_with_bid))},
        {'metric': 'quick_win_keyword_count', 'value': str(len(quick_wins))},
        {'metric': 'total_addressable_spend_usd', 'value': f'${total_addressable:,.2f}'},
        {'metric': 'weighted_avg_cpc_usd', 'value': f'${weighted_avg_cpc:.2f}'},
        {'metric': f'budget_conservative_usd (target={target_monthly_clicks} clicks/mo)',
         'value': f'${budget_conservative:,.2f}'},
        {'metric': f'budget_moderate_usd (target={target_monthly_clicks} clicks/mo)',
         'value': f'${budget_moderate:,.2f}'},
        {'metric': f'budget_aggressive_usd (target={target_monthly_clicks} clicks/mo)',
         'value': f'${budget_aggressive:,.2f}'},
        {'metric': 'top_quick_win_keywords', 'value': top_qw_names or 'N/A'},
    ]


def analyze_ppc_bids(
    mcp_data,
    output_dir: str | None = None,
    seed_keyword: str = '',
    assumed_ctr: float = DEFAULT_CTR,
    target_monthly_clicks: int = DEFAULT_TARGET_CLICKS,
) -> dict[str, Any]:
    """Process MCP response from js_keywords_by_keyword. Analyze PPC bid landscape."""
    items = _unwrap_response(mcp_data)
    data_dir = output_dir or '.'
    os.makedirs(data_dir, exist_ok=True)

    all_rows = []
    seen_keywords = set()
    for item in (items or []):
        attrs = item.get('attributes', item)
        keyword_text = (attrs.get('name') or attrs.get('keyword') or '').strip().lower()
        if not keyword_text or keyword_text in seen_keywords:
            continue
        seen_keywords.add(keyword_text)
        exact_vol = attrs.get('monthly_search_volume_exact') or 0
        bid = attrs.get('ppc_bid_exact')
        cpc_efficiency = round(exact_vol / bid, 2) if (bid and bid > 0) else None
        est_spend = round(exact_vol * assumed_ctr * bid, 2) if (bid and bid > 0) else None
        all_rows.append({
            'keyword': keyword_text, 'seed_keyword': seed_keyword,
            'exact_volume': exact_vol or None, 'ppc_bid_exact': bid,
            'ease_of_ranking_score': attrs.get('ease_of_ranking_score'),
            'organic_product_count': attrs.get('organic_product_count'),
            'cpc_efficiency': cpc_efficiency, 'estimated_monthly_spend': est_spend,
            'bid_tier': _bid_tier(bid), 'keyword_category': None,
        })

    if not all_rows:
        return {
            'output_dir': data_dir, 'total_keywords': 0, 'quick_win_count': 0,
            'weighted_avg_cpc': 0.0, 'total_addressable_spend': 0.0,
            'budget_moderate_usd': 0.0, 'top_quick_win_keywords': [],
            'bid_strategy_csv': '', 'budget_forecast_csv': '',
        }

    all_rows = _classify_keywords(all_rows)
    forecast_rows = _build_budget_forecast(all_rows, target_monthly_clicks)

    def sort_key(r):
        cat_order = {'Quick Win': 0, 'Long-tail': 1, 'Competitive': 2, 'High-Spend': 3, 'NO_BID_DATA': 4}
        return (cat_order.get(r.get('keyword_category', ''), 5), -(r.get('cpc_efficiency') or 0))
    all_rows.sort(key=sort_key)

    strategy_csv = os.path.join(data_dir, 'bid_strategy.csv')
    pd.DataFrame(all_rows, columns=_STRATEGY_COLS).to_csv(strategy_csv, index=False, encoding='utf-8-sig')

    forecast_csv = os.path.join(data_dir, 'budget_forecast.csv')
    pd.DataFrame(forecast_rows, columns=_FORECAST_COLS).to_csv(forecast_csv, index=False, encoding='utf-8-sig')

    rows_with_bid = [r for r in all_rows if r['ppc_bid_exact'] is not None]
    total_vol = sum(r['exact_volume'] or 0 for r in rows_with_bid)
    weighted_avg_cpc = (
        sum((r['exact_volume'] or 0) * (r['ppc_bid_exact'] or 0) for r in rows_with_bid) / total_vol
        if total_vol > 0 else 0.0)
    total_addressable = sum(r['estimated_monthly_spend'] or 0 for r in rows_with_bid)
    quick_wins = [r for r in all_rows if r.get('keyword_category') == 'Quick Win']
    top_qw = sorted(quick_wins, key=lambda r: r.get('cpc_efficiency') or 0, reverse=True)

    return {
        'output_dir': data_dir, 'total_keywords': len(all_rows),
        'quick_win_count': len(quick_wins),
        'weighted_avg_cpc': round(weighted_avg_cpc, 4),
        'total_addressable_spend': round(total_addressable, 2),
        'budget_moderate_usd': round(target_monthly_clicks * weighted_avg_cpc, 2),
        'top_quick_win_keywords': [r['keyword'] for r in top_qw[:10]],
        'bid_strategy_csv': strategy_csv,
        'budget_forecast_csv': forecast_csv,
    }

