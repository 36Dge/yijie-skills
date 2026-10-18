"""Local research evidence, comparable-company arithmetic and artifact preparation.
Python standard library only; no network, credentials, installs or subprocesses.
"""
import argparse
from datetime import date
from decimal import Decimal, InvalidOperation
import hashlib
import html
import json
from pathlib import Path
import re
from urllib.parse import urlsplit
import sys
sys.dont_write_bytecode = True
from artifacts import workbook

METRICS = ('revenue', 'ebitda', 'net_income', 'market_cap', 'debt', 'cash', 'preferred', 'minority')
SECTIONS = ('overview', 'competition', 'valuation', 'watchlist')
FINANCE_SERVICES = ('eastmoney', 'wind', 'morningstar', 'gildata_finance_data_qwen')


def fields(value, allowed):
    if not isinstance(value, dict) or set(value) - set(allowed):
        raise ValueError('unexpected fields or non-object input')


def text(value, label, maximum=1000):
    if not isinstance(value, str) or not value.strip() or len(value) > maximum or any(ord(c) < 32 and c not in '\n\t\r' for c in value):
        raise ValueError('explicit text required: ' + label)
    return value


def day(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        raise ValueError('ISO date required')
    return date.fromisoformat(value)


def number(value):
    if isinstance(value, bool) or not isinstance(value, (str, int, float)) or len(str(value)) > 40:
        raise ValueError('missing numeric value; unknown is not zero')
    try:
        n = Decimal(str(value))
    except InvalidOperation:
        raise ValueError('invalid decimal') from None
    if not n.is_finite() or abs(n) > Decimal('1e15') or n.as_tuple().exponent < -8:
        raise ValueError('unsupported numeric precision or range')
    return n


def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def digest(value):
    return hashlib.sha256(encode(value).encode()).hexdigest()


def prepare(value):
    fields(value, ['kind', 'query', 'ts_code', 'trade_date', 'service_id', 'tool', 'arguments', 'purpose'])
    kind = value.get('kind')
    if kind == 'search':
        fields(value, ['kind', 'query'])
        service = 'linkfox'
        request = {'toolName': 'aiMode/googleSearch', 'arguments': {'keyword': text(value.get('query'), 'public research query', 1000)}}
        tool = 'proxy_call'
    elif kind == 'price':
        fields(value, ['kind', 'ts_code', 'trade_date'])
        code = value.get('ts_code')
        if not isinstance(code, str) or not re.fullmatch(r'\d{6}\.(SH|SZ|BJ)', code):
            raise ValueError('single A-share code required')
        t = value.get('trade_date')
        if not isinstance(t, str) or not re.fullmatch(r'\d{8}', t):
            raise ValueError('single trading date required')
        day(t[:4]+'-'+t[4:6]+'-'+t[6:])
        service, tool, request = 'tushareMcp', 'tushare_daily', {'ts_code': code, 'trade_date': t}
    elif kind == 'finance':
        fields(value, ['kind', 'service_id', 'tool', 'arguments', 'purpose'])
        service = value.get('service_id')
        if service not in FINANCE_SERVICES:
            raise ValueError('use a supported existing financial connector')
        declared = value.get('tool')
        fields(declared, ['name', 'title', 'inputSchema'])
        title = text(declared.get('title'), 'current Native tool title', 300)
        prefix = service + ' · '
        if not title.startswith(prefix) or not title[len(prefix):]:
            raise ValueError('tool belongs to a different provider')
        expected = 'm_' + hashlib.sha256((service+'\n'+title[len(prefix):]).encode()).hexdigest()[:60]
        if declared.get('name') != expected:
            raise ValueError('use the actual exposed Native tool name; do not invent a method')
        schema = declared.get('inputSchema')
        if not isinstance(schema, dict) or schema.get('type') != 'object':
            raise ValueError('current discovered input schema required')
        request = value.get('arguments')
        if not isinstance(request, dict):
            raise ValueError('explicit arguments object required')
        text(value.get('purpose'), 'specific read/query purpose', 1000)
        # Do not implement a second permissive JSON Schema validator. The existing
        # Native/Broker frozen-schema validator and approval remain mandatory.
        tool = expected
    else:
        raise ValueError('unsupported request kind')
    if len(encode(request).encode()) > 16*1024:
        raise ValueError('arguments exceed existing review capacity')
    return {'state': 'prepared_not_submitted', 'service_id': service, 'tool_name': tool,
            'arguments': request, 'plan_sha256': digest(value), 'schema_validation': 'Native_required',
            'execution_authorized': False}


def observe(value):
    fields(value, ['plan', 'actual_arguments', 'source_operation_id', 'retrieved_on', 'mcp_result', 'actual_service_id', 'actual_tool_name'])
    prepared = prepare(value.get('plan'))
    if value.get('actual_service_id') != prepared['service_id'] or value.get('actual_tool_name') != prepared['tool_name']:
        raise ValueError('actual service/tool differs from plan')
    if value.get('actual_arguments') != prepared['arguments']:
        raise ValueError('actual request differs from plan')
    text(value.get('source_operation_id'), 'actual Native operation ID', 200)
    day(value.get('retrieved_on'))
    result = value.get('mcp_result')
    if not isinstance(result, dict) or result.get('isError'):
        raise ValueError('MCP failed or unknown result')
    if len(encode(result).encode()) > 64*1024:
        raise ValueError('MCP result exceeds existing bound')
    if 'structuredContent' in result:
        body = result['structuredContent']
    else:
        content = result.get('content')
        if not isinstance(content, list) or len(content) != 1 or not isinstance(content[0], dict) or content[0].get('type') != 'text':
            raise ValueError('ambiguous MCP text result')
        raw = text(content[0].get('text'), 'result text', 64*1024)
        try:
            body = json.loads(raw)
        except ValueError:
            body = raw
    if isinstance(body, dict):
        # Finance provider success envelopes are provider-specific; keep them
        # uninterpreted unless a known error is present. Never declare facts verified.
        if body.get('success') is False or body.get('error'):
            raise ValueError('provider reported failure')
        for key in ('errcode', 'errorCode', 'code'):
            if key in body and str(body[key]) not in ('0', '200'):
                raise ValueError('unknown or unsuccessful provider code')
    kind = value['plan']['kind']
    if kind == 'search':
        if not isinstance(body, dict) or not isinstance(body.get('stdout'), str) or not body['stdout'].strip():
            raise ValueError('empty or unknown search response')
        state = 'discovery_only'
    elif kind == 'price':
        if not isinstance(body, dict) or not isinstance(body.get('rows'), list) or len(body['rows']) != 1:
            raise ValueError('expected the Native single-row daily result')
        row = body['rows'][0]
        if not isinstance(row, dict) or any(row.get(k) != prepared['arguments'][k] for k in ('ts_code', 'trade_date')):
            raise ValueError('price security/date mismatch')
        if number(row.get('close')) <= 0:
            raise ValueError('positive close required')
        state = 'unadjusted_price_only'
    else:
        if body in (None, '', [], {}):
            raise ValueError('empty financial response')
        state = 'source_requires_review'
    return {**prepared, 'state': state, 'source_operation_id': value['source_operation_id'],
            'retrieved_on': value['retrieved_on'], 'body': body, 'result_sha256': digest(result),
            'verified_financial_facts': False}


def source_map(items, cutoff):
    if not isinstance(items, list) or not 1 <= len(items) <= 100:
        raise ValueError('1..100 source records required')
    sources = {}
    for item in items:
        fields(item, ['id', 'kind', 'title', 'locator', 'published_on', 'retrieved_on', 'content', 'receipt', 'entity_ids', 'period_ends'])
        key = text(item.get('id'), 'source ID', 80)
        if key in sources:
            raise ValueError('duplicate source ID')
        kind = item.get('kind')
        if kind not in ('issuer', 'exchange', 'provider', 'user', 'search'):
            raise ValueError('explicit source kind required')
        text(item.get('title'), 'source title')
        text(item.get('locator'), 'URL or user file/page reference', 2000)
        published, retrieved = day(item.get('published_on')), day(item.get('retrieved_on'))
        if published > cutoff or retrieved < published:
            raise ValueError('source published after research cutoff or retrieved before publication')
        for index_name in ('entity_ids', 'period_ends'):
            declared = item.get(index_name)
            if not isinstance(declared, list) or len(declared) > 40 or any(not isinstance(x,str) or not x for x in declared) or len(set(declared)) != len(declared):
                raise ValueError('source identity/period index required')
        for period in item['period_ends']:
            day(period)
        content = text(item.get('content'), 'source excerpt/text', 64*1024)
        if kind in ('provider', 'search'):
            receipt = observe(item.get('receipt'))
            expected = 'search' if kind == 'search' else None
            if expected == 'search' and receipt['state'] != 'discovery_only':
                raise ValueError('wrong search receipt')
            if kind == 'provider' and receipt['state'] == 'discovery_only':
                raise ValueError('search summary is not a financial source')
            body_text = receipt['body'] if isinstance(receipt['body'], str) else json.dumps(receipt['body'], ensure_ascii=False, indent=2)
            if content not in body_text or item['retrieved_on'] != receipt['retrieved_on']:
                raise ValueError('excerpt is not in the actual received text')
        elif 'receipt' in item:
            raise ValueError('issuer/user source must retain its actual document attribution')
        sources[key] = {**item, 'content_sha256': hashlib.sha256(content.encode()).hexdigest(),
                        'verification': 'citation consistency only; source authenticity and meaning require review'}
    return sources


def point(name, value, entity, scope, sources):
    fields(value, ['value', 'scale', 'currency', 'basis', 'period_start', 'period_end', 'as_of', 'definition', 'source_id', 'quote'])
    n = number(value.get('value'))
    if name in ('revenue', 'market_cap', 'debt', 'cash', 'preferred', 'minority') and n < 0:
        raise ValueError('negative balance/size input needs separate review')
    scale = value.get('scale')
    if type(scale) is not int or scale not in (1,1000,1000000,1000000000):
        raise ValueError('explicit currency scale required')
    if value.get('currency') != scope['currency']:
        raise ValueError('currency mismatch; no implicit FX conversion')
    operating = name in ('revenue', 'ebitda', 'net_income')
    if value.get('basis') != (scope['basis'] if operating else 'instant'):
        raise ValueError('incompatible fiscal/forecast basis')
    if value.get('period_end') != scope['period_end'] or value.get('period_start') != (scope['period_start'] if operating else None):
        raise ValueError('period mismatch; no quarter annualization')
    expected_date = scope['valuation_date'] if name == 'market_cap' else scope['period_end']
    if value.get('as_of') != expected_date:
        raise ValueError('valuation/balance date mismatch')
    if value.get('definition') != (scope['ebitda_definition'] if name == 'ebitda' else name):
        raise ValueError('metric definition mismatch')
    source = sources.get(value.get('source_id')) if isinstance(value.get('source_id'), str) else None
    if not source or source['kind'] == 'search':
        raise ValueError('missing primary/provider/user source; discovery is not evidence')
    if day(source['published_on']) < day(expected_date):
        raise ValueError('source predates the asserted financial/valuation date')
    quote = text(value.get('quote'), 'exact source quote', 5000)
    # Mechanical citation consistency, not semantic verification of a filing.
    literal = re.escape(str(value['value']))
    exact_number = re.search(r'(?<![\w.,+-])'+literal+r'(?![\w.,])', quote) is not None
    if quote not in source['content'] or entity not in source['entity_ids'] or scope['period_end'] not in source['period_ends'] or not exact_number:
        raise ValueError('quote/value/security/period does not match retained evidence')
    return n * scale / Decimal('1000000')


def shown(n):
    return str(n) if n is not None else None


def analyze(value):
    fields(value, ['title', 'scope', 'sources', 'companies', 'sections'])
    title = text(value.get('title'), 'research title', 200)
    scope = value.get('scope')
    fields(scope, ['currency', 'basis', 'period_start', 'period_end', 'valuation_date', 'ebitda_definition'])
    if scope.get('currency') not in ('CNY','USD','HKD','EUR','GBP','JPY') or scope.get('basis') not in ('FY','LTM'):
        raise ValueError('explicit reporting currency and actual FY/LTM basis required')
    start, end, cutoff = day(scope.get('period_start')), day(scope.get('period_end')), day(scope.get('valuation_date'))
    if not start < end <= cutoff or not 350 <= (end-start).days <= 371:
        raise ValueError('FY/LTM must cover an explicit approximately annual period before valuation')
    text(scope.get('ebitda_definition'), 'shared EBITDA definition', 200)
    sources = source_map(value.get('sources'), cutoff)
    companies = value.get('companies')
    if not isinstance(companies, list) or not 1 <= len(companies) <= 30:
        raise ValueError('1..30 explicit companies required; never silently drop peers')
    seen, output = set(), []
    for company in companies:
        fields(company, ['entity_id', 'name', 'business_model', 'metrics'])
        entity = text(company.get('entity_id'), 'exchange-qualified security identity', 80)
        if entity in seen:
            raise ValueError('duplicate company/security')
        seen.add(entity)
        text(company.get('name'), 'company name', 200)
        text(company.get('business_model'), 'comparability rationale', 2000)
        metrics = company.get('metrics', {})
        fields(metrics, METRICS)
        amounts, issues = {}, {}
        for name in METRICS:
            try:
                amounts[name] = point(name, metrics.get(name), entity, scope, sources)
            except ValueError as e:
                amounts[name], issues[name] = None, str(e)
        ev_fields = ('market_cap','debt','cash','preferred','minority')
        ev = None if any(amounts[k] is None for k in ev_fields) else amounts['market_cap']+amounts['debt']-amounts['cash']+amounts['preferred']+amounts['minority']
        def ratio(a,b):return a/b if a is not None and b is not None and a > 0 and b > 0 else None
        def margin(a,b):return a/b*100 if a is not None and b is not None and b > 0 else None
        derived = {'enterprise_value':ev, 'ev_revenue':ratio(ev,amounts['revenue']), 'ev_ebitda':ratio(ev,amounts['ebitda']),
                   'pe':ratio(amounts['market_cap'],amounts['net_income']), 'ebitda_margin_percent':margin(amounts['ebitda'],amounts['revenue'])}
        output.append({**company, 'normalized_millions':{k:str(v) if v is not None else None for k,v in amounts.items()}, 'derived':{k:shown(v) for k,v in derived.items()}, 'issues':issues,
                       'state':'incomplete' if issues else 'inputs_consistent', 'interpretation':'null multiples mean missing or not meaningful, never zero'})
    sections = value.get('sections')
    fields(sections, SECTIONS)
    for section in SECTIONS:
        claims = sections.get(section)
        if not isinstance(claims, list) or not 1 <= len(claims) <= 40:
            raise ValueError('all four research sections required; use explicit unknowns')
        for claim in claims:
            fields(claim, ['text', 'kind', 'source_ids'])
            text(claim.get('text'), 'research statement', 3000)
            refs = claim.get('source_ids')
            if claim.get('kind') not in ('fact','analysis','unknown') or not isinstance(refs, list) or any(not isinstance(k,str) or k not in sources for k in refs):
                raise ValueError('unknown statement kind/source')
            if claim['kind'] != 'unknown' and (not refs or all(sources[k]['kind']=='search' for k in refs)):
                raise ValueError('facts and analysis need reviewed sources beyond search summaries')
    stats = {}
    for metric in ('ev_revenue','ev_ebitda','pe','ebitda_margin_percent'):
        vals = sorted(Decimal(c['derived'][metric]) for c in output if c['derived'][metric] is not None)
        count = len(vals)
        median = (vals[(count-1)//2]+vals[count//2])/2 if count else None
        stats[metric]={'count':count,'median':shown(median),'min':shown(vals[0]) if count else None,'max':shown(vals[-1]) if count else None}
    return {'state':'research_draft','title':title,'scope':scope,'sources':sources,'companies':output,'sections':sections,'statistics':stats,
            'limitations':['Source identity and numeric citation consistency are not independent verification of the underlying disclosure.',
                           'No automatic FX, forecasts, investment recommendation or publishing. Missing fields and nonpositive valuation denominators stay unknown/NM.']}


def report(result):
    e=html.escape
    headings = {'overview':'行业概览','competition':'竞争格局','valuation':'可比估值','watchlist':'主题观察清单'}
    kinds = {'fact':'已引证事实','analysis':'分析判断','unknown':'待核实'}
    sections=''.join('<section><h2>'+headings[name]+'</h2>'+''.join('<p><b>'+kinds[c['kind']]+'</b> '+e(c['text'])+(' ['+e(', '.join(c['source_ids']))+']' if c['source_ids'] else '')+'</p>' for c in claims)+'</section>' for name,claims in result['sections'].items())
    rows=''.join('<tr>'+''.join('<td>'+e(str(v) if v is not None else 'N/A / NM')+'</td>' for v in [c['entity_id'],c['name'],c['derived']['enterprise_value'],c['derived']['ev_revenue'],c['derived']['ev_ebitda'],c['derived']['pe'],c['derived']['ebitda_margin_percent'],c['state']])+'</tr>' for c in result['companies'])
    # Direct SVG bars use actual comparable revenue only; missing peers remain in the table.
    bars=[(c['name'],Decimal(c['normalized_millions']['revenue'])) for c in result['companies'] if c['normalized_millions']['revenue'] is not None]
    maxval=max((v for _,v in bars),default=Decimal(0))
    svg='<svg xmlns="http://www.w3.org/2000/svg" role="img" aria-label="已核对收入，百万计" viewBox="0 0 800 '+str(max(60,len(bars)*40))+'">'
    for i,(name,n) in enumerate(bars):
        width=n/maxval*450 if maxval else 0
        svg+=f'<text x="0" y="{i*40+25}" font-size="14">{e(name[:16])}</text><rect x="190" y="{i*40+8}" width="{width}" height="24" fill="#567a48"/><text x="660" y="{i*40+25}" font-size="14">{n}</text>'
    svg+='</svg>'
    scope = result['scope']
    metadata = '<p>研究截止：'+e(scope['valuation_date'])+' · 财务期间：'+e(scope['period_start'])+' 至 '+e(scope['period_end'])+' · '+e(scope['basis'])+' · '+e(scope['currency'])+'</p><p>EBITDA口径：'+e(scope['ebitda_definition'])+'</p>'
    source_table = '<table><tr><th>来源</th><th>材料/位置</th><th>发布 / 获取</th></tr>'+''.join('<tr><td>'+e(k)+'</td><td>'+e(v['title'])+'<br>'+e(v['locator'])+'</td><td>'+e(v['published_on'])+' / '+e(v['retrieved_on'])+'</td></tr>' for k,v in result['sources'].items())+'</table>'
    return '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>'+e(result['title'])+'</title><style>body{font:15px/1.7 system-ui;max-width:1100px;margin:40px auto;padding:0 24px;color:#252a2c}section{padding:16px 0;border-top:1px solid #e4e7e9}table{border-collapse:collapse;width:100%;font-size:13px}td,th{padding:10px;border-bottom:1px solid #ddd;text-align:left}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f6f7f8;padding:20px}svg{width:100%}h1{font-size:28px}</style><h1>'+e(result['title'])+'</h1><p>研究草稿 · 数据口径和缺项见附录 · 非发布稿</p>'+metadata+sections+'<h2>同业比较 · 金额百万，倍数x，利润率%</h2><table><tr>'+''.join('<th>'+v+'</th>' for v in ['代码','公司','EV','EV/收入','EV/EBITDA','P/E','EBITDA率','状态'])+'</tr>'+rows+'</table><h2>收入对比</h2>'+svg+'<h2>资料来源</h2>'+source_table+'<details><summary>展开完整证据、缺项与统计记录</summary><pre>'+e(json.dumps(result,ensure_ascii=False,indent=2))+'</pre></details></html>'


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['prepare','observe','build']);p.add_argument('--input',required=True);p.add_argument('--output-dir',required=True)
    args=p.parse_args();source=Path(args.input)
    if source.stat().st_size>2*1024*1024:raise ValueError('input exceeds 2 MiB')
    raw=source.read_bytes();value=json.loads(raw.decode('utf-8-sig'))
    result=analyze(value) if args.action=='build' else globals()[args.action](value)
    result.update(schema_version=1,input_sha256=hashlib.sha256(raw).hexdigest(),authority='Local artifact only; Native tool history and approval remain authoritative')
    encoded=json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n'
    rendered=report(result) if args.action=='build' else None
    requested=Path(args.output_dir);target=requested.parent.resolve(strict=True)/requested.name
    if target==Path.cwd().resolve() or not target.is_relative_to(Path.cwd().resolve()):raise ValueError('new task workspace subdirectory required')
    target.mkdir();(target/'input.json').write_bytes(raw);(target/'inspection.json').write_text(encoded,encoding='utf-8')
    if rendered is not None:
        (target/'report.html').write_text(rendered,encoding='utf-8');workbook(target/'comps.xlsx',result)
    print(json.dumps({'directory':str(target),'state':result['state'],'external_calls':0}))


if __name__=='__main__':
    try:main()
    except (ValueError,OSError,InvalidOperation) as error:raise SystemExit('research not completed: '+str(error)) from None
