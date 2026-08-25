"""
Trend Detection — Based on MCP data processing (js_keywords_by_keyword).

Monitor monthly_trend and quarterly_trend to identify emerging opportunities,
declining risks, and short-term anomaly signals.

Usage:
  import sys
  sys.path.insert(0, '/home/wuying/skills/trend-detection/scripts')
  from detect_trends import detect_trends
  result = detect_trends(
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


DEFAULT_EMERGING_THRESHOLD = 20.0
DEFAULT_DECLINING_THRESHOLD = -20.0


def _classify_trend(
    monthly: float, quarterly: float,
    emerging_thr: float, declining_thr: float,
) -> tuple[str, str]:
    """Return (trend_signal, trend_strength)"""
    if quarterly > emerging_thr:
        strength = 'STRONG' if quarterly > emerging_thr * 2 else 'MODERATE'
        return 'Emerging Opportunity', strength
    if quarterly < declining_thr:
        strength = 'STRONG' if quarterly < declining_thr * 2 else 'MODERATE'
        return 'Declining Risk', strength
    if monthly > 10 and quarterly < 0:
        return 'Short-term Rebound', 'WEAK'
    if monthly < -10 and quarterly > 0:
        return 'Recent Cooldown', 'WEAK'
    return 'Stable', 'WEAK'


def _action_suggestion(signal: str) -> str:
    actions = {
        'Emerging Opportunity': 'Add to keyword library and ad campaigns immediately to capture early ranking advantage',
        'Declining Risk': 'Evaluate reducing inventory and ad spend; look for alternative niche keywords',
        'Short-term Rebound': 'Monitor closely; combine with YoY data to determine if this is a seasonal recovery',
        'Recent Cooldown': 'Maintain current strategy; watch subsequent monthly data for continued cooling',
        'Stable': 'Maintain existing ad spend and inventory strategy; review periodically',
    }
    return actions.get(signal, '')


def detect_trends(
    mcp_data,
    output_dir: str | None = None,
    seed_keyword: str = '',
    emerging_threshold: float = DEFAULT_EMERGING_THRESHOLD,
    declining_threshold: float = DEFAULT_DECLINING_THRESHOLD,
) -> dict[str, Any]:
    """
    Process MCP response from js_keywords_by_keyword.
    Detect keyword trend signals, classifying as emerging/stable/declining/rebound/cooldown.
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
        return {'output_dir': data_dir, 'total_rows': 0,
                'emerging_keywords': [], 'declining_keywords': [],
                'signal_counts': {}, 'trend_signals_csv': ''}

    df = pd.DataFrame(all_rows)

    mt = 'monthly_trend'
    qt = 'quarterly_trend'
    df[mt] = pd.to_numeric(df.get(mt, 0), errors='coerce').fillna(0)
    df[qt] = pd.to_numeric(df.get(qt, 0), errors='coerce').fillna(0)

    signals = df.apply(
        lambda r: _classify_trend(r[mt], r[qt], emerging_threshold, declining_threshold),
        axis=1,
    )
    df['trend_signal'] = signals.apply(lambda x: x[0])
    df['trend_strength'] = signals.apply(lambda x: x[1])
    df['action_suggestion'] = df['trend_signal'].map(_action_suggestion)

    out_cols = ['seed_keyword', 'name', 'monthly_search_volume_exact',
                mt, qt, 'trend_signal', 'trend_strength', 'action_suggestion']
    out_df = df[[c for c in out_cols if c in df.columns]].copy()
    out_df = out_df.sort_values(qt, ascending=False)

    csv_path = os.path.join(data_dir, 'trend_signals.csv')
    out_df.to_csv(csv_path, index=False, encoding='utf-8-sig')

    signal_counts = out_df['trend_signal'].value_counts().to_dict()
    emerging_kws = out_df[out_df['trend_signal'] == 'Emerging Opportunity']['name'].tolist()[:10]
    declining_kws = out_df[out_df['trend_signal'] == 'Declining Risk']['name'].tolist()[:10]

    return {
        'output_dir': data_dir,
        'total_rows': len(all_rows),
        'emerging_keywords': emerging_kws,
        'declining_keywords': declining_kws,
        'signal_counts': signal_counts,
        'trend_signals_csv': csv_path,
    }

