"""
Keyword Expansion Script — MCP data processing (js_keywords_by_keyword).

Raw data collection: calls keywords_by_keyword for each seed keyword,
dumps ALL fields from model_dump() as-is to CSV. No transformation.


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


def expand_keywords(
    mcp_data,
    output_dir: str | None = None,
    seed_keyword: str = '',
) -> dict[str, Any]:
    """
    Process MCP response from js_keywords_by_keyword.
    Dumps ALL raw fields to CSV with a seed_keyword column prepended.

    Args:
        mcp_data:      Pre-fetched MCP response data.
        output_dir:    Directory for output CSV.
        seed_keyword:  The seed keyword used for the MCP call.

    Returns:
        dict with output_dir, total_rows, columns, keyword_expansion_csv.
    """
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
        return {
            'output_dir': data_dir,
            'total_rows': 0,
            'columns': [],
            'keyword_expansion_csv': '',
        }

    csv_path = os.path.join(data_dir, 'keyword_expansion.csv')
    df = pd.DataFrame(all_rows)
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')

    return {
        'output_dir': data_dir,
        'total_rows': len(all_rows),
        'columns': list(df.columns),
        'keyword_expansion_csv': csv_path,
    }

