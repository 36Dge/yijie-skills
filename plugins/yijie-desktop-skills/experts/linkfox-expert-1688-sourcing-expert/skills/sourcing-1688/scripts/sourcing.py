#!/usr/bin/env python3
"""Offline LinkFox request/evidence review and explicit unit contribution scenarios.
No HTTP, credentials, subprocesses, account discovery or automatic tool execution.
"""
import argparse
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import hashlib
import html
import ipaddress
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

SUPPLIERS = {'alibaba1688/imageSearch', 'dld/productSearch'}
UNITS = {
    'sale_usd': 'USD/sale', 'purchase_cny': 'CNY/purchase_unit',
    'fx_cny_per_usd': 'CNY/USD', 'purchase_units_per_sale': 'purchase_units/sale',
    'inbound_usd': 'USD/sale', 'fba_usd': 'USD/sale', 'referral_usd': 'USD/sale',
    'advertising_usd': 'USD/sale', 'storage_usd': 'USD/sale', 'placement_usd': 'USD/sale',
    'other_usd': 'USD/sale', 'return_rate': 'returns/sale',
    'refunded_revenue_usd': 'USD/return', 'referral_refund_usd': 'USD/return',
    'refund_admin_usd': 'USD/return', 'return_handling_usd': 'USD/return', 'recovery_usd': 'USD/return',
}
POSITIVE = {'sale_usd', 'purchase_cny', 'fx_cny_per_usd', 'purchase_units_per_sale'}


def fields(value, allowed):
    if not isinstance(value, dict) or set(value) - set(allowed):
        raise ValueError('unexpected fields or non-object input')


def text(value, label, limit=300):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValueError(label + ' must be explicit nonempty text')
    return value


def number(value):
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise ValueError('explicit finite decimal required')
    try:
        result = Decimal(str(value))
    except InvalidOperation:
        raise ValueError('invalid decimal') from None
    if not result.is_finite() or result < 0 or result > Decimal('1000000000'):
        raise ValueError('nonnegative bounded decimal required')
    return result


def date(value):
    text(value, 'source timestamp', 40)
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None:
        raise ValueError('source timestamp needs timezone')
    return value


def asin(value):
    if not isinstance(value, str) or not re.fullmatch('[A-Z0-9]{10}', value):
        raise ValueError('exact uppercase 10-character ASIN required')
    return value


def public_image(value):
    url = urlsplit(text(value, 'authorized public image URL', 2500))
    host = url.hostname or ''
    if url.scheme != 'https' or not host or url.username or url.password or url.fragment or url.port not in (None, 443):
        raise ValueError('public HTTPS image required')
    if host.lower() == 'localhost' or host.endswith(('.local', '.internal')) or '.' not in host:
        raise ValueError('public image hostname required')
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if address is not None and not address.is_global:
        raise ValueError('public image address required')
    if not re.search(r'\.(png|jpe?g)$', url.path, re.I):
        raise ValueError('explicit PNG/JPEG direct image required; no upload fallback')
    return value


def prepare(value):
    fields(value, ['method', 'target_asin', 'market', 'keyword', 'image_url', 'page', 'days'])
    target = asin(value.get('target_asin'))
    if value.get('market') != 'US':
        raise ValueError('this content version supports US only')
    method = value.get('method')
    page = value.get('page', 1)
    if type(page) is not int or not 1 <= page <= 20:
        raise ValueError('explicit page outside 1..20')
    args = {}
    allowed = {'method', 'target_asin', 'market'}
    if method == 'keepa/productRequest':
        args = {'asin': target, 'domain': '1', 'history': 0}
    elif method == 'keepa/productSeries':
        days = value.get('days')
        if type(days) is not int or not 1 <= days <= 365:
            raise ValueError('history days 1..365 required')
        allowed.add('days')
        args = {'asin': target, 'domain': '1', 'days': days}
    elif method in ('sif/asinKeywords', 'sif/asinSummary'):
        args = {'country': 'US', 'pageNum': page, 'pageSize': 20}
        allowed.add('page')
        args.update({'asin': target, 'timePieceType': 'latelyDay', 'timePieceValue': '7'} if method.endswith('Keywords') else {'searchValue': target, 'last7d': True})
    elif method == 'sellersprite/trafficKeyword':
        allowed.add('page')
        args = {'asin': target, 'marketplace': 'US', 'page': page, 'size': 20}
    elif method == 'alibaba1688/imageSearch':
        allowed.update(['image_url', 'page'])
        args = {'imageUrl': public_image(value.get('image_url')), 'page': page, 'pageSize': 20}
    elif method in ('dld/productSearch', 'amazon/search', 'jiimore/getNicheInfoByKeyword', 'aiMode/googleSearch'):
        allowed.update(['keyword', 'page'])
        keyword = text(value.get('keyword'), 'query keyword', 50 if method == 'dld/productSearch' else 500)
        if method == 'dld/productSearch':
            args = {'keyWord': keyword, 'cycle': '30', 'searchType': 1, 'pageIndex': page, 'pageSize': 20}
        elif method == 'amazon/search':
            args = {'keyword': keyword, 'amazonDomain': 'amazon.com', 'language': 'en_US', 'page': page}
        elif method == 'jiimore/getNicheInfoByKeyword':
            args = {'keyword': keyword, 'countryCode': 'US', 'page': page, 'pageSize': 20}
        else:
            allowed.remove('page')
            args = {'keyword': keyword}
    else:
        raise ValueError('unsupported method; verify current selected MCP schema, do not guess')
    fields(value, allowed)
    request = {'toolName': method, 'arguments': args}
    if len(json.dumps(request, ensure_ascii=False).encode()) > 16 * 1024:
        raise ValueError('request exceeds existing approval limit')
    return {'state': 'prepared_not_submitted', 'request': request, 'target_asin': target,
            'market': 'US', 'current_tool_schema_verified': False}


