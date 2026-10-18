"""Explicit-scope local operations diagnosis; Decimal evidence, never business mutations."""
import argparse
import csv
import zipfile
from xml.etree.ElementTree import ParseError
import hashlib
import html
import json
import re
import sys
from collections import defaultdict
from datetime import date
from decimal import Decimal, InvalidOperation, localcontext
from pathlib import Path

from tableio import read_table, cell, MAX_BYTES

MONEY = {'gmv', 'refund_amount', 'spend', 'ad_gmv'}
COUNTS = {'visitors', 'buyers', 'orders', 'cart_users', 'impressions', 'clicks',
          'ad_orders', 'refund_orders', 'consultations', 'replied_3min', 'shipments', 'on_time_shipments'}
RATES = {'refund_rate', 'reply_rate', 'sign_rate'}
KINDS = {
    'overview': {'visitors', 'buyers', 'orders', 'gmv', 'refund_amount'},
    'products': {'visitors', 'buyers', 'orders', 'gmv', 'cart_users', 'refund_amount'},
    'ads': {'spend', 'ad_gmv', 'impressions', 'clicks', 'ad_orders'},
    'traffic': {'visitors', 'buyers', 'orders', 'gmv'},
    'orders': {'gmv', 'refund_amount'},
    'after_sales': {'refund_amount', 'refund_orders', 'refund_rate'},
    'service': {'consultations', 'replied_3min', 'reply_rate', 'shipments', 'on_time_shipments', 'sign_rate'},
    'scores': {'score'},
}
TEXT = {'date', 'id', 'platform', 'store', 'system'}
SCORE_SYSTEMS = {'pdd': {'店铺领航员', '消费者服务体验分', '店铺综合体验星级'},
                 'taobao': {'真实体验分', 'DSR'}, 'tmall': {'真实体验分', 'DSR'}}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def number_text(value):
    if value is None:
        return None
    return format(value.normalize(), 'f') if value else '0'


