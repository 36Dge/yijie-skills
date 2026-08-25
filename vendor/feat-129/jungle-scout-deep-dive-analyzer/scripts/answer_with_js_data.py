"""
Real Data Extraction for the jungle-scout-deep-dive-analyzer skill.

Step 5 helper: loads CSV data collected from Jungle Scout APIs (Step 2)
and extracts relevant data slices for each sub-question dimension.

This module only handles data loading. The Agent itself is the analyst —
it reads the extracted data, reasons over it, and directly constructs
SubQuestionAnswer objects. There is NO external LLM call in this step.

Flow per sub-question:
  1. Agent calls set_data_dir() to point to the round's data directory
  2. Agent calls extract_relevant_data(question) to get CSV summaries
  3. Agent analyzes the data and constructs SubQuestionAnswer directly
  4. Agent calls pipeline.save_subquestion_answers()
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from models import SubQuestion

_DATA_DIR = Path('/home/wuying/accio/data')


def set_data_dir(path: str) -> None:
    """Override the data directory at runtime (called before extract_relevant_data)."""
    global _DATA_DIR
    _DATA_DIR = Path(path)


# ---------------------------------------------------------------------------
# Dimension → CSV data source mapping
# ---------------------------------------------------------------------------
_DIMENSION_DATA_MAP: dict[str, list[str]] = {
    'search_volume': ['keywords_market.csv'],
    'search_volume_trend': ['keyword_trends.csv', 'keywords_market.csv'],
    'keyword_analysis': ['keywords_market.csv'],
    'keyword_trend': ['keyword_trends.csv'],
    'brand_concentration': ['market_concentration.csv'],
    'brand_share': ['market_concentration.csv'],
    'market_share': ['market_concentration.csv'],
    'competition': ['competitors.csv', 'market_concentration.csv'],
    'competitor_analysis': ['competitors.csv'],
    'review_barrier': ['competitors.csv'],
    'review_distribution': ['competitors.csv'],
    'price_analysis': ['competitors.csv'],
    'profit_margin': ['competitors.csv'],
    'margin_analysis': ['competitors.csv'],
    'sub_niche': ['competitors.csv', 'keywords_market.csv'],
    'niche_analysis': ['competitors.csv', 'keywords_market.csv'],
    'ppc_analysis': ['keywords_market.csv', 'market_concentration.csv'],
    'traffic_structure': ['market_concentration.csv', 'keywords_market.csv'],
    'seasonality': ['keyword_trends.csv'],
    'trend_analysis': ['keyword_trends.csv'],
    # Standard 8-dimension keys (match SKILL.md Step 4 target_dimension values)
    'market_size_demand': ['keywords_market.csv', 'keyword_trends.csv'],
    'market_size': ['keywords_market.csv', 'keyword_trends.csv'],
    'competitive_landscape': ['competitors.csv', 'market_concentration.csv'],
    'demand_seasonality': ['keyword_trends.csv'],
    'stability': ['keyword_trends.csv'],
    'barrier': ['competitors.csv'],
    'entry_barrier': ['competitors.csv'],
    'marketing_traffic': ['keywords_market.csv', 'market_concentration.csv'],
    'marketing': ['keywords_market.csv', 'market_concentration.csv'],
    'niche_opportunities': ['competitors.csv', 'keywords_market.csv'],
    'niche': ['competitors.csv', 'keywords_market.csv'],
    'pain_points': ['competitors.csv'],
    'pain_point': ['competitors.csv'],
}


def _load_csv(name: str) -> pd.DataFrame:
    """Load a CSV from the data directory, returning empty DataFrame if missing."""
    path = _DATA_DIR / name
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def extract_relevant_data(question: SubQuestion) -> dict[str, Any]:
    """Extract relevant CSV data slices for a sub-question.

    Uses target_dimension and source_indicators to determine which
    CSV files to load and what summary statistics to extract.

    Args:
        question: A SubQuestion with target_dimension set.

    Returns:
        Dict keyed by CSV name (without .csv) containing summary data:
        - keywords_market: total_keywords, top_10_keywords, columns
        - competitors: total_products, top_20_products, price_stats, review_stats, columns
        - market_concentration: total_brands, all_brands
        - keyword_trends: total_data_points, trend_data
    """
    dimension = question.target_dimension.lower().replace(' ', '_').replace('-', '_')

    # Find matching CSV files
    csv_files: set[str] = set()
    for key, files in _DIMENSION_DATA_MAP.items():
        if key in dimension:
            csv_files.update(files)

    # Fallback: load all core CSVs if no specific match
    if not csv_files:
        csv_files = {
            'keywords_market.csv',
            'competitors.csv',
            'market_concentration.csv',
            'keyword_trends.csv',
        }

    data_context: dict[str, Any] = {}

    for csv_file in csv_files:
        df = _load_csv(csv_file)
        if df.empty:
            continue

        key = csv_file.replace('.csv', '')

        if csv_file == 'keywords_market.csv':
            data_context[key] = {
                'total_keywords': len(df),
                'top_10_keywords': df.head(10).to_dict('records'),
                'columns': list(df.columns),
            }
        elif csv_file == 'competitors.csv':
            data_context[key] = {
                'total_products': len(df),
                'top_20_products': df.head(20).to_dict('records'),
                'price_stats': {
                    'mean': round(pd.to_numeric(df['price'], errors='coerce').mean(), 2),
                    'min': round(pd.to_numeric(df['price'], errors='coerce').min(), 2),
                    'max': round(pd.to_numeric(df['price'], errors='coerce').max(), 2),
                } if 'price' in df.columns and len(df) > 0 else {},
                'review_stats': {
                    'mean': round(pd.to_numeric(df['reviews'], errors='coerce').mean(), 0),
                    'min': int(pd.to_numeric(df['reviews'], errors='coerce').min()),
                    'max': int(pd.to_numeric(df['reviews'], errors='coerce').max()),
                } if 'reviews' in df.columns and len(df) > 0 else {},
                'columns': list(df.columns),
            }
        elif csv_file == 'market_concentration.csv':
            data_context[key] = {
                'total_brands': len(df),
                'all_brands': df.to_dict('records'),
            }
        elif csv_file == 'keyword_trends.csv':
            data_context[key] = {
                'total_data_points': len(df),
                'trend_data': df.to_dict('records'),
            }

    return data_context