def payload(result):
    if not isinstance(result, dict) or result.get('isError'):
        raise ValueError('MCP error or unsupported result')
    if 'structuredContent' in result:
        body = result['structuredContent']
    else:
        blocks = result.get('content', [])
        texts = [b.get('text') for b in blocks if isinstance(b, dict) and b.get('type') == 'text']
        if len(texts) != 1 or not isinstance(texts[0], str):
            raise ValueError('ambiguous MCP text result')
        body = json.loads(texts[0])
    if not isinstance(body, (dict, list)):
        raise ValueError('unknown business result shape')
    if isinstance(body, dict):
        for key in ('errcode', 'errorCode', 'code'):
            if key in body and str(body[key]) != '200':
                raise ValueError('business error or unknown success code')
        # Message text is not itself an error: ordinary successful replies say "ok".
        if 'status' in body and body['status'] not in ('SUCCESS', 'success', '200', 200):
            raise ValueError('unknown or unsuccessful business status')
        if body.get('success') is False or body.get('error'):
            raise ValueError('business error')
    return body


def rows(body, key):
    result = body.get(key) if isinstance(body, dict) else body
    if not isinstance(result, list) or len(result) > 200 or any(not isinstance(v, dict) for v in result):
        raise ValueError('missing or unsupported result collection')
    return result


def unique(records, key, identity):
    if not isinstance(records, list) or len(records) > 200 or any(not isinstance(r, dict) for r in records):
        raise ValueError('unsupported identity collection')
    found = [r for r in records if r.get(key) == identity]
    if len(found) != 1:
        raise ValueError('source identity absent or ambiguous: ' + key)
    return found[0]


def market_echo(value):
    if isinstance(value, dict):
        for key, expected in [('marketplace', 'US'), ('country', 'US'), ('countryCode', 'US'), ('domain', '1')]:
            if key in value and str(value[key]) != expected:
                raise ValueError('response market mismatch')


