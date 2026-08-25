"""
Content & SEO Strategy — Based on MCP data processing (js_keywords_by_keyword).

Calculate content priority scores and assign keywords to listing title, bullet points,
A+ content, and long-tail content modules.

Usage:
  import sys
  sys.path.insert(0, '/home/wuying/skills/content-seo-strategy/scripts')
  from content_seo import plan_content_seo
  result = plan_content_seo(
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


DEFAULT_MIN_EASE = 60


def _content_placement(row, title_threshold, bullet_threshold, min_ease):
    score = row.get('content_priority_score', 0)
    ease = row.get('ease_of_ranking_score', 0) or 0
    if score >= title_threshold:
        return 'Title Priority'
    if score >= bullet_threshold:
        return 'Bullet Priority'
    if ease >= min_ease:
        return 'A+ Topic'
    return 'Long-tail Opportunity'


def _recommended_action(placement: str) -> str:
    actions = {
        'Title Priority': 'Place in the first 80 characters of the product title, ensuring the keyword appears in full',
        'Bullet Priority': 'Include in the first three bullet points, using natural sentences to describe selling points',
        'A+ Topic': 'Use as the main heading or visual theme for an A+ content module, designing module content around this keyword',
        'Long-tail Opportunity': 'Use in brand storefront page descriptions or A+ detail supplements to improve long-tail coverage',
    }
    return actions.get(placement, '')


def plan_content_seo(
    mcp_data,
    output_dir: str | None = None,
    seed_keyword: str = '',
    min_ease_for_opportunity: int = DEFAULT_MIN_EASE,
) -> dict[str, Any]:
    """Process MCP response from js_keywords_by_keyword. Plan keyword priority and placement."""
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
        return {'output_dir': data_dir, 'total_rows': 0,
                'title_keywords': [], 'opportunity_keywords': [],
                'content_keyword_plan_csv': ''}

    df = pd.DataFrame(all_rows)
    ev = 'monthly_search_volume_exact'
    er = 'ease_of_ranking_score'

    df[ev] = pd.to_numeric(df.get(ev, 0), errors='coerce').fillna(0)
    df[er] = pd.to_numeric(df.get(er, 0), errors='coerce').fillna(0)
    df['content_priority_score'] = (df[ev] * (df[er] / 100.0)).round(1)

    scores = df['content_priority_score']
    title_thr = scores.quantile(0.90)
    bullet_thr = scores.quantile(0.70)

    df['content_placement'] = df.apply(
        lambda r: _content_placement(r, title_thr, bullet_thr, min_ease_for_opportunity), axis=1)
    df['recommended_action'] = df['content_placement'].map(_recommended_action)

    out_cols = ['seed_keyword', 'name', ev, er, 'content_priority_score',
                'content_placement', 'relevancy_score', 'recommended_action']
    out_df = df[[c for c in out_cols if c in df.columns]].copy()
    out_df = out_df.sort_values('content_priority_score', ascending=False)

    csv_path = os.path.join(data_dir, 'content_keyword_plan.csv')
    out_df.to_csv(csv_path, index=False, encoding='utf-8-sig')

    title_kws = out_df[out_df['content_placement'] == 'Title Priority']['name'].tolist()[:5]
    opp_kws = out_df[out_df['content_placement'] == 'A+ Topic']['name'].tolist()[:10]

    return {
        'output_dir': data_dir,
        'total_rows': len(all_rows),
        'title_keywords': title_kws,
        'opportunity_keywords': opp_kws,
        'content_keyword_plan_csv': csv_path,
    }

