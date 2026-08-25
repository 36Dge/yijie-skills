"""
Indicator Analysis Script for Product Selection Deep Research.

Step 3: Compute 11 Core Indicators from collected CSV data.
Run after collect_js_data.py.

Indicators:
  1. Main KW
  2. Category
  3. Search Volume
  4. Top 1 Seller Revenue
  5. $5K+ Listings
  6. Avg Price / Weight / FBA Fee
  7. Avg Reviews / Rating
  8. Monopoly
  9. Seasonality
  10. Traffic Ratio
  11. PPC Bid / Conversion

Usage:
  python analyze_indicators.py --keyword "wireless earbuds" [--input_dir /path/to/data] [--output_file /path/to/output.json]

  Legacy usage (edit REPLACE_KEYWORD directly) is still supported.
"""

import argparse
import json
import os

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# CLI arguments
# ---------------------------------------------------------------------------
_parser = argparse.ArgumentParser(description='Compute indicator framework from CSV data')
_parser.add_argument('--keyword', type=str, default=None, help='Main search keyword')
_parser.add_argument('--input_dir', type=str, default=None, help='Input directory containing CSV files')
_parser.add_argument('--output_file', type=str, default=None, help='Output JSON file path')
_args, _ = _parser.parse_known_args()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DATA_DIR = _args.input_dir or '/home/wuying/accio/data/'
MAIN_KEYWORD_ARG = _args.keyword  # Will be used in main block

CV_THRESHOLD = 0.5
MIN_DATA_POINTS = 12
SINGLE_BRAND_THRESHOLD = 0.30
TOP3_THRESHOLD = 0.60


# ===========================================================================
# Indicator Computation Functions
# ===========================================================================

def compute_main_kw(df_keywords: pd.DataFrame, user_keyword: str | None = None) -> dict:
    """Indicator 1: Main KW."""
    if user_keyword:
        return {'value': user_keyword, 'derivation': 'User-specified keyword'}
    if df_keywords.empty or 'monthly_search_volume_exact' not in df_keywords.columns:
        return {'value': 'N/A', 'derivation': 'No keyword data available'}
    top_row = df_keywords.loc[df_keywords['monthly_search_volume_exact'].idxmax()]
    return {
        'value': top_row.get('keyword', 'N/A'),
        'derivation': (
            f"Highest search volume ({top_row.get('monthly_search_volume_exact', 0):,})"
            ' in keywords_market.csv'
        ),
    }


def compute_category(df_competitors: pd.DataFrame) -> dict:
    """Indicator 2: Category."""
    if df_competitors.empty or 'category' not in df_competitors.columns:
        return {'value': 'N/A', 'derivation': 'No category data available'}
    category_counts = df_competitors['category'].value_counts()
    if category_counts.empty:
        return {'value': 'N/A', 'derivation': 'No category data available'}
    top_category = category_counts.index[0]
    return {
        'value': top_category,
        'derivation': f'Dominant category (mode) from {len(df_competitors)} products',
    }


def compute_search_volume(df_keywords: pd.DataFrame, main_kw: str) -> dict:
    """Indicator 3: Search Volume."""
    if df_keywords.empty:
        return {'value': 0, 'derivation': 'No keyword data available'}
    kw_row = df_keywords[df_keywords['keyword'] == main_kw]
    if kw_row.empty:
        kw_row = df_keywords.loc[[df_keywords['monthly_search_volume_exact'].idxmax()]]
    volume = int(kw_row['monthly_search_volume_exact'].iloc[0])
    return {'value': volume, 'derivation': f"monthly_search_volume_exact for '{main_kw}'"}


def compute_top1_revenue(df_competitors: pd.DataFrame) -> dict:
    """Indicator 4: Top 1 Seller Revenue."""
    if df_competitors.empty:
        return {'value': 0, 'derivation': 'No competitor data available'}
    df = df_competitors.copy()
    df['sales_cnt_30d'] = pd.to_numeric(df['sales_cnt_30d'], errors='coerce').fillna(0)
    df['price'] = pd.to_numeric(df['price'], errors='coerce').fillna(0)
    df['daily_sales'] = df['sales_cnt_30d'] / 30
    df['monthly_revenue'] = df['daily_sales'] * df['price'] * 30
    top_idx = df['monthly_revenue'].idxmax()
    top_row = df.loc[top_idx]
    return {
        'value': round(top_row['monthly_revenue'], 2),
        'derivation': (
            f"Daily Sales ({top_row['daily_sales']:.1f})"
            f" × Price (${top_row['price']:.2f}) × 30"
        ),
    }