def observe(value):
    fields(value, ['query', 'request', 'source_operation_id', 'captured_at', 'mcp_result', 'offer_id', 'niche_id'])
    plan = prepare(value.get('query'))
    if value.get('request') != plan['request']:
        raise ValueError('actual request differs from query identity')
    operation = text(value.get('source_operation_id'), 'actual Native source operation', 200)
    captured = date(value.get('captured_at'))
    if len(json.dumps(value.get('mcp_result'), ensure_ascii=False).encode()) > 64 * 1024:
        raise ValueError('result exceeds existing connector bound; request a smaller page')
    body = payload(value.get('mcp_result'))
    target, method = plan['target_asin'], plan['request']['toolName']
    row, state = None, 'matched'
    if method not in SUPPLIERS and method != 'aiMode/googleSearch':
        market_echo(body)
    if method == 'keepa/productRequest':
        row = unique(rows(body, 'products'), 'asin', target)
        if row.get('currency') not in ('USD', '$'):
            raise ValueError('unconfirmed US product currency')
    elif method == 'keepa/productSeries':
        row = unique(body if isinstance(body, list) else [body], 'asin', target)
        rows(row, 'buyboxPrice')
        if 'currency' in row and row['currency'] not in ('USD', '$'):
            raise ValueError('historical currency mismatch')
    elif method == 'sif/asinSummary':
        row = unique(rows(body, 'data'), 'asin', target)
    elif method == 'sif/asinKeywords':
        selected = [r for r in rows(body, 'data') if r.get('asin') == target]
        if not selected:
            raise ValueError('no keywords for exact ASIN; absence is not zero advertising')
        row = {'asin': target, 'data': selected}
    elif method == 'sellersprite/trafficKeyword':
        if not isinstance(body, dict) or body.get('asin') != target or body.get('marketplace') != 'US':
            raise ValueError('traffic result ASIN/market mismatch')
        rows(body, 'data')
        row = body
    elif method in SUPPLIERS:
        products = rows(body, 'products')
        offer = value.get('offer_id')
        if offer is None:
            row, state = {'candidates': products}, 'candidates_only'
        else:
            text(offer, 'offer_id', 100)
            row = unique(products, 'offerId', offer)
            if row.get('currency') not in ('CNY', 'RMB', '¥', '￥'):
                raise ValueError('unconfirmed supplier CNY currency')
            # Supplier products.asin is an offer ID, never the Amazon target.
    elif method == 'jiimore/getNicheInfoByKeyword':
        items = rows(body, 'data')
        niche = value.get('niche_id')
        if niche is None:
            row, state = {'candidates': items}, 'candidates_only'
        else:
            row = unique(items, 'nicheId', text(niche, 'exact niche ID', 100))
    elif method == 'amazon/search':
        row, state = {'candidates': rows(body, 'products')}, 'candidates_only'
    else:
        if not isinstance(body, dict) or not isinstance(body.get('stdout'), str):
            raise ValueError('unknown research response')
        row, state = body, 'research_only'
    if method not in SUPPLIERS and state == 'matched':
        market_echo(row)
        if method == 'sif/asinKeywords':
            for item in row['data']:
                market_echo(item)
    if value.get('offer_id') is not None and method not in SUPPLIERS:
        raise ValueError('offer selection belongs only to supplier retrieval')
    if value.get('niche_id') is not None and method != 'jiimore/getNicheInfoByKeyword':
        raise ValueError('niche selection belongs only to niche retrieval')
    return {'state': state, 'source_operation_id': operation, 'captured_at': captured,
            'target_asin': target, 'market': 'US', 'method': method, 'row': row,
            'offer_id': value.get('offer_id'), 'niche_id': value.get('niche_id'),
            'raw_sha256': hashlib.sha256(json.dumps(value['mcp_result'], sort_keys=True, ensure_ascii=False).encode()).hexdigest(),
            'advertising_cost_inferred': False, 'supplier_authenticity_verified': False}


def observed_value(evidence, field):
    text(field, 'source field', 200)
    node = evidence['row']
    for key in field.split('.'):
        if isinstance(node, dict) and key in node:
            node = node[key]
        elif isinstance(node, list) and key.isdigit() and int(key) < len(node):
            node = node[int(key)]
        else:
            raise ValueError('source field absent')
    return number(node)


def cost(name, item, candidate, evidence):
    fields(item, ['value', 'unit', 'basis', 'source', 'as_of', 'note', 'field'])
    amount = number(item.get('value'))
    if name in POSITIVE and amount <= 0:
        raise ValueError('positive amount required')
    if item.get('unit') != UNITS[name]:
        raise ValueError('wrong or missing unit')
    date(item.get('as_of'))
    text(item.get('note'), 'cost basis / explicit zero reason', 1000)
    source = text(item.get('source'), 'cost source', 200)
    if item.get('basis') == 'observed':
        ref = evidence.get(source)
        if ref is None or ref['state'] != 'matched' or ref['target_asin'] != candidate['target_asin']:
            raise ValueError('wrong ASIN or missing matched source')
        if item['as_of'] != ref['captured_at']:
            raise ValueError('source timestamp mismatch')
        field = item.get('field')
        # Only these direct price observations have a sufficiently clear unit contract.
        # Fees, currency rates, quantities and forecasts require explicit scenarios.
        allowed = (name == 'purchase_cny' and ref['method'] in SUPPLIERS and field == 'price'
                   and ref['offer_id'] == candidate['offer_id'] and source == candidate['supplier_source'])
        allowed = allowed or (name == 'sale_usd' and ref['method'] == 'keepa/productRequest' and field == 'price')
        allowed = allowed or (name == 'sale_usd' and ref['method'] == 'keepa/productSeries'
                              and isinstance(field, str) and re.fullmatch(r'buyboxPrice\.\d+\.value', field))
        observed = observed_value(ref, field) if allowed else None
        if allowed and name == 'sale_usd' and ref['method'] == 'keepa/productSeries':
            point = ref['row']['buyboxPrice'][int(field.split('.')[1])]
            timestamp = point.get('time')
            if not isinstance(timestamp, (str, int, float)) or isinstance(timestamp, bool) or str(timestamp).strip() == '':
                raise ValueError('historical price timestamp missing')
        if not allowed or observed != amount:
            raise ValueError('field, supplier, unit or amount does not match direct evidence')
    elif item.get('basis') == 'user_scenario':
        if 'field' in item:
            raise ValueError('scenario must not claim an observed field')
    else:
        raise ValueError('explicit observed or user_scenario basis required')
    return amount


