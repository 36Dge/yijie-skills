"""
Competitor Keyword Gap Analysis Script — MCP data processing (js_keywords_by_asin).

Collect keywords for "own ASIN" and "competitor ASINs" separately, compute three gap types:
  - Keywords competitors have but you don't (Gap keywords)
  - Keywords both have but competitors rank higher (Rank disadvantage keywords)
  - Keywords only you have (Your unique keywords)


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


def keyword_gap_analysis(
    my_asin_data,
    competitor_data,
    output_dir: str | None = None,
    my_asin: str = '',
) -> dict[str, Any]:
    """Process MCP responses from js_keywords_by_asin for gap analysis."""
    data_dir = output_dir or '.'
    os.makedirs(data_dir, exist_ok=True)

    my_rows = []
    for item in (_unwrap_response(my_asin_data) or []):
        attrs = item.get('attributes', item)
        row = {'asin': my_asin}
        row.update(attrs)
        my_rows.append(row)

    comp_rows = []
    for item in (_unwrap_response(competitor_data) or []):
        attrs = item.get('attributes', item)
        row = {'asin': attrs.get('asin', '')}
        row.update(attrs)
        comp_rows.append(row)

    my_df = pd.DataFrame(my_rows) if my_rows else pd.DataFrame(columns=['asin', 'name'])
    comp_df = pd.DataFrame(comp_rows) if comp_rows else pd.DataFrame(columns=['asin', 'name'])

    kw_col = 'name'
    vol_col = 'monthly_search_volume_exact'
    rank_col = 'organic_rank'

    my_keywords = set(my_df[kw_col].dropna()) if kw_col in my_df.columns else set()
    comp_keywords = set(comp_df[kw_col].dropna()) if kw_col in comp_df.columns else set()

    gap_kws = comp_keywords - my_keywords
    gap_df = comp_df[comp_df[kw_col].isin(gap_kws)].copy()
    if vol_col in gap_df.columns:
        gap_df = gap_df.sort_values(vol_col, ascending=False).drop_duplicates(subset=[kw_col]).reset_index(drop=True)
    gap_csv = os.path.join(data_dir, 'gap_keywords.csv')
    gap_df.to_csv(gap_csv, index=False, encoding='utf-8-sig')

    rank_dis_rows = []
    if rank_col in my_df.columns and rank_col in comp_df.columns:
        common_kws = my_keywords & comp_keywords
        my_rank = my_df[my_df[kw_col].isin(common_kws)][[kw_col, rank_col]].set_index(kw_col)
        comp_rank = (
            comp_df[comp_df[kw_col].isin(common_kws)]
            .sort_values(rank_col).drop_duplicates(subset=[kw_col])
            [[kw_col, rank_col, vol_col if vol_col in comp_df.columns else kw_col]]
            .set_index(kw_col))
        for kw in common_kws:
            if kw in my_rank.index and kw in comp_rank.index:
                my_r = my_rank.loc[kw, rank_col]
                comp_r = comp_rank.loc[kw, rank_col]
                try:
                    if comp_r is not None and my_r is not None and float(comp_r) < float(my_r):
                        row = {kw_col: kw, 'my_rank': my_r, 'competitor_best_rank': comp_r}
                        if vol_col in comp_rank.columns:
                            row[vol_col] = comp_rank.loc[kw, vol_col]
                        rank_dis_rows.append(row)
                except (ValueError, TypeError):
                    pass

    rank_dis_df = pd.DataFrame(rank_dis_rows)
    if not rank_dis_df.empty and vol_col in rank_dis_df.columns:
        rank_dis_df = rank_dis_df.sort_values(vol_col, ascending=False).reset_index(drop=True)
    rank_dis_csv = os.path.join(data_dir, 'rank_disadvantage.csv')
    rank_dis_df.to_csv(rank_dis_csv, index=False, encoding='utf-8-sig')

    my_unique_df = my_df[my_df[kw_col].isin(my_keywords - comp_keywords)].copy()
    if vol_col in my_unique_df.columns:
        my_unique_df = my_unique_df.sort_values(vol_col, ascending=False).reset_index(drop=True)
    my_unique_csv = os.path.join(data_dir, 'my_unique_keywords.csv')
    my_unique_df.to_csv(my_unique_csv, index=False, encoding='utf-8-sig')

    return {
        'output_dir': data_dir, 'gap_count': len(gap_df),
        'rank_disadvantage_count': len(rank_dis_df), 'my_unique_count': len(my_unique_df),
        'gap_csv': gap_csv, 'rank_disadvantage_csv': rank_dis_csv, 'my_unique_csv': my_unique_csv,
    }

