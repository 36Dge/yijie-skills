"""
Pipeline file I/O wiring for the jungle-scout-deep-dive-analyzer skill.

Provides helper functions for:
- Creating the output directory structure (data/, reports/, charts/)
- Saving Step 4 output (subquestions.json)
- Saving Step 5 output (subquestion_answers.json)
- Aggregating analysis-driven product recommendations (generate_ranked_recommendations)
- Generating CSV content for Amazon products and Alibaba supply search

These functions are called by the Agent at runtime via SKILL.md instructions.
The actual pipeline orchestration (Step 1 → Step 8) is driven by
the Agent, not by this module.
"""

from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import Any

from models import (
    SubQuestionAnswerList,
    SubQuestionList,
)

# Default output base directory (relative to sandbox working directory).
# Agent MUST pass the correct round directory at runtime.
_DEFAULT_OUTPUT_DIR = '.'

def ensure_output_dirs(base_dir: str = _DEFAULT_OUTPUT_DIR) -> dict[str, Path]:
    """Create the output directory structure for the pipeline.

    Creates:
        - ``<base_dir>/data/``
        - ``<base_dir>/reports/``
        - ``<base_dir>/charts/``

    Args:
        base_dir: Root output directory. Agent should pass the current round path.

    Returns:
        Dict mapping directory names to their Path objects.
    """
    base = Path(base_dir)
    dirs = {
        'data': base / 'data',
        'reports': base / 'reports',
        'charts': base / 'charts',
    }
    for name, path in dirs.items():
        path.mkdir(parents=True, exist_ok=True)
    return dirs

def save_subquestions(
    subquestions: SubQuestionList,
    base_dir: str = _DEFAULT_OUTPUT_DIR,
) -> Path:
    """Serialize SubQuestionList to JSON and save to reports directory."""
    output_path = Path(base_dir) / 'reports' / 'subquestions.json'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(subquestions.to_json(), encoding='utf-8')
    return output_path

def load_subquestions(base_dir: str = _DEFAULT_OUTPUT_DIR) -> SubQuestionList:
    """Load SubQuestionList from the reports directory JSON file."""
    input_path = Path(base_dir) / 'reports' / 'subquestions.json'
    return SubQuestionList.from_json(input_path.read_text(encoding='utf-8'))


def save_subquestion_answers(
    answers: SubQuestionAnswerList,
    base_dir: str = _DEFAULT_OUTPUT_DIR,
) -> Path:
    """Serialize SubQuestionAnswerList to JSON and save to reports directory."""
    output_path = Path(base_dir) / 'reports' / 'subquestion_answers.json'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(answers.to_json(), encoding='utf-8')
    return output_path

def save_report(
    report_content: str,
    base_dir: str = _DEFAULT_OUTPUT_DIR,
) -> Path:
    """Save the final report markdown to the reports directory.

    .. deprecated::
        SKILL.md v0.16.0+ uses the ``write_file`` tool directly to write
        ``final_report.md``. This function is kept for backward compatibility
        but is no longer called by the standard pipeline.
    """
    output_path = Path(base_dir) / 'reports' / 'final_report.md'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report_content, encoding='utf-8')
    return output_path

def save_recommendations_csv(
    csv_content: str | list[dict[str, Any]],
    base_dir: str = _DEFAULT_OUTPUT_DIR,
) -> Path:
    """Save the recommended products CSV to the reports directory.

    Accepts either a pre-formatted CSV string **or** a list of product dicts.
    If a list is passed it is automatically converted via
    ``generate_recommendations_csv()``.
    """
    if isinstance(csv_content, list):
        csv_content = generate_recommendations_csv(csv_content)
    output_path = Path(base_dir) / 'reports' / 'final_recommendations.csv'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(csv_content, encoding='utf-8-sig')
    return output_path

def save_alibaba_supply_csv(
    csv_content: str | list[dict[str, Any]],
    base_dir: str = _DEFAULT_OUTPUT_DIR,
) -> Path:
    """Save the Alibaba supply search CSV to the reports directory.

    Accepts either a pre-formatted CSV string **or** a list of supplier dicts.
    If a list is passed it is automatically converted via
    ``generate_alibaba_supply_csv()``.
    """
    if isinstance(csv_content, list):
        csv_content = generate_alibaba_supply_csv(csv_content)
    output_path = Path(base_dir) / 'reports' / 'alibaba_supply.csv'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(csv_content, encoding='utf-8-sig')
    return output_path


# ---------------------------------------------------------------------------
# CSV generation
# ---------------------------------------------------------------------------

_RECOMMENDATIONS_CSV_COLUMNS: list[str] = [
    'asin', 'title', 'brand', 'price', 'sales_cnt_30d',
    'rating', 'reviews', 'net_margin_pct', 'prodUrl', 'imageUrl',
    'recommendation_source', 'recommendation_reason', 'reference_id',
]