def money(value):
    return str(value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))


def calculate(value):
    fields(value, ['scenario_id', 'observations', 'candidates'])
    scenario = text(value.get('scenario_id'), 'scenario ID', 100)
    observations, candidates = value.get('observations'), value.get('candidates')
    if not isinstance(observations, list) or len(observations) > 60:
        raise ValueError('bounded raw observations required')
    if not isinstance(candidates, list) or not 1 <= len(candidates) <= 40:
        raise ValueError('1..40 explicit candidates required')
    evidence, failures = {}, {}
    for original in observations:
        if not isinstance(original, dict):
            raise ValueError('raw observation must be an object')
        key = text(original.get('source_operation_id'), 'source operation', 200)
        if key in evidence or key in failures:
            raise ValueError('duplicate source operation; do not overwrite evidence')
        try:
            evidence[key] = observe(original)
        except ValueError as error:
            failures[key] = str(error)
    output, identities = [], set()
    for candidate in candidates:
        fields(candidate, ['target_asin', 'market', 'offer_id', 'variant', 'supplier_source', 'quote', 'costs'])
        target = asin(candidate.get('target_asin'))
        if candidate.get('market') != 'US':
            raise ValueError('candidate market must be US')
        offer = text(candidate.get('offer_id'), 'offer ID', 100)
        variant = text(candidate.get('variant'), 'explicit supplier variant', 200)
        identity = (target, offer, variant)
        if identity in identities:
            raise ValueError('duplicate candidate identity')
        identities.add(identity)
        missing, amounts = [], {}
        supplier = evidence.get(candidate.get('supplier_source'))
        if not supplier or supplier['state'] != 'matched' or supplier['method'] not in SUPPLIERS or supplier['target_asin'] != target or supplier['offer_id'] != offer:
            missing.append('supplier: exact target/offer source absent or mismatched')
        quote = candidate.get('quote')
        try:
            fields(quote, ['variant', 'purchase_quantity', 'minimum_order_quantity', 'price_basis', 'confirmed_at', 'source', 'note'])
            if quote.get('variant') != variant or quote.get('price_basis') != 'CNY/purchase_unit':
                raise ValueError('quote variant/unit not confirmed')
            quantity, moq = number(quote.get('purchase_quantity')), number(quote.get('minimum_order_quantity'))
            if quantity <= 0 or moq <= 0 or quantity != quantity.to_integral_value() or moq != moq.to_integral_value() or quantity < moq:
                raise ValueError('purchase quantity does not meet explicit MOQ')
            if supplier and supplier['state'] == 'matched' and supplier['row'].get('quantityBegin') is not None:
                listed_moq = number(supplier['row']['quantityBegin'])
                if quantity < listed_moq or moq < listed_moq:
                    raise ValueError('quote contradicts supplier listed MOQ; obtain revised evidence')
            date(quote.get('confirmed_at'))
            text(quote.get('source'), 'quote source')
            text(quote.get('note'), 'variant and price tier confirmation', 1000)
        except ValueError as error:
            missing.append('quote: ' + str(error))
        costs = candidate.get('costs', {})
        fields(costs, UNITS)
        for name in UNITS:
            try:
                amounts[name] = cost(name, costs.get(name), candidate, evidence)
            except ValueError as error:
                missing.append(name + ': ' + str(error))
        result = {**candidate, 'state': 'incomplete', 'missing': missing, 'unit_contribution_usd': None,
                  'margin_on_net_revenue_percent': None, 'monthly_profit': None, 'rank': None}
        if not missing:
            a = amounts
            cogs = a['purchase_cny'] / a['fx_cny_per_usd'] * a['purchase_units_per_sale']
            if a['return_rate'] > 1 or a['refunded_revenue_usd'] > a['sale_usd'] or a['referral_refund_usd'] > a['referral_usd'] or a['recovery_usd'] > cogs + a['inbound_usd']:
                missing.append('inconsistent return/refund/recovery assumptions')
            else:
                base_cost = cogs + sum(a[n] for n in ['inbound_usd', 'fba_usd', 'referral_usd', 'advertising_usd', 'storage_usd', 'placement_usd', 'other_usd'])
                incremental = a['refunded_revenue_usd'] - a['referral_refund_usd'] + a['refund_admin_usd'] + a['return_handling_usd'] - a['recovery_usd']
                adjustment = a['return_rate'] * incremental
                profit = a['sale_usd'] - base_cost - adjustment
                revenue = a['sale_usd'] - a['return_rate'] * a['refunded_revenue_usd']
                result.update(state='scenario_complete', purchase_cost_usd=money(cogs), base_cost_usd=money(base_cost),
                              return_adjustment_usd=money(adjustment), expected_net_revenue_usd=money(revenue),
                              unit_contribution_usd=money(profit),
                              margin_on_net_revenue_percent=money(profit / revenue * 100) if revenue > 0 else None)
        output.append(result)
    # Rank only within the exact Amazon target and the explicit scenario; never multiply by competitor sales.
    for target in {r['target_asin'] for r in output}:
        complete = [r for r in output if r['target_asin'] == target and r['state'] == 'scenario_complete']
        for index, result in enumerate(sorted(complete, key=lambda r: Decimal(r['unit_contribution_usd']), reverse=True), 1):
            result['rank'] = index
    return {'state': 'scenarios_reviewed', 'scenario_id': scenario, 'model': 'unit-contribution-v1',
            'candidates': output, 'evidence': evidence, 'source_failures': failures,
            'claims': '单位贡献利润情景；不是净利润承诺、同款认证、供应商资质证明或月销量预测。所有成本与假设见明细。'}