def compute_5k_listings(df_competitors: pd.DataFrame) -> dict:
    """Indicator 5: $5K+ Listings."""
    if df_competitors.empty:
        return {'value': 0, 'derivation': 'No competitor data available'}
    df = df_competitors.copy()
    df['sales_cnt_30d'] = pd.to_numeric(df['sales_cnt_30d'], errors='coerce').fillna(0)
    df['price'] = pd.to_numeric(df['price'], errors='coerce').fillna(0)
    df['monthly_revenue'] = (df['sales_cnt_30d'] / 30) * df['price'] * 30
    count = int((df['monthly_revenue'] > 5000).sum())
    return {
        'value': count,
        'derivation': f'Count of ASINs with monthly revenue > $5,000 (out of {len(df)})',
    }


def compute_averages(df_competitors: pd.DataFrame) -> dict:
    """Indicator 6: Avg Price / Weight / FBA Fee."""
    if df_competitors.empty:
        return {
            'avg_price': 0, 'avg_weight': 0, 'avg_fba': 0,
            'derivation': 'No competitor data available',
        }
    df = df_competitors.copy()
    avg_price = pd.to_numeric(df['price'], errors='coerce').mean()
    avg_weight = pd.to_numeric(
        df.get('weight', pd.Series(dtype=float)), errors='coerce',
    ).mean()
    if pd.notna(avg_weight) and avg_weight > 0:
        avg_fba = 3.0 + avg_weight * 0.5
    else:
        avg_fba = 5.0
    return {
        'avg_price': round(avg_price, 2) if pd.notna(avg_price) else 0,
        'avg_weight': round(avg_weight, 2) if pd.notna(avg_weight) else 0,
        'avg_fba': round(avg_fba, 2),
        'derivation': f'Mean values from {len(df)} products in competitors.csv',
    }


def compute_reviews_rating(df_competitors: pd.DataFrame, top_n: int = 50) -> dict:
    """Indicator 7: Avg Reviews / Rating."""
    if df_competitors.empty:
        return {
            'avg_reviews': 0, 'avg_rating': 0,
            'derivation': 'No competitor data available',
        }
    df = df_competitors.head(top_n).copy()
    avg_reviews = pd.to_numeric(df['reviews'], errors='coerce').mean()
    avg_rating = pd.to_numeric(df['rating'], errors='coerce').mean()
    return {
        'avg_reviews': int(avg_reviews) if pd.notna(avg_reviews) else 0,
        'avg_rating': round(avg_rating, 2) if pd.notna(avg_rating) else 0,
        'derivation': f'Mean from Top {min(top_n, len(df))} products',
    }


def compute_monopoly(df_sov: pd.DataFrame) -> dict:
    """Indicator 8: Monopoly."""
    if df_sov.empty or 'combined_weighted_sov' not in df_sov.columns:
        return {
            'classification': 'Data unavailable', 'emoji': '❓',
            'top_brand': None, 'top_brand_share': 0, 'top3_share': 0,
            'derivation': 'No share_of_voice data available',
        }
    df = df_sov.sort_values('combined_weighted_sov', ascending=False)
    top_brand = df.iloc[0]['brand']
    top_brand_share = df.iloc[0]['combined_weighted_sov']
    top3_share = df.head(3)['combined_weighted_sov'].sum()
    is_amazon = str(top_brand).lower().strip() == 'amazon'

    if top_brand_share > SINGLE_BRAND_THRESHOLD:
        brand_type = 'Amazon' if is_amazon else 'Third-party'
        return {
            'classification': 'Single brand monopoly', 'emoji': '🔴',
            'top_brand': top_brand,
            'top_brand_share': round(top_brand_share * 100, 1),
            'top3_share': round(top3_share * 100, 1),
            'derivation': f"{brand_type} '{top_brand}' holds {top_brand_share:.1%} share",
        }
    if top3_share > TOP3_THRESHOLD:
        return {
            'classification': 'Concentrated market', 'emoji': '🟡',
            'top_brand': top_brand,
            'top_brand_share': round(top_brand_share * 100, 1),
            'top3_share': round(top3_share * 100, 1),
            'derivation': f'Top 3 brands hold {top3_share:.1%} combined share',
        }
    return {
        'classification': 'Fragmented market', 'emoji': '🟢',
        'top_brand': top_brand,
        'top_brand_share': round(top_brand_share * 100, 1),
        'top3_share': round(top3_share * 100, 1),
        'derivation': 'No dominant brand — market is dispersed',
    }


