"""
Search Share & Organic Visibility Tracking Script — MCP data processing (js_keywords_by_asin).

Collects keyword ranking data (organic rank + sponsored rank) for target ASINs,
computes search share metrics (weighted organic rank coverage), outputs ranking
distribution snapshots, and supports ranking change comparison across periodic pulls.


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


# Rank tier buckets (organic rank)
RANK_BUCKETS = [
    ('Top3', 1, 3),
    ('Top10', 4, 10),
    ('Top20', 11, 20),
    ('Top50', 21, 50),
    ('Beyond50', 51, 9999),
]


def share_of_search_tracking(
    mcp_data,
    output_dir: str | None = None,
    asin: str = '',
    snapshot_label: str = 'snapshot',
    min_search_volume: int = 100,
) -> dict[str, Any]:
    """Process MCP response from js_keywords_by_asin for search share tracking."""
    items = _unwrap_response(mcp_data)
    data_dir = output_dir or '.'
    os.makedirs(data_dir, exist_ok=True)

    all_rows = []
    for item in (items or []):
        attrs = item.get('attributes', item)
        row = {'asin': asin, 'snapshot': snapshot_label}
        row.update(attrs)
        all_rows.append(row)

    if not all_rows:
        return {'output_dir': data_dir, 'snapshot_label': snapshot_label,
                'rows_per_asin': {asin: 0}, 'weighted_sos_per_asin': {},
                'raw_csv': '', 'distribution_csv': '', 'sos_csv': ''}

    df = pd.DataFrame(all_rows)
    rank_col = 'organic_rank'
    sp_rank_col = 'sponsored_rank'
    vol_col = 'monthly_search_volume_exact'

    raw_csv = os.path.join(data_dir, f'rank_snapshot_{snapshot_label}.csv')
    df.to_csv(raw_csv, index=False, encoding='utf-8-sig')

    for c in (rank_col, sp_rank_col, vol_col):
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')

    if vol_col in df.columns:
        df_filtered = df[df[vol_col].fillna(0) >= min_search_volume].copy()
    else:
        df_filtered = df.copy()

    asins = [asin] if asin else df_filtered['asin'].unique().tolist()
    dist_rows = []
    if rank_col in df_filtered.columns:
        for a in asins:
            adf = df_filtered[df_filtered['asin'] == a]
            row = {'asin': a, 'snapshot': snapshot_label, 'total_keywords': len(adf)}
            for bucket_name, lo, hi in RANK_BUCKETS:
                count = int(((adf[rank_col] >= lo) & (adf[rank_col] <= hi)).sum())
                row[f'rank_{bucket_name}'] = count
            if sp_rank_col in adf.columns:
                row['sponsored_coverage'] = int(adf[sp_rank_col].notna().sum())
            dist_rows.append(row)

    dist_df = pd.DataFrame(dist_rows)
    dist_csv = os.path.join(data_dir, f'rank_distribution_{snapshot_label}.csv')
    dist_df.to_csv(dist_csv, index=False, encoding='utf-8-sig')

    sos_rows = []
    weighted_sos_per_asin = {}
    if rank_col in df_filtered.columns and vol_col in df_filtered.columns:
        for a in asins:
            adf = df_filtered[df_filtered['asin'] == a].copy()
            total_vol = adf[vol_col].fillna(0).sum()
            top20_vol = adf.loc[adf[rank_col].fillna(999) <= 20, vol_col].fillna(0).sum()
            sos = (top20_vol / total_vol) if total_vol > 0 else 0.0
            weighted_sos_per_asin[a] = round(float(sos), 4)
            sos_rows.append({
                'asin': a, 'snapshot': snapshot_label,
                'total_search_volume': int(total_vol),
                'top20_organic_search_volume': int(top20_vol),
                'weighted_organic_sos': round(float(sos), 4),
            })

    sos_df = pd.DataFrame(sos_rows)
    sos_csv = os.path.join(data_dir, f'weighted_sos_{snapshot_label}.csv')
    sos_df.to_csv(sos_csv, index=False, encoding='utf-8-sig')

    return {
        'output_dir': data_dir, 'snapshot_label': snapshot_label,
        'rows_per_asin': {asin: len(all_rows)},
        'weighted_sos_per_asin': weighted_sos_per_asin,
        'raw_csv': raw_csv, 'distribution_csv': dist_csv, 'sos_csv': sos_csv,
    }

