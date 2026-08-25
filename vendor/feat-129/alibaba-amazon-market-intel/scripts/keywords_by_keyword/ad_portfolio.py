"""
Ad Keyword Portfolio — Based on MCP data processing (js_keywords_by_keyword).

Assign match types by relevancy score, build campaign architecture by CPC tier,
and identify Sponsored Brands (SB) ad opportunities.

Usage:
  import sys
  sys.path.insert(0, '/home/wuying/skills/ad-keyword-portfolio/scripts')
  from ad_portfolio import build_ad_portfolio
  result = build_ad_portfolio(
      seed_keywords=["yoga mat"],
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


EXACT_MATCH_THRESHOLD = 100   # relevancy_score > 100 → exact match
PHRASE_MATCH_MIN = 60         # 60-100 → phrase match
CPC_HIGH_THRESHOLD = 3.0
CPC_LOW_THRESHOLD = 1.0


def _match_type(relevancy: float) -> str:
    if relevancy > EXACT_MATCH_THRESHOLD:
        return 'Exact'
    if relevancy >= PHRASE_MATCH_MIN:
        return 'Phrase'
    return 'Broad'


def _cpc_tier(bid: float | None) -> str:
    if bid is None:
        return 'N/A'
    if bid >= CPC_HIGH_THRESHOLD:
        return 'HIGH'
    if bid >= CPC_LOW_THRESHOLD:
        return 'MID'
    return 'LOW'


def _campaign_name(match_type: str, cpc_tier: str) -> str:
    mt_map = {'Exact': 'Exact', 'Phrase': 'Phrase', 'Broad': 'Broad'}
    mt = mt_map.get(match_type, match_type)
    if cpc_tier == 'N/A':
        return f'SP_{mt}_NoBid'
    return f'SP_{mt}_{cpc_tier}CPC'


def build_ad_portfolio(
    mcp_data,
    output_dir: str | None = None,
    seed_keyword: str = '',
) -> dict[str, Any]:
    """Process MCP response from js_keywords_by_keyword. Build a tiered ad keyword portfolio."""
    items = _unwrap_response(mcp_data)
    data_dir = output_dir or '.'
    os.makedirs(data_dir, exist_ok=True)

    all_rows = []
    for item in (items or []):
        attrs = item.get('attributes', item)
        row = {'seed_keyword': seed_keyword}
        row.update(attrs)
        all_rows.append(row)

    if not all_rows:
        return {'output_dir': data_dir, 'total_keywords': 0,
                'sb_opportunity_keywords': [], 'campaign_count': 0,
                'ad_keyword_portfolio_csv': '', 'campaign_structure_csv': ''}

    df = pd.DataFrame(all_rows)

    rs = 'relevancy_score'
    bid_e = 'ppc_bid_exact'
    sb = 'sp_brand_ad_bid'

    df[rs] = pd.to_numeric(df.get(rs, 0), errors='coerce').fillna(0)
    df[bid_e] = pd.to_numeric(df.get(bid_e, None), errors='coerce')

    df['match_type'] = df[rs].apply(_match_type)
    df['cpc_tier'] = df[bid_e].apply(_cpc_tier)
    df['suggested_campaign'] = df.apply(
        lambda r: _campaign_name(r['match_type'], r['cpc_tier']), axis=1
    )
    df['sb_opportunity'] = df[sb].apply(
        lambda v: bool(pd.notna(v) and float(v or 0) > 0)
    ) if sb in df.columns else False

    portfolio_cols = ['seed_keyword', 'name', 'monthly_search_volume_exact',
                      rs, bid_e, 'ppc_bid_broad', sb,
                      'match_type', 'cpc_tier', 'suggested_campaign', 'sb_opportunity']
    portfolio_df = df[[c for c in portfolio_cols if c in df.columns]].copy()
    portfolio_df = portfolio_df.sort_values(rs, ascending=False)

    portfolio_path = os.path.join(data_dir, 'ad_keyword_portfolio.csv')
    portfolio_df.to_csv(portfolio_path, index=False, encoding='utf-8-sig')

    ev = 'monthly_search_volume_exact'
    campaign_rows = []
    for camp, g in df.groupby('suggested_campaign'):
        mt = g['match_type'].iloc[0]
        ct = g['cpc_tier'].iloc[0]
        avg_bid = g[bid_e].mean() if bid_e in g.columns else None
        campaign_rows.append({
            'campaign_name': camp, 'match_type': mt, 'cpc_tier': ct,
            'keyword_count': len(g),
            'avg_bid': round(avg_bid, 2) if avg_bid is not None and not pd.isna(avg_bid) else None,
            'total_volume': int(g[ev].sum()) if ev in g.columns else 0,
        })
    camp_df = pd.DataFrame(campaign_rows).sort_values('total_volume', ascending=False)
    camp_path = os.path.join(data_dir, 'campaign_structure.csv')
    camp_df.to_csv(camp_path, index=False, encoding='utf-8-sig')

    sb_kws = portfolio_df[portfolio_df['sb_opportunity'] == True]['name'].tolist()[:10] if 'sb_opportunity' in portfolio_df.columns else []

    return {
        'output_dir': data_dir,
        'total_keywords': len(portfolio_df),
        'sb_opportunity_keywords': sb_kws,
        'campaign_count': len(camp_df),
        'ad_keyword_portfolio_csv': portfolio_path,
        'campaign_structure_csv': camp_path,
    }

