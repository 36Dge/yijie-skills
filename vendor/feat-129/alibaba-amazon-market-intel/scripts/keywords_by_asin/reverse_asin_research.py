"""
Reverse ASIN Keyword Research Script — MCP data processing (js_keywords_by_asin).

Raw data collection: calls keywords_by_asin for each ASIN, writes all model_dump() fields
as-is to CSV, with an additional asin source column. No transformations applied.


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


def reverse_asin_research(
    mcp_data,
    output_dir: str | None = None,
    asin: str = '',
    top_n: int = 50,
) -> dict[str, Any]:
    """Process MCP response from js_keywords_by_asin. Raw data collection."""
    items = _unwrap_response(mcp_data)
    data_dir = output_dir or '.'
    os.makedirs(data_dir, exist_ok=True)

    all_rows = []
    for item in (items or []):
        attrs = item.get('attributes', item)
        row = {'asin': asin}
        row.update(attrs)
        all_rows.append(row)

    if not all_rows:
        return {'output_dir': data_dir, 'total_rows': 0, 'rows_per_asin': {asin: 0},
                'columns': [], 'raw_csv': '', 'summary_csv': ''}

    raw_csv = os.path.join(data_dir, 'asin_keywords_raw.csv')
    df = pd.DataFrame(all_rows)
    df.to_csv(raw_csv, index=False, encoding='utf-8-sig')

    vol_col = 'monthly_search_volume_exact' if 'monthly_search_volume_exact' in df.columns else None
    if vol_col:
        summary_df = (
            df.sort_values(vol_col, ascending=False)
            .groupby('asin').head(top_n).reset_index(drop=True))
    else:
        summary_df = df.copy()

    summary_csv = os.path.join(data_dir, 'top_keywords_summary.csv')
    summary_df.to_csv(summary_csv, index=False, encoding='utf-8-sig')

    return {
        'output_dir': data_dir, 'total_rows': len(all_rows),
        'rows_per_asin': {asin: len(all_rows)},
        'columns': list(df.columns), 'raw_csv': raw_csv, 'summary_csv': summary_csv,
    }