def _normalize_product_row(raw: dict[str, Any]) -> dict[str, Any]:
    """Normalize varying column names from shopping search / Agent into canonical keys."""

    def _clean(val: Any) -> str:
        """Return empty string for NaN/None/empty values."""
        s = str(val).strip() if val is not None else ''
        return '' if s.lower() in ('nan', 'none', '') else s

    row: dict[str, Any] = {}
    row['asin'] = (
        raw.get('asin') or raw.get('ASIN')
        or raw.get('Reference ID') or raw.get('Reference id')
        or raw.get('reference_id') or ''
    )
    row['title'] = (
        raw.get('title') or raw.get('Title')
        or raw.get('Product Title') or raw.get('Product Name')
        or raw.get('product_title') or raw.get('name') or ''
    )
    row['brand'] = _clean(raw.get('brand') or raw.get('Brand'))
    row['price'] = _clean(raw.get('price') or raw.get('Price'))
    row['sales_cnt_30d'] = _clean(
        raw.get('sales_cnt_30d') or raw.get('Monthly Sales')
        or raw.get('monthly_sales')
        or raw.get("Latest Month's Sale Volume")
        or raw.get('Last Month Sales')
    )
    row['rating'] = _clean(raw.get('rating') or raw.get('Rating'))
    row['reviews'] = _clean(raw.get('reviews') or raw.get('Reviews'))
    row['net_margin_pct'] = _clean(raw.get('net_margin_pct'))
    row['prodUrl'] = (
        raw.get('prodUrl') or raw.get('Product Url')
        or raw.get('Product URL') or raw.get('product_url') or ''
    )
    row['imageUrl'] = (
        raw.get('imageUrl') or raw.get('Image Url')
        or raw.get('Image URL') or raw.get('image_url') or ''
    )
    row['recommendation_source'] = raw.get('recommendation_source') or ''
    row['recommendation_reason'] = raw.get('recommendation_reason') or ''
    row['reference_id'] = raw.get('reference_id') or raw.get('Reference id') or raw.get('Reference ID') or ''
    # Auto-generate prodUrl from ASIN if missing
    if not row['prodUrl'] and row['asin']:
        row['prodUrl'] = f"https://www.amazon.com/dp/{row['asin']}"
    return row


def generate_recommendations_csv(
    product_search_results: list[dict[str, Any]] | None,
) -> str:
    """Generate a CSV string of recommended Amazon products (Step 6).

    Handles varying column names from different sources (shopping search CSV,
    Agent-constructed dicts, etc.) by normalizing keys before writing.
    """
    if not product_search_results:
        return ''

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=_RECOMMENDATIONS_CSV_COLUMNS, extrasaction='ignore')
    writer.writeheader()

    for product in product_search_results:
        row = _normalize_product_row(product)
        writer.writerow(row)

    csv_content = output.getvalue()
    output.close()
    return csv_content