def json_text(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + '\n'


def require(value, message):
    if not value:
        raise ValueError(message)


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def parse_date(raw):
    text = str(raw).strip()
    require(bool(re.fullmatch(r'\d{4}-\d{2}-\d{2}(?:T00:00:00)?', text)), 'Date must be ISO YYYY-MM-DD without an intraday time')
    return date.fromisoformat(text[:10]).isoformat()


def numeric(c, unit, field):
    raw = str(c['raw']).strip()
    if not raw or raw in ('--', '-', 'N/A', 'null'):
        return None, 'missing'
    if c['kind'] in ('formula', 'unsupported', 'date'):
        return None, 'export_values_required'
    if field in MONEY:
        valid_units = {'CNY'}
    elif field in COUNTS:
        valid_units = {'count'}
    elif field in RATES or field == 'gross_margin':
        valid_units = {'percent', 'fraction'}
    else:
        valid_units = {'percent', 'fraction', 'points', 'stars'}
    if unit not in valid_units:
        return None, 'unit_required_or_incompatible'
    pct = raw.endswith('%')
    if pct:
        if unit != 'percent':
            return None, 'percent_text_requires_percent_unit'
        raw = raw[:-1].strip()
    # Do not guess locale thousands separators, currencies or percentage scales.
    if not re.fullmatch(r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)', raw) or len(raw) > 40:
        return None, 'invalid_number'
    try:
        value = Decimal(raw)
    except InvalidOperation:
        return None, 'invalid_number'
    if not value.is_finite() or abs(value) > Decimal('1e18'):
        return None, 'number_out_of_range'
    if c['kind'] == 'percent':
        if unit not in ('percent', 'fraction'):
            return None, 'excel_percent_unit_mismatch'
        # XLSX percent style stores an already-normalized fraction.
        if pct:
            return None, 'ambiguous_excel_percent'
    elif unit == 'percent':
        value /= 100
    if value < 0:
        return None, 'negative_value_requires_separate_adjustment_analysis'
    if (field in RATES or field == 'gross_margin' or unit in ('percent', 'fraction')) and value > 1:
        return None, 'ratio_out_of_range'
    if field in COUNTS and value != value.to_integral_value():
        return None, 'count_must_be_integer'
    return value, None


def ratio(a, b):
    if a is None or b is None or b == 0:
        return None
    return number_text(a / b)


def analyze(config, base, profile):
    require(isinstance(config, dict) and config.get('schema_version') == 1, 'schema_version must be 1')
    platform, store = config.get('platform'), config.get('store')
    require(platform in profile['platforms'] and nonempty(store), 'Explicit supported platform and store required')
    require(config.get('currency') == 'CNY', 'Only explicit CNY input is supported')
    window = config.get('window', {})
    require(isinstance(window, dict), 'Explicit window object required')
    start, end = parse_date(window.get('start', '')), parse_date(window.get('end', ''))
    require(start <= end, 'Window start must not follow end')
    datasets = config.get('datasets')
    require(isinstance(datasets, list) and 0 < len(datasets) <= 32, 'Provide 1–32 explicit datasets; no sample fallback')
    ids, issues, inventory = set(), [], []
    groups = {}
    seen_files = {}
    for ds in datasets:
        require(isinstance(ds, dict), 'Dataset must be an object')
        ident = ds.get('id')
        require(nonempty(ident) and ident not in ids, 'Dataset id must be unique')
        ids.add(ident)
        kind, basis = ds.get('kind'), ds.get('basis')
        # Incorrectly scoped files remain visible as gaps; never silently infer their platform/type.
        if (ds.get('platform') != platform or ds.get('store') != store or
                kind not in KINDS or not nonempty(basis) or not nonempty(ds.get('source'))):
            issues.append({'dataset': ident, 'reason': 'scope_type_basis_or_source_unconfirmed', 'severity': 'gap'})
            continue
        require(ds.get('grain') in ('day', 'day_entity'), 'Explicit day/day_entity grain required')
        require(kind not in ('products', 'ads', 'traffic', 'orders', 'scores') or ds['grain'] == 'day_entity', 'This table requires day_entity grain')
        columns = ds.get('columns')
        require(isinstance(columns, dict) and 'date' in columns and any(k in KINDS[kind] for k in columns), 'Date and a supported metric mapping required')
        require(set(columns) <= TEXT | KINDS[kind], 'Unknown or wrong-kind mapped metric')
        require(ds['grain'] != 'day_entity' or 'id' in columns, 'Entity id mapping required')
        require(ds['grain'] != 'day' or 'id' not in columns, 'Day grain is one store row per date; use day_entity for ids')
        require(kind != 'scores' or 'system' in columns, 'Score system mapping required')
        require(all(isinstance(c, dict) and nonempty(c.get('header')) for c in columns.values()), 'Every mapping needs an exact header')
        require(len({c['header'] for c in columns.values()}) == len(columns), 'A header must not map to multiple fields')
        for field, c in columns.items():
            if field not in TEXT:
                require(nonempty(c.get('unit')), 'Explicit units required for '+field)
        header_row = ds.get('header_row')
        require(type(header_row) is int and header_row > 0, 'Explicit positive header_row required')
        require(nonempty(ds.get('path')), 'Dataset path required')
        path = (base / ds['path']).resolve()
        require(path.is_file(), 'Dataset file not found: '+ident)
        require(path.stat().st_size <= MAX_BYTES, 'Input exceeds 16 MiB')
        filehash = digest(path.read_bytes())
        sheet, table = read_table(path, ds.get('sheet'))
        require(filehash == digest(path.read_bytes()), 'Source changed while reading; retry with a stable export')
        filekey = (str(path), sheet)
        require(filekey not in seen_files, 'Same file/sheet supplied twice; supply it once')
        seen_files[filekey] = ident
        inventory.append({'dataset': ident, 'path': str(path), 'sha256': filehash, 'sheet': sheet,
                          'kind': kind, 'platform': platform, 'store': store, 'basis': basis, 'source': ds['source']})
        headers = next((values for row, values in table if row == header_row), None)
        require(headers is not None, 'Header row not found: '+ident)
        require(all(c['kind'] not in ('formula', 'unsupported') for c in headers), 'Invalid header values')
        names = [str(c['raw']).strip() for c in headers]
        require(all(names.count(c['header']) == 1 for c in columns.values()), 'Mapped header missing or duplicated: '+ident)
        positions = {field: names.index(c['header']) for field, c in columns.items()}
        # Same kind but different declared attribution basis/grain is never combined.
        key = (kind, basis, ds['grain'], ('fraction' if columns.get('score', {}).get('unit') == 'percent' else columns.get('score', {}).get('unit')) if kind == 'scores' else None)
        group = groups.setdefault(key, {'kind': kind, 'basis': basis, 'grain': ds['grain'], 'datasets': [], 'rows': [], 'excluded': [], 'metrics': set(), 'units': {}})
        group['datasets'].append(ident)
        group['metrics'].update(k for k in columns if k not in TEXT)
        for field in KINDS[kind] & columns.keys():
            unit = columns[field]['unit']
            normalized_unit = 'fraction' if unit == 'percent' else unit
            if field in group['units']:
                require(group['units'][field] == normalized_unit, 'Metric units differ within a basis; use distinct basis')
            group['units'][field] = normalized_unit
        for line, values in table:
            if line <= header_row or not any(str(c['raw']).strip() for c in values):
                continue
            cells = {field: values[pos] if pos < len(values) else cell() for field, pos in positions.items()}
            location = {'dataset': ident, 'sheet': sheet, 'row': line}
            reason = None
            try:
                require(cells['date']['kind'] not in ('formula', 'unsupported'), 'Date value required')
                day = parse_date(cells['date']['raw'])
            except ValueError:
                day, reason = None, 'missing_or_invalid_date'
            if day is not None and not start <= day <= end:
                issues.append({**location, 'reason': 'outside_window', 'severity': 'excluded'})
                continue
            for field, expected in (('platform', platform), ('store', store)):
                if field in cells and str(cells[field]['raw']).strip() != expected:
                    reason = 'foreign_or_unknown_'+field
            entity = str(cells.get('id', cell('store'))['raw']).strip()
            if not entity or cells.get('id', cell())['kind'] in ('formula', 'unsupported'):
                reason = 'entity_id_required'
            system = str(cells.get('system', cell())['raw']).strip()
            if kind == 'scores' and system not in SCORE_SYSTEMS[platform]:
                reason = 'unknown_score_system'
            if any(c['kind'] in ('formula', 'unsupported') for k, c in cells.items() if k in TEXT):
                reason = 'literal_scope_identity_and_date_values_required'
            if reason:
                gap = {**location, 'reason': reason, 'severity': 'gap'}
                issues.append(gap)
                group['excluded'].append(gap)
                continue
            fields, evidence = {}, {}
            for field, c in cells.items():
                unit = columns[field].get('unit')
                source = {**location, 'header': columns[field]['header'], 'raw': c.get('stored_raw', c['raw']), 'decoded': c['raw'], 'storage': c['kind'], 'unit': unit}
                if field in TEXT:
                    source['value'] = str(c['raw'])
                else:
                    value, error = numeric(c, unit, field)
                    fields[field] = number_text(value)
                    source.update(value=fields[field], reason=error, normalized_unit='fraction' if unit == 'percent' else unit)
                    if error:
                        issues.append({**location, 'field': field, 'reason': error, 'severity': 'gap'})
                evidence[field] = source
            if kind == 'scores':
                scales = ds.get('score_scales', {})
                require(isinstance(scales, dict), 'score_scales must map systems to declared scales')
                scale = scales.get(system)
                if not isinstance(scale, dict) or not all(nonempty(scale.get(k)) for k in ('min', 'max', 'source')):
                    gap = {**location, 'reason': 'explicit_score_scale_and_source_required', 'severity': 'gap'}
                    issues.append(gap); group['excluded'].append(gap)
                    continue
                low, er1 = numeric(cell(scale['min']), columns['score']['unit'], 'score')
                high, er2 = numeric(cell(scale['max']), columns['score']['unit'], 'score')
                require(not er1 and not er2 and low <= high, 'Invalid score scale')
                val = fields.get('score')
                if val is not None and not low <= Decimal(val) <= high:
                    fields['score'] = None
                    evidence['score'].update(value=None, reason='outside_declared_score_scale')
                    issues.append({**location, 'reason': 'outside_declared_score_scale', 'severity': 'gap'})
                evidence['score']['scale'] = scale
            group['rows'].append({'date': day, 'id': entity, 'system': system, 'values': fields, 'evidence': evidence})
    results = []
    for group in groups.values():
        candidates = defaultdict(list)
        for row in group['rows']:
            candidates[(row['date'], row['id'], row['system'])].append(row)
        accepted, duplicates = [], []
        for key, rows in candidates.items():
            signatures = {json.dumps({'values': row['values'], 'scale': row['evidence'].get('score', {}).get('scale')}, sort_keys=True) for row in rows}
            if len(signatures) > 1:
                gap = {'reason': 'conflicting_duplicate', 'key': list(key), 'sources': [r['evidence']['date'] for r in rows], 'severity': 'gap'}
                issues.append(gap); group['excluded'].append(gap)
            else:
                row = rows[0]
                row['duplicate_sources'] = [r['evidence']['date'] for r in rows[1:]]
                accepted.append(row)
                duplicates.extend(row['duplicate_sources'])
        accepted.sort(key=lambda r: (r['date'], r['id'], r['system']))
        aggregates = {}
        for field in sorted(group['metrics']):
            vals = [Decimal(r['values'][field]) for r in accepted if r['values'].get(field) is not None]
            is_additive = field in MONEY | COUNTS
            complete = bool(accepted) and len(vals) == len(accepted) and not group['excluded']
            # Rates/scores are snapshots; never sum or take an unweighted average.
            aggregates[field] = {'unit': group['units'][field], 'known_rows': len(vals), 'accepted_rows': len(accepted),
                                 'missing_rows': len(accepted)-len(vals), 'excluded_rows': len(group['excluded']),
                                 'known_subtotal': number_text(sum(vals, Decimal(0))) if vals and is_additive else None,
                                 'total': number_text(sum(vals, Decimal(0))) if complete and is_additive else None,
                                 'coverage': 'complete_observed_rows' if complete else 'incomplete',
                                 'meaning': 'day/entity-count sum, not period-unique people' if field in ('visitors', 'buyers', 'cart_users') else ('additive within declared basis' if is_additive else 'row snapshots only')}
        def total(field):
            value = aggregates.get(field, {}).get('total')
            return Decimal(value) if value is not None else None
        derived = {}
        for name, num, den in [('buyers_per_visitor_daily_basis', 'buyers', 'visitors'), ('click_through_rate', 'clicks', 'impressions'), ('ad_roi', 'ad_gmv', 'spend'), ('reply_rate_from_counts', 'replied_3min', 'consultations'), ('on_time_shipment_rate', 'on_time_shipments', 'shipments')]:
            if num in group['metrics'] or den in group['metrics']:
                value = ratio(total(num), total(den))
                if name != 'ad_roi' and value is not None and Decimal(value) > 1:
                    issues.append({'datasets': group['datasets'], 'reason': 'inconsistent_numerator_denominator', 'metric': name, 'severity': 'gap'})
                    value = None
                derived[name] = {'value': value, 'formula': num+' / '+den, 'reason': None if value is not None else 'missing_incomplete_or_zero_denominator_or_inconsistent_counts'}
        finance = None
        if group['kind'] == 'ads':
            finance = {'gross_margin': None, 'mode': None, 'contribution': None, 'breakeven_roi': None, 'loss_per_ad_yuan': None,
                       'label': '广告归因毛利贡献（不是净利润，未另行扣除退款/费用/税费；是否含这些项目以毛利口径为准）', 'reason': 'explicit_margin_required'}
            margin = config.get('gross_margin')
            if margin is not None:
                require(isinstance(margin, dict) and margin.get('mode') in ('confirmed', 'scenario') and nonempty(margin.get('source')) and nonempty(margin.get('basis')), 'Margin needs mode, source and basis')
                require(margin['basis'] == group['basis'], 'Margin basis must match advertising basis; split reports for different assumptions')
                m, err = numeric(cell(margin.get('value', '')), margin.get('unit'), 'gross_margin')
                if err:
                    finance['reason'] = err
                else:
                    finance.update(gross_margin=number_text(m), gross_margin_unit='fraction', mode=margin['mode'], source=margin['source'], basis=margin['basis'])
                    spend, revenue = total('spend'), total('ad_gmv')
                    finance['breakeven_roi'] = ratio(Decimal(1), m)
                    if spend is not None and revenue is not None:
                        contribution = revenue * m - spend
                        finance.update(contribution=number_text(contribution), loss_per_ad_yuan=ratio(max(Decimal(0), -contribution), spend), reason=None)
                    else:
                        finance['reason'] = 'advertising_revenue_or_spend_incomplete'
        snapshots = []
        if group['kind'] == 'scores':
            latest = {}
            for row in accepted:
                latest[(row['system'], row['id'])] = row
            snapshots = list(latest.values())
        results.append({'kind': group['kind'], 'basis': group['basis'], 'grain': group['grain'], 'datasets': group['datasets'],
                        'rows': accepted, 'excluded': group['excluded'], 'duplicate_sources': duplicates,
                        'aggregates': aggregates, 'derived': derived, 'finance': finance, 'latest_score_snapshots': snapshots})
    incomplete = any(a['coverage'] == 'incomplete' for g in results for a in g['aggregates'].values())
    status = 'needs_input' if not any(r['rows'] for r in results) else ('partial' if incomplete or any(i['severity'] == 'gap' for i in issues) else 'observed_scope_only')
    return {'schema_version': 1, 'expert_id': profile['expert_id'], 'expert_version': profile['version'], 'status': status,
            'scope': {'platform': platform, 'store': store, 'window': {'start': start, 'end': end}, 'currency': 'CNY'},
            'inventory': inventory, 'groups': results, 'issues': issues,
            'limits': ['Only supplied, explicitly mapped records; row completeness is not proof of full platform export coverage.',
                       'Different basis/grain/table groups are not combined. Daily visitor counts are not period-unique visitors.',
                       'No default margin/fees, net profit, platform thresholds, health score or predicted revenue uplift.',
                       'Score snapshots are independent systems; an absent latest-day record is not imputed.',
                       'No login, API, network, advertising mutation or database access.']}


def render(report):
    esc = lambda value: html.escape(str(value), quote=True)
    def table(headers, rows):
        return '<table><thead><tr>'+''.join('<th>'+esc(x)+'</th>' for x in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+esc('待补充' if x is None else x)+'</td>' for x in row)+'</tr>' for row in rows)+'</tbody></table>'
    scope = report['scope']
    sections = []
    sections.append(('01 口径与数据质量', '<p>'+esc(json.dumps(scope, ensure_ascii=False))+'</p><p>状态：'+esc(report['status'])+'。完整仅指已提交且通过范围校验的记录；不能证明平台全量。日去重访客累计不等于周期独立访客。</p>'))
    sections.append(('02 来源清单', table(['数据集', '文件/工作表', '口径', '来源声明', 'SHA256'], [[x['dataset'], x['path']+' / '+x['sheet'], x['basis'], x['source'], x['sha256']] for x in report['inventory']])))
    sections.append(('03 已知指标与覆盖', ''.join('<h3>'+esc(g['kind']+' · '+g['basis'])+'</h3>'+table(['指标','单位','完整总额','已知小计','已知/有效行','排除行','含义'], [[k,v['unit'],v['total'] if k in MONEY | COUNTS else '不适用（按行快照）',v['known_subtotal'] if k in MONEY | COUNTS else '不适用（按行快照）',str(v['known_rows'])+'/'+str(v['accepted_rows']),v['excluded_rows'],v['meaning']] for k,v in g['aggregates'].items()]) for g in report['groups'])))
    sections.append(('04 可复算派生指标', ''.join('<h3>'+esc(g['kind']+' · '+g['basis'])+'</h3>'+table(['指标','公式','值','缺口'], [[k,v['formula'],v['value'],v['reason'] or '—'] for k,v in g['derived'].items()]) for g in report['groups'] if g['derived'])))
    finance_labels = {'gross_margin': '毛利率（分数）', 'mode': '参数属性', 'contribution': '广告归因毛利贡献（元）', 'breakeven_roi': '毛利保本 ROI', 'loss_per_ad_yuan': '每广告元毛利亏损（元）', 'label': '核算边界', 'reason': '计算缺口', 'gross_margin_unit': '毛利率单位', 'source': '毛利来源', 'basis': '归因口径'}
    def finance_value(key, value):
        if key == 'reason' and value is None:
            return '无计算缺口'
        if key == 'mode':
            return {'confirmed': '本次输入已确认', 'scenario': '用户假设情景'}.get(value, value)
        return value
    sections.append(('05 广告贡献与情景', ''.join('<h3>'+esc(g['basis'])+'</h3>'+table(['项目','值'], [[finance_labels[k],finance_value(k,v)] for k,v in g['finance'].items()]) for g in report['groups'] if g['finance']) or '<p>未提供广告数据。不能推断投放盈亏。</p>'))
    sections.append(('06 商品与流量分析', '<p>商品、渠道、订单与总览分组分别展示，禁止跨表相加。每组最多展示前200行，完整明细及单元格证据见report.json。没有同行基准和用户目标时，不生成排名好坏、健康分或虚构增长预测。</p>'+''.join('<h3>'+esc(g['kind']+' · '+g['basis'])+'</h3>'+table(['日期','对象','指标值','行来源'], [[r['date'],r['id'],json.dumps(r['values'],ensure_ascii=False),json.dumps(r['evidence']['date'],ensure_ascii=False)] for r in g['rows'][:200]]) for g in report['groups'] if g['kind'] in ('products','traffic','orders','overview'))))
    def displayed_snapshot(row, metric):
        value = row['values'].get(metric)
        unit = row['evidence'][metric]['normalized_unit']
        if value is not None and unit == 'fraction':
            return number_text(Decimal(value) * 100), '%'
        return value, {'points': '分', 'stars': '星'}.get(unit, unit)
    score_tables = ''.join(table(['体系','对象','观测日期','值','单位','量表来源'], [[r['system'],r['id'],r['date'],*displayed_snapshot(r,'score'),r['evidence']['score']['scale']['source']] for r in g['latest_score_snapshots']]) for g in report['groups'] if g['kind']=='scores')
    rate_tables = ''.join('<h3>'+esc(g['kind']+' · '+g['basis'])+'</h3>'+table(['观测日期','对象','比例指标','值','单位','来源行'], [[r['date'],r['id'],k,*displayed_snapshot(r,k),json.dumps(r['evidence'][k],ensure_ascii=False)] for r in g['rows'][:200] for k in sorted(RATES & r['values'].keys())]) for g in report['groups'] if any(k in RATES for k in g['aggregates']))
    sections.append(('07 独立评分与比例时点', (score_tables or '<p>未提供明确评分体系及尺度。</p>')+'<h3>比例快照（不汇总、不平均）</h3>'+(rate_tables or '<p>未提供比例快照。</p>')))
    sections.append(('08 数据缺口与排除', table(['定位','原因'], [[json.dumps({k:v for k,v in i.items() if k != 'reason'},ensure_ascii=False),i['reason']] for i in report['issues']]) if report['issues'] else '<p>无已检测缺口。</p>'))
    sections.append(('09 下一步工作表', table(['动作','依据','完成标准'], [['核对范围/单位/来源','本报告来源清单及缺口','补齐已列缺口，用新目录重新生成'],['人工复核经营动作','用户目标、毛利口径、实际指标','建议与已确认事实分开，未授权不改价或改投放'],['核验时效规则','原知识库为有日期的参考资料','当前官方公告或商家后台证据；无证据保留待确认']])) )
    sections.append(('10 结论与交付边界', '<p>本报告提供已给资料的可追溯核算与缺口。不是净利润审计、平台处罚判断或自动投放方案。需要业务解读时，专家应引用具体数据集/行/指标，另存review.md，不能把建议或情景当成已发生事实。</p><p>完整原始值、单位、工作表、行号、列名、冲突与重复记录见report.json。输入清单input.json和receipt.json可复核文件摘要。</p>'))
    body=''.join('<section><h2>'+title+'</h2>'+content+'</section>' for title,content in sections)
    return '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>经营诊断 · '+esc(scope['store'])+'</title><style>body{font:15px/1.7 -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif;color:#252a2c;background:#f7f8f8;margin:0;padding:32px}main{max-width:1180px;margin:auto}h1{font-size:28px}h2{font-size:19px}h3{font-size:16px}section{background:white;border:1px solid #e2e5e6;border-radius:12px;padding:24px;margin:20px 0;overflow:auto}table{border-collapse:collapse;width:100%;font-size:13px}th,td{text-align:left;border-bottom:1px solid #eee;padding:9px;vertical-align:top;overflow-wrap:anywhere}th{background:#f4f6f5}p{max-width:90ch}</style><main><h1>'+esc(scope['store'])+' · 经营诊断</h1><p>'+esc(scope['platform'])+' / '+esc(scope['window']['start'])+' — '+esc(scope['window']['end'])+'</p>'+body+'</main></html>\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    input_path = args.input.resolve()
    root = Path(__file__).resolve().parents[1]
    out = args.out.resolve()
    require(out != root and root not in out.parents, 'Output must be outside installed expert resources')
    require(not out.exists(), 'Output already exists; choose a new version directory')
    require(input_path.stat().st_size <= 1024 * 1024, 'Manifest exceeds 1 MiB')
    raw = input_path.read_bytes()
    config = json.loads(raw)
    profile = json.loads((root/'profile.json').read_text())
    with localcontext() as ctx:
        ctx.prec = 40
        report = analyze(config, input_path.parent, profile)
        outputs = {'report.json': json_text(report), 'report.html': render(report),
                   'input.json': raw.decode('utf-8'), 'summary.md': '# 经营诊断\n\n状态：'+report['status']+'\n\n平台/店铺：'+report['scope']['platform']+' / '+report['scope']['store']+'\n\n请阅读report.html及report.json中的来源、逐字段证据与缺口。完整仅指已提交记录，非平台全量。建议另存review.md，不覆盖本目录。\n'}
    out.mkdir(parents=True, exist_ok=False)
    receipts = []
    for name, text in outputs.items():
        data = text.encode('utf-8')
        with (out/name).open('xb') as handle:
            handle.write(data)
        receipts.append({'path': name, 'bytes': len(data), 'sha256': digest(data)})
    receipt = {'schema_version': 1, 'expert_id': profile['expert_id'], 'expert_version': profile['version'],
               'input_sha256': digest(raw), 'files': receipts, 'status': report['status']}
    with (out/'receipt.json').open('x', encoding='utf-8') as handle:
        handle.write(json_text(receipt))
    print(json_text({'output': str(out), 'status': report['status'], 'files': len(receipts)+1}).strip())


if __name__ == '__main__':
    try:
        main()
    except (ValueError, KeyError, TypeError, OSError, InvalidOperation, csv.Error, zipfile.BadZipFile, ParseError) as error:
        print('Input/report error: '+str(error), file=sys.stderr)
        sys.exit(2)
