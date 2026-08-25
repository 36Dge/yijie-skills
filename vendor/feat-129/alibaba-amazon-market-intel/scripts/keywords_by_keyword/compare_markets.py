"""
Cross-Market Comparison — Based on MCP data processing (js_keywords_by_keyword).

Run the same seed keywords across multiple marketplaces, compare demand levels,
bid prices, and ranking difficulty to identify optimal expansion markets.

Usage:
  import sys
  sys.path.insert(0, '/home/wuying/skills/cross-market-comparison/scripts')
  from compare_markets import compare_markets
  result = compare_markets(
      seed_keywords=["yoga mat"],
      marketplaces=["US", "UK", "DE"],
      output_dir="/home/wuying/accio/round-1/data",
  )
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


# Jungle Scout SDK Marketplace enum mapping


def compare_markets(
    mcp_data,
    output_dir: str | None = None,
    seed_keyword: str = '',
    marketplace: str = '',
) -> dict[str, Any]:
    """
    Process MCP response from js_keywords_by_keyword (cross-market).
    Compare demand across marketplaces.

    Args:
        mcp_data:      Pre-fetched MCP response data (items should include marketplace field).
        output_dir:    Directory for CSV output.
        seed_keyword:  Seed keyword label.
        marketplace:   Marketplace code (e.g. 'US').
    """
    items = _unwrap_response(mcp_data)
    data_dir = output_dir or '.'
    os.makedirs(data_dir, exist_ok=True)

    all_rows = []
    for item in (items or []):
        attrs = item.get('attributes', item)
        row = {'seed_keyword': seed_keyword, 'marketplace': marketplace}
        row.update(attrs)
        all_rows.append(row)

    if not all_rows:
        return {'output_dir': data_dir, 'total_rows': 0,
                'best_market_per_seed': {}, 'opportunity_markets': [],
                'market_summary_csv': '', 'cross_market_raw_csv': ''}

    df = pd.DataFrame(all_rows)
    ev = 'monthly_search_volume_exact'
    bid_e = 'ppc_bid_exact'
    er = 'ease_of_ranking_score'
    for col in [ev, bid_e, er]:
        df[col] = pd.to_numeric(df.get(col, None), errors='coerce')

    raw_path = os.path.join(data_dir, 'cross_market_raw.csv')
    df.to_csv(raw_path, index=False, encoding='utf-8-sig')

    summary_rows = []
    for (seed, mkt), g in df.groupby(['seed_keyword', 'marketplace']):
        avg_vol = g[ev].mean() if ev in g.columns else 0
        total_vol = int(g[ev].sum()) if ev in g.columns else 0
        avg_bid = g[bid_e].mean() if bid_e in g.columns else 0
        avg_ease = g[er].mean() if er in g.columns else 0
        opp_score = total_vol / (1 + (avg_bid or 0))
        summary_rows.append({
            'seed_keyword': seed, 'marketplace': mkt,
            'keyword_count': len(g),
            'avg_exact_volume': round(avg_vol, 1),
            'total_exact_volume': total_vol,
            'avg_ppc_bid_exact': round(avg_bid, 2) if not pd.isna(avg_bid) else None,
            'avg_ease_of_ranking': round(avg_ease, 1) if not pd.isna(avg_ease) else None,
            'opportunity_score': round(opp_score, 1),
        })

    sum_df = pd.DataFrame(summary_rows)
    if not sum_df.empty:
        sum_df['market_rank'] = sum_df.groupby('seed_keyword')['opportunity_score'].rank(
            ascending=False, method='min').astype(int)
        sum_df = sum_df.sort_values(['seed_keyword', 'market_rank'])

    sum_path = os.path.join(data_dir, 'market_summary.csv')
    sum_df.to_csv(sum_path, index=False, encoding='utf-8-sig')

    best_per_seed = (
        sum_df[sum_df['market_rank'] == 1].set_index('seed_keyword')['marketplace'].to_dict()
    ) if not sum_df.empty else {}
    top_markets = (
        sum_df[sum_df['market_rank'] == 1]['marketplace'].value_counts().index.tolist()
    ) if not sum_df.empty else []

    return {
        'output_dir': data_dir,
        'total_rows': len(all_rows),
        'best_market_per_seed': best_per_seed,
        'opportunity_markets': top_markets,
        'market_summary_csv': sum_path,
        'cross_market_raw_csv': raw_path,
    }