def render_report(result):
    # Text-only, escaped local report: no injected model HTML, scripts, remote media or CDN.
    sections = []
    for row in result['candidates']:
        label = f"{row['target_asin']} · {row['offer_id']} · {row['variant']}"
        profit = row['unit_contribution_usd']
        sections.append('<section><h2>' + html.escape(label) + '</h2><p>' +
                        ('缺项待补，不参与排名' if profit is None else '单位贡献利润情景 USD ' + html.escape(profit)) +
                        '</p><pre>' + html.escape(json.dumps(row, ensure_ascii=False, indent=2)) + '</pre></section>')
    return ('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width">'
            '<title>1688货源与贡献利润情景</title><style>body{font:15px/1.7 system-ui;margin:40px auto;padding:0 24px;max-width:1000px;color:#24282b;background:#fff}section{border-top:1px solid #e4e7e9;padding:20px 0}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f6f7f8;padding:20px;border-radius:12px}h1{font-size:26px}h2{font-size:19px}</style><h1>1688货源与贡献利润情景</h1><p>' + html.escape(result['claims']) + '</p>' + ''.join(sections) +
            '<h2>来源与失败记录</h2><pre>' + html.escape(json.dumps({'evidence': result['evidence'], 'source_failures': result['source_failures']}, ensure_ascii=False, indent=2)) + '</pre></html>')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'observe', 'calculate'])
    parser.add_argument('--input', required=True)
    parser.add_argument('--output-dir', required=True)
    args = parser.parse_args()
    source = Path(args.input)
    if source.stat().st_size > 2 * 1024 * 1024:
        raise ValueError('input exceeds 2 MiB')
    raw = source.read_bytes()
    result = globals()[args.action](json.loads(raw.decode('utf-8-sig')))
    result.update(schema_version=1, service_id='linkfox', input_sha256=hashlib.sha256(raw).hexdigest(),
                  authority='Local artifact only; actual Native tool history and approvals remain authoritative')
    requested = Path(args.output_dir)
    target = requested.parent.resolve(strict=True) / requested.name
    if target == Path.cwd().resolve() or not target.is_relative_to(Path.cwd().resolve()):
        raise ValueError('output must be a new task workspace subdirectory')
    encoded = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n'
    report = render_report(result) if args.action == 'calculate' else None
    target.mkdir()
    (target / 'input.json').write_bytes(raw)
    (target / 'inspection.json').write_text(encoded, encoding='utf-8')
    if report is not None:
        (target / 'report.html').write_text(report, encoding='utf-8')
    print(json.dumps({'directory': str(target), 'state': result['state'], 'external_calls': 0}))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, InvalidOperation) as error:
        raise SystemExit('sourcing review not completed: ' + str(error)) from None