def compute_seasonality(df_trends: pd.DataFrame) -> dict:
    """Indicator 9: Seasonality."""
    if df_trends.empty or 'estimated_exact_search_volume' not in df_trends.columns:
        return {
            'classification': 'Insufficient data', 'cv': None,
            'derivation': 'No historical search volume data available',
        }
    volumes = pd.to_numeric(
        df_trends['estimated_exact_search_volume'], errors='coerce',
    ).dropna().tolist()
    n = len(volumes)
    if n < MIN_DATA_POINTS:
        return {
            'classification': 'Insufficient data', 'cv': None,
            'derivation': f'Only {n} data points (need >= {MIN_DATA_POINTS})',
        }
    mean_val = np.mean(volumes)
    if mean_val == 0:
        return {
            'classification': 'No search volume', 'cv': None,
            'derivation': 'Mean search volume is 0',
        }
    std_val = np.std(volumes)
    cv = std_val / mean_val
    classification = 'Seasonal' if cv > CV_THRESHOLD else 'Non-seasonal'
    comparison = '>' if cv > CV_THRESHOLD else '≤'
    return {
        'classification': classification,
        'cv': round(cv, 2),
        'derivation': f'CV = {cv:.2f} {comparison} {CV_THRESHOLD} threshold',
    }


def compute_traffic_ratio(df_sov: pd.DataFrame) -> dict:
    """Indicator 10: Traffic Ratio."""
    if df_sov.empty:
        return {
            'organic_pct': 0, 'paid_pct': 0,
            'is_high_ad_dependency': False,
            'derivation': 'No share_of_voice data available',
        }
    organic = pd.to_numeric(
        df_sov.get('organic_click_share', pd.Series(dtype=float)), errors='coerce',
    ).sum()
    sponsored = pd.to_numeric(
        df_sov.get('sponsored_click_share', pd.Series(dtype=float)), errors='coerce',
    ).sum()
    total = organic + sponsored
    if total <= 0:
        return {
            'organic_pct': 0, 'paid_pct': 0,
            'is_high_ad_dependency': False,
            'derivation': 'No click share data available',
        }
    organic_pct = round(organic / total * 100, 1)
    paid_pct = round(sponsored / total * 100, 1)
    return {
        'organic_pct': organic_pct,
        'paid_pct': paid_pct,
        'is_high_ad_dependency': paid_pct > 80,
        'derivation': (
            f'From share_of_voice click shares'
            f' (organic: {organic:.2f}, sponsored: {sponsored:.2f})'
        ),
    }


def compute_ppc_conversion(df_keywords: pd.DataFrame, df_sov: pd.DataFrame) -> dict:
    """Indicator 11: PPC Bid / Conversion."""
    result = {'ppc_min': 0, 'ppc_max': 0, 'conversion': 0, 'derivation': ''}
    if not df_keywords.empty and 'ppc_bid_exact' in df_keywords.columns:
        ppc_values = pd.to_numeric(df_keywords['ppc_bid_exact'], errors='coerce').dropna()
        if not ppc_values.empty:
            result['ppc_min'] = round(ppc_values.min(), 2)
            result['ppc_max'] = round(ppc_values.max(), 2)
    result['conversion'] = 10.0  # Default category average estimate
    result['derivation'] = 'PPC bid range from keywords_market.csv; conversion is category estimate'
    return result