def generate_ranked_recommendations(
    base_dir: str = _DEFAULT_OUTPUT_DIR,
) -> list[dict[str, Any]]:
    """Aggregate ``recommended_asins`` from subquestion_answers.json and rank them.

    For each ASIN recommended across dimensions, counts how many dimensions
    mentioned it (``dimension_count``) and collects the per-dimension reasons.
    Then cross-matches with ``competitors.csv`` to enrich with product details
    (title, brand, price, sales, rating, reviews, imageUrl).

    Returns a list sorted by ``dimension_count`` desc, then by revenue proxy
    (price × sales) desc.  Also writes ``product_recommendations_ranked.json``
    to the reports directory.

    This is the **Tier-1 (analysis-driven)** recommendation source.
    """
    import json as _json

    reports_dir = Path(base_dir) / 'reports'
    answers_path = reports_dir / 'subquestion_answers.json'
    if not answers_path.exists():
        return []

    answers_data = _json.loads(answers_path.read_text(encoding='utf-8'))

    # --- collect per-ASIN info across dimensions ---
    asin_map: dict[str, dict[str, Any]] = {}
    for ans in answers_data.get('answers', []):
        dim = ans.get('question_id', '')
        for rec in ans.get('recommended_asins', []):
            asin = rec.get('asin', '').strip()
            if not asin:
                continue
            if asin not in asin_map:
                asin_map[asin] = {
                    'asin': asin,
                    'dimension_count': 0,
                    'dimensions': [],
                    'reasons': [],
                }
            asin_map[asin]['dimension_count'] += 1
            asin_map[asin]['dimensions'].append(dim)
            asin_map[asin]['reasons'].append(rec.get('reason', ''))

    if not asin_map:
        return []

    # --- enrich from competitors.csv ---
    competitors_path = Path(base_dir) / 'data' / 'competitors.csv'
    comp_lookup: dict[str, dict[str, Any]] = {}
    if competitors_path.exists():
        import csv as _csv
        with open(competitors_path, encoding='utf-8-sig') as f:
            reader = _csv.DictReader(f)
            for row in reader:
                row_asin = (
                    row.get('asin') or row.get('ASIN')
                    or row.get('asin_number') or ''
                )
                if row_asin:
                    comp_lookup[row_asin] = row

    ranked: list[dict[str, Any]] = []
    for asin, info in asin_map.items():
        comp = comp_lookup.get(asin, {})
        entry: dict[str, Any] = {
            'asin': asin,
            'dimension_count': info['dimension_count'],
            'dimensions': info['dimensions'],
            'reasons': info['reasons'],
            'title': comp.get('title') or comp.get('name') or '',
            'brand': comp.get('brand') or '',
            'price': comp.get('price') or '',
            'sales_cnt_30d': comp.get('sales_cnt_30d') or comp.get('Monthly Sales') or '',
            'rating': comp.get('rating') or '',
            'reviews': comp.get('reviews') or '',
            'revenue_30d': comp.get('revenue_30d') or '',
            'imageUrl': comp.get('imageUrl') or comp.get('image_url') or '',
            'prodUrl': comp.get('prodUrl') or '',
            'recommendation_source': 'analysis-driven',
            'recommendation_reason': '; '.join(info['reasons']),
        }
        ranked.append(entry)

    # sort: dimension_count desc, then revenue desc
    def _sort_key(e: dict[str, Any]) -> tuple[int, float]:
        dim_cnt = e.get('dimension_count', 0)
        try:
            rev = float(str(e.get('revenue_30d', 0)).replace('$', '').replace(',', '') or 0)
            if not rev:
                price = float(str(e.get('price', 0)).replace('$', '').replace(',', '') or 0)
                sales = float(str(e.get('sales_cnt_30d', 0)).replace(',', '') or 0)
                rev = price * sales
        except (ValueError, TypeError):
            rev = 0.0
        return (dim_cnt, rev)

    ranked.sort(key=_sort_key, reverse=True)

    # write JSON
    out_path = reports_dir / 'product_recommendations_ranked.json'
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        _json.dumps(ranked, ensure_ascii=False, indent=2),
        encoding='utf-8',
    )
    return ranked


_ALIBABA_CSV_COLUMNS: list[str] = [
    'title', 'supplier_name', 'price_min', 'price_max',
    'moq', 'supplier_rating', 'url', 'reference_id',
]


def _split_alibaba_price(price_str: str) -> tuple[str, str]:
    """Split Alibaba price string like '$6.20-7.80' into (min, max).

    Handles formats: '$6.20-7.80', '$6.20 - $7.80', '$10', '$3.51'.
    """
    import re

    if not price_str:
        return ('', '')
    nums = re.findall(r'[\d.]+', str(price_str))
    if len(nums) >= 2:
        return (nums[0], nums[1])
    if len(nums) == 1:
        return (nums[0], nums[0])
    return ('', '')


def generate_alibaba_supply_csv(
    alibaba_supply_results: list[dict[str, Any]] | None,
) -> str:
    """Generate a CSV string of Alibaba supply search results (Step 7)."""
    if not alibaba_supply_results:
        return ''

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=_ALIBABA_CSV_COLUMNS, extrasaction='ignore')
    writer.writeheader()

    for item in alibaba_supply_results:
        row = dict(item)
        # Normalize field names from various sources (raw, display, LLM)
        if 'title' not in row:
            row['title'] = (
                row.get('name') or row.get('Product title') or
                row.get('product_title') or ''
            )
        if 'supplier_name' not in row:
            row['supplier_name'] = (
                row.get('supplier') or row.get('Supplier name') or
                row.get('comp_name') or ''
            )
        # Handle combined price field (e.g., '$6.20-7.80') → split into min/max
        if 'price_min' not in row and 'price_max' not in row:
            combined_price = row.get('price') or row.get('Price') or ''
            if combined_price:
                row['price_min'], row['price_max'] = _split_alibaba_price(combined_price)
            else:
                row['price_min'] = row.get('min_price') or ''
                row['price_max'] = row.get('max_price') or ''
        elif 'price_min' not in row:
            row['price_min'] = row.get('min_price') or ''
        elif 'price_max' not in row:
            row['price_max'] = row.get('max_price') or ''
        if 'moq' not in row:
            row['moq'] = row.get('min_order') or row.get('MOQ') or ''
        if 'supplier_rating' not in row:
            row['supplier_rating'] = row.get('rating') or ''
        if 'url' not in row:
            row['url'] = (
                row.get('productUrl') or row.get('prodUrl') or
                row.get('Product URL') or row.get('Product url') or ''
            )
        # Normalize reference_id from product_supplier_search results
        if 'reference_id' not in row:
            row['reference_id'] = (
                row.get('Reference id') or row.get('Reference ID') or
                row.get('ref_id') or ''
            )
        writer.writerow(row)

    csv_content = output.getvalue()
    output.close()
    return csv_content

