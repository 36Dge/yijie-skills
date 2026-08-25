"""
Stock-Out Detection & Competitive Opportunity — MCP data processing (js_sales_estimates).

Monitors daily sales velocity for competitor ASINs, detects sudden drops
that signal stock-outs, quantifies duration and demand gap for each event,
and classifies severity to support rapid competitive responses.


"""

from __future__ import annotations

import json as _json
import os
from datetime import datetime, timedelta
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
MA_WINDOW = 7
DEFAULT_DROP_THRESHOLD = 0.2
DEFAULT_MIN_STREAK = 2
SEVERE_RATIO = 0.05
MODERATE_RATIO = 0.20


def _add_stockout_signals(
    df: pd.DataFrame,
    drop_threshold: float,
    min_streak_days: int,
) -> pd.DataFrame:
    """Add MA7, velocity_ratio, stockout signal, and event IDs."""
    result_frames = []
    global_event_id = 0

    for asin, group in df.groupby('asin'):
        g = group.sort_values('date').copy()
        units = g['estimated_units_sold']

        # 7-day moving average (lagged by 1 to avoid look-ahead)
        g['ma7_units'] = (
            units.shift(1)
            .rolling(window=MA_WINDOW, min_periods=1)
            .mean()
            .round(1)
        )
        # First row has no lag; use raw value as fallback
        g['ma7_units'] = g['ma7_units'].fillna(units.iloc[0] if len(units) > 0 else 0)

        # Velocity ratio: current units / MA7 baseline
        g['velocity_ratio'] = (
            (units / g['ma7_units'].replace(0, float('nan')))
            .round(3)
            .fillna(0.0)
        )

        # Stock-out signal: velocity_ratio < drop_threshold
        g['is_stockout_signal'] = g['velocity_ratio'] < drop_threshold

        # Identify consecutive streaks and assign event IDs
        g['stockout_event_id'] = 0
        streak = 0
        current_event = 0
        event_ids = []
        for signal in g['is_stockout_signal']:
            if signal:
                streak += 1
                if streak == min_streak_days:
                    global_event_id += 1
                    current_event = global_event_id
                    # Back-fill the earlier days of this streak
                    for i in range(min_streak_days - 1):
                        event_ids[-(i + 1)] = current_event
                if streak >= min_streak_days:
                    event_ids.append(current_event)
                else:
                    event_ids.append(0)
            else:
                streak = 0
                current_event = 0
                event_ids.append(0)
        g['stockout_event_id'] = event_ids

        result_frames.append(g)

    return pd.concat(result_frames, ignore_index=True)


def _classify_severity(avg_units: float, baseline: float) -> str:
    """Classify stock-out severity based on remaining sales vs baseline."""
    if baseline <= 0:
        return 'mild'
    ratio = avg_units / baseline
    if ratio < SEVERE_RATIO:
        return 'severe'
    if ratio < MODERATE_RATIO:
        return 'moderate'
    return 'mild'


def _build_stockout_events(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate daily signals into discrete stock-out events."""
    events_df = df[df['stockout_event_id'] > 0]
    if events_df.empty:
        return pd.DataFrame(columns=[
            'event_id', 'asin', 'start_date', 'end_date', 'duration_days',
            'avg_units_during', 'baseline_ma7', 'demand_gap_units', 'severity',
        ])

    rows = []
    for event_id, group in events_df.groupby('stockout_event_id'):
        g = group.sort_values('date')
        asin = g['asin'].iloc[0]
        start_date = g['date'].iloc[0]
        end_date = g['date'].iloc[-1]
        duration = len(g)
        avg_units = round(float(g['estimated_units_sold'].mean()), 1)
        baseline = round(float(g['ma7_units'].iloc[0]), 1)
        actual_total = int(g['estimated_units_sold'].sum())
        expected_total = round(baseline * duration)
        demand_gap = max(0, expected_total - actual_total)
        severity = _classify_severity(avg_units, baseline)

        rows.append({
            'event_id': int(event_id),
            'asin': asin,
            'start_date': start_date,
            'end_date': end_date,
            'duration_days': duration,
            'avg_units_during': avg_units,
            'baseline_ma7': baseline,
            'demand_gap_units': demand_gap,
            'severity': severity,
        })

    return pd.DataFrame(rows)


def detect_stockouts(
    mcp_data,
    output_dir: str | None = None,
    asin: str = '',
    drop_threshold: float = DEFAULT_DROP_THRESHOLD,
    min_streak_days: int = DEFAULT_MIN_STREAK,
) -> dict[str, Any]:
    """Process MCP response from js_sales_estimates for stock-out detection."""
    items = _unwrap_response(mcp_data)
    data_dir = output_dir or '.'
    os.makedirs(data_dir, exist_ok=True)

    all_rows = []
    for item in (items or []):
        attrs = item.get('attributes', item)
        nested_data = attrs.get('data', None)
        if isinstance(nested_data, list):
            for daily in nested_data:
                row = {
                    'asin': asin,
                    'date': str(daily.get('date', '')),
                    'estimated_units_sold': daily.get('estimated_units_sold', 0),
                    'price': daily.get('last_known_price') or 0.0,
                }
                all_rows.append(row)
        else:
            row = {
                'asin': asin,
                'date': str(attrs.get('date', '')),
                'estimated_units_sold': attrs.get('estimated_units_sold', 0),
                'price': attrs.get('last_known_price') or 0.0,
            }
            all_rows.append(row)

    if not all_rows:
        return {'output_dir': data_dir, 'total_rows': 0, 'rows_per_asin': {asin: 0},
                'columns': [], 'stockout_daily_csv': '', 'stockout_events_csv': '',
                'total_events': 0}

    df = pd.DataFrame(all_rows)
    df = _add_stockout_signals(df, drop_threshold, min_streak_days)

    csv_path = os.path.join(data_dir, 'stockout_daily.csv')
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')

    events_df = _build_stockout_events(df)
    events_path = os.path.join(data_dir, 'stockout_events.csv')
    events_df.to_csv(events_path, index=False, encoding='utf-8-sig')

    return {
        'output_dir': data_dir, 'total_rows': len(df),
        'rows_per_asin': {asin: len(all_rows)},
        'columns': list(df.columns),
        'stockout_daily_csv': csv_path, 'stockout_events_csv': events_path,
        'total_events': len(events_df),
    }