# ===========================================================================
# Main execution
# ===========================================================================
if __name__ == '__main__':
    # Determine output directory for JSON
    _json_output_path = _args.output_file or '/home/wuying/accio/reports/indicators.json'
    _json_output_dir = os.path.dirname(_json_output_path)
    os.makedirs(_json_output_dir, exist_ok=True)

    # Load CSV data — handle empty files gracefully
    def _load_csv(name: str) -> pd.DataFrame:
        path = f'{DATA_DIR}/{name}'
        if not os.path.exists(path):
            return pd.DataFrame()
        try:
            df = pd.read_csv(path)
            return df
        except pd.errors.EmptyDataError:
            print(f'⚠️  {name} is empty, using empty DataFrame')
            return pd.DataFrame()

    df_keywords = _load_csv('keywords_market.csv')
    df_trends = _load_csv('keyword_trends.csv')
    df_competitors = _load_csv('competitors.csv')
    df_sov = _load_csv('market_concentration.csv')

    # Compute all indicators
    print('📊 Computing 11 Core Indicators...\n')

    _user_keyword = MAIN_KEYWORD_ARG or 'REPLACE_KEYWORD'
    main_kw_result = compute_main_kw(df_keywords, user_keyword=_user_keyword)
    main_kw = main_kw_result['value']
    print(f'1. Main KW: {main_kw}')

    category_result = compute_category(df_competitors)
    print(f"2. Category: {category_result['value']}")

    search_vol_result = compute_search_volume(df_keywords, main_kw)
    print(f"3. Search Volume: {search_vol_result['value']:,}")

    top1_result = compute_top1_revenue(df_competitors)
    print(f"4. Top 1 Seller Revenue: ${top1_result['value']:,.2f}")

    listings_result = compute_5k_listings(df_competitors)
    print(f"5. $5K+ Listings: {listings_result['value']}")

    avg_result = compute_averages(df_competitors)
    print(
        f"6. Avg Price/Weight/FBA: ${avg_result['avg_price']}"
        f" / {avg_result['avg_weight']} lbs / ${avg_result['avg_fba']}"
    )

    reviews_result = compute_reviews_rating(df_competitors)
    print(f"7. Avg Reviews/Rating: {reviews_result['avg_reviews']:,} / {reviews_result['avg_rating']}")

    monopoly_result = compute_monopoly(df_sov)
    print(
        f"8. Monopoly: {monopoly_result['emoji']} {monopoly_result['classification']}"
        f" (Top 1: {monopoly_result['top_brand_share']}%)"
    )

    seasonality_result = compute_seasonality(df_trends)
    print(f"9. Seasonality: {seasonality_result['classification']} (CV: {seasonality_result['cv']})")

    traffic_result = compute_traffic_ratio(df_sov)
    flag = ' ⚠️ High Ad Dependency' if traffic_result['is_high_ad_dependency'] else ''
    print(
        f"10. Traffic Ratio: Organic {traffic_result['organic_pct']}%"
        f" / Paid {traffic_result['paid_pct']}%{flag}"
    )

    ppc_result = compute_ppc_conversion(df_keywords, df_sov)
    print(
        f"11. PPC Bid/Conv: ${ppc_result['ppc_min']}"
        f" - ${ppc_result['ppc_max']} / {ppc_result['conversion']}%"
    )

    # Save indicators as JSON for subsequent steps
    print('\n📄 Saving indicator_framework.json...')

    indicators = {
        'main_kw': main_kw,
        'category': category_result['value'],
        'search_volume': search_vol_result['value'],
        'top1_revenue': top1_result['value'],
        'five_k_listings': listings_result['value'],
        'avg_price': avg_result['avg_price'],
        'avg_weight': avg_result['avg_weight'],
        'avg_fba': avg_result['avg_fba'],
        'avg_reviews': reviews_result['avg_reviews'],
        'avg_rating': reviews_result['avg_rating'],
        'monopoly': {
            'classification': monopoly_result['classification'],
            'emoji': monopoly_result['emoji'],
            'top_brand': monopoly_result['top_brand'],
            'top1_share': monopoly_result['top_brand_share'],
            'top3_share': monopoly_result['top3_share'],
        },
        'seasonality': {
            'classification': seasonality_result['classification'],
            'cv': seasonality_result['cv'],
        },
        'traffic_ratio': {
            'organic_pct': traffic_result['organic_pct'],
            'paid_pct': traffic_result['paid_pct'],
        },
        'ppc_bid': {
            'min': ppc_result['ppc_min'],
            'max': ppc_result['ppc_max'],
        },
        'conversion_rate': ppc_result['conversion'],
    }

    with open(_json_output_path, 'w', encoding='utf-8') as f:
        json.dump(indicators, f, indent=2, ensure_ascii=False)

    print(f'\n✅ Indicator analysis complete. JSON saved to {_json_output_path}')

