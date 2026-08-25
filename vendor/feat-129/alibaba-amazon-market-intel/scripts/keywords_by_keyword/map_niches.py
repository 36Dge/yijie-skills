"""
Category & Niche Mapping — MCP data processing (js_keywords_by_keyword).

Group keywords by dominant_category, map competition density, identify low-competition
sub-niches and cross-category opportunities.

Usage:
  import sys
  sys.path.insert(0, '/home/wuying/skills/category-niche-mapping/scripts')
  from map_niches import map_niches
  result = map_niches(
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


# Competition density thresholds (based on sponsored_product_count)
COMPETITION_LOW = 5
COMPETITION_HIGH = 20


def _competition_level(avg_sponsored: float) -> str:
    if avg_sponsored < COMPETITION_LOW:
        return 'LOW'
    if avg_sponsored <= COMPETITION_HIGH:
        return 'MEDIUM'
    return 'HIGH'


def map_niches(
    mcp_data,
    output_dir: str | None = None,
    seed_keyword: str = '',
) -> dict[str, Any]:
    """Process MCP response from js_keywords_by_keyword. Group keywords by dominant_category."""
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
                'category_summary_csv': '', 'keyword_by_category_csv': ''}

    df = pd.DataFrame(all_rows)

    if 'dominant_category' in df.columns and 'name' in df.columns:
        kw_cat_count = df.groupby('name')['dominant_category'].nunique()
        cross_cat_kws = set(kw_cat_count[kw_cat_count > 1].index)
        df['is_cross_category'] = df['name'].isin(cross_cat_kws)
    else:
        df['is_cross_category'] = False
        cross_cat_kws = set()

    kw_cols = ['seed_keyword', 'name', 'dominant_category',
               'monthly_search_volume_exact', 'sponsored_product_count',
               'ease_of_ranking_score', 'is_cross_category']
    kw_df = df[[c for c in kw_cols if c in df.columns]].copy()
    kw_path = os.path.join(data_dir, 'keyword_by_category.csv')
    kw_df.to_csv(kw_path, index=False, encoding='utf-8-sig')

    if 'dominant_category' in df.columns:
        grp = df.groupby('dominant_category')
        summary_rows = []
        for cat, g in grp:
            ev_col = 'monthly_search_volume_exact'
            sp_col = 'sponsored_product_count'
            er_col = 'ease_of_ranking_score'
            avg_sp = g[sp_col].mean() if sp_col in g.columns else 0
            def _top_kw(g):
                col = 'monthly_search_volume_exact'
                return g.loc[g[col].idxmax(), 'name'] if col in g.columns and not g[col].isna().all() else ''
            summary_rows.append({
                'dominant_category': cat, 'keyword_count': len(g),
                'total_exact_volume': g[ev_col].sum() if ev_col in g.columns else 0,
                'avg_exact_volume': round(g[ev_col].mean(), 1) if ev_col in g.columns else 0,
                'avg_sponsored_count': round(avg_sp, 1),
                'avg_ease_of_ranking': round(g[er_col].mean(), 1) if er_col in g.columns else 0,
                'top_keyword': _top_kw(g),
                'competition_level': _competition_level(avg_sp),
            })
        cat_df = pd.DataFrame(summary_rows).sort_values('total_exact_volume', ascending=False)
    else:
        cat_df = pd.DataFrame()

    cat_path = os.path.join(data_dir, 'category_summary.csv')
    cat_df.to_csv(cat_path, index=False, encoding='utf-8-sig')

    top_cats = cat_df['dominant_category'].tolist()[:5] if not cat_df.empty else []
    low_comp = cat_df[cat_df['competition_level'] == 'LOW']['dominant_category'].tolist() if not cat_df.empty else []

    return {
        'output_dir': data_dir,
        'total_rows': len(all_rows),
        'top_categories': top_cats,
        'low_competition_categories': low_comp,
        'cross_category_keywords': list(cross_cat_kws)[:20],
        'category_summary_csv': cat_path,
        'keyword_by_category_csv': kw_path,
    }

