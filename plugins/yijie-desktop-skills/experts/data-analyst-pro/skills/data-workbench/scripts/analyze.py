"""Explicit, reproducible local EDA. Python >=3.10 standard library; no network."""
import argparse
import csv
import hashlib
import html
import json
import re
import shutil
import sys
from collections import Counter, defaultdict
from datetime import date, datetime
from decimal import Decimal, InvalidOperation, localcontext
from pathlib import Path

from tableio import MAX_BYTES, MAX_COLS, MAX_ROWS, cell, read_table

VERSION = '0.1.0'
ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(value):
    return json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n'


def decimal(value):
    if isinstance(value, bool) or not re.fullmatch(r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?', str(value)):
        raise ValueError('Expected a plain finite decimal; percent/currency/group separators need explicit preprocessing')
    n = Decimal(str(value))
    if not n.is_finite() or abs(n) > Decimal('1e100') or (n and n.adjusted() < -100):
        raise ValueError('Number outside supported finite range')
    return n


def number(value):
    if value is None:
        return None
    return format(value, '.28g')


def quantile(values, p):
    if not values:
        return None
    a = sorted(values)
    position = Decimal(len(a) - 1) * p
    i = int(position)
    return a[i] + (a[min(i + 1, len(a) - 1)] - a[i]) * (position - i)


def statistics(values, total):
    n = len(values)
    mean = sum(values) / n if n else None
    variance = sum((v - mean) ** 2 for v in values) / (n - 1) if n > 1 else None
    return {'rows': total, 'valid': n, 'unavailable': total - n,
            'coverage': number(Decimal(n) / total) if total else None,
            'known_sum': number(sum(values)) if n else None,
            'mean': number(mean), 'min': number(min(values)) if n else None,
            'q1_type7': number(quantile(values, Decimal('.25'))),
            'median': number(quantile(values, Decimal('.5'))),
            'q3_type7': number(quantile(values, Decimal('.75'))),
            'max': number(max(values)) if n else None,
            'sample_variance': number(variance),
            'sample_stddev': number(variance.sqrt()) if variance is not None else None}


def load_rows(path, config):
    if path.stat().st_size > MAX_BYTES:
        raise ValueError('Source exceeds 16 MiB')
    if path.suffix.lower() != '.json':
        sheet, rows = read_table(path, config.get('sheet'))
        if not rows:
            raise ValueError('Input needs a header row, even for an empty dataset')
        header = [str(c['raw']) for c in rows[0][1]]
        if any(c['kind'] in ('formula', 'unsupported') for c in rows[0][1]):
            raise ValueError('Header must be literal names')
        return sheet, header, rows[1:]
    if config.get('sheet') is not None:
        raise ValueError('JSON cannot specify an XLSX sheet')
    objects = json.loads(path.read_text(encoding='utf-8-sig'), parse_float=str,
                         parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Nonfinite JSON')))
    if not isinstance(objects, list) or len(objects) > MAX_ROWS - 1:
        raise ValueError('JSON must contain at most 49999 row objects')
    header = config.get('json_columns')
    if not isinstance(header, list) or not header or len(header) > MAX_COLS:
        raise ValueError('JSON needs explicit json_columns, including for empty input')
    rows = []
    for i, obj in enumerate(objects, 1):
        if not isinstance(obj, dict) or set(obj) - set(header):
            raise ValueError('JSON rows must be objects with declared columns')
        values = []
        for name in header:
            v = obj.get(name)
            values.append(cell(v, 'unsupported' if isinstance(v, (dict, list, bool)) else 'text'))
        rows.append((i, values))
    return 'JSON objects (1-based)', header, rows


def validate(config):
    if config.get('schema_version') != 1:
        raise ValueError('schema_version must be 1')
    for field in ['title', 'source', 'source_label', 'question']:
        if not isinstance(config.get(field), str) or not config[field].strip():
            raise ValueError('Missing input field: ' + field)
    columns = config.get('columns')
    if not isinstance(columns, list) or not 1 <= len(columns) <= MAX_COLS:
        raise ValueError('Provide a nonempty data dictionary (max 200 columns)')
    names = []
    for c in columns:
        if not isinstance(c, dict) or not isinstance(c.get('name'), str) or not c['name']:
            raise ValueError('Dictionary names must be nonempty')
        if c.get('type') not in ['identifier', 'category', 'number', 'date']:
            raise ValueError('Unsupported dictionary type')
        if not isinstance(c.get('unit'), str) or not c['unit']:
            raise ValueError('Declare unit or explicit not-applicable for each column')
        if c['type'] == 'date' and c.get('format') != '%Y-%m-%d':
            raise ValueError('Date columns require format %Y-%m-%d')
        if not isinstance(c.get('missing'), list) or any(v is not None and not isinstance(v, str) for v in c['missing']):
            raise ValueError('Explicit missing token list (strings/null) required')
        names.append(c['name'])
    if 'source_row' in names:
        raise ValueError('source_row is reserved for the output row provenance; rename explicitly in a preserved input copy')
    if len(set(names)) != len(names):
        raise ValueError('Dictionary has duplicate names')
    if config.get('duplicate_policy') not in ['keep_all', 'deduplicate_exact']:
        raise ValueError('Explicit duplicate_policy required')
    metrics = [c['name'] for c in columns if c['type'] == 'number']
    if not metrics:
        raise ValueError('At least one numeric metric required')
    group = config.get('group_by')
    if group is not None and group not in [c['name'] for c in columns if c['type'] in ['category', 'identifier']]:
        raise ValueError('group_by must reference a category/identifier')
    expected = config.get('expected_groups', [])
    if not isinstance(expected, list) or any(not isinstance(x, str) for x in expected) or len(set(expected)) != len(expected):
        raise ValueError('expected_groups must be unique strings')
    if expected and group is None:
        raise ValueError('expected_groups requires group_by')
    trend = config.get('trend')
    if trend is not None:
        if trend.get('column') not in [c['name'] for c in columns if c['type'] == 'date']:
            raise ValueError('Trend needs a declared date column')
        start, end = date.fromisoformat(trend['start']), date.fromisoformat(trend['end'])
        if end < start or (end - start).days > 3660:
            raise ValueError('Trend window must be ordered and at most 3660 days')
    for field, edges in config.get('histograms', {}).items():
        if field not in metrics or not isinstance(edges, list) or not 2 <= len(edges) <= 101:
            raise ValueError('Histogram needs a numeric field and 2..101 explicit edges')
        values = [decimal(v) for v in edges]
        if any(a >= b for a, b in zip(values, values[1:])):
            raise ValueError('Histogram edges must strictly increase')


def analyze(config, path):
    validate(config)
    source_sha = digest(path)
    sheet, header, raw_rows = load_rows(path, config)
    if digest(path) != source_sha:
        raise ValueError('Source changed while reading')
    if len(header) != len(set(header)) or any(not isinstance(n, str) or not n for n in header):
        raise ValueError('Header names must be unique and nonempty')
    columns = config['columns']
    if any(c['name'] not in header for c in columns):
        raise ValueError('Dictionary column absent from source')
    indices = {c['name']: header.index(c['name']) for c in columns}
    parsed, ledger, seen = [], [], {}
    for row_number, raw in raw_rows:
        if len(raw) > len(header):
            raise ValueError('Row has more fields than the header: ' + str(row_number))
        raw = raw + [cell()] * (len(header) - len(raw))
        fingerprint = json.dumps(raw, sort_keys=True, ensure_ascii=False)
        duplicate_of = seen.get(fingerprint)
        if duplicate_of is None:
            seen[fingerprint] = row_number
        keep = duplicate_of is None or config['duplicate_policy'] == 'keep_all'
        values, states = {}, {}
        for c in columns:
            item = raw[indices[c['name']]]
            value = item['raw']
            state = 'valid'
            try:
                if item['kind'] in ['formula', 'unsupported']:
                    raise ValueError('Unsupported/formula cell')
                if value in c['missing']:
                    value, state = None, 'missing'
                elif value is None:
                    raise ValueError('null is not declared missing')
                elif c['type'] == 'number':
                    if item['kind'] == 'percent':
                        raise ValueError('Percent-formatted XLSX needs explicit value-only conversion')
                    value = decimal(value)
                elif c['type'] == 'date':
                    if item['kind'] == 'date':
                        dt = datetime.fromisoformat(str(value))
                        if dt.time().isoformat() != '00:00:00':
                            raise ValueError('Non-midnight time cannot be truncated')
                        value = dt.date().isoformat()
                    else:
                        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', str(value)):
                            raise ValueError('Date requires exact ISO calendar day')
                        value = date.fromisoformat(str(value)).isoformat()
                else:
                    value = str(value)
            except (ValueError, InvalidOperation, TypeError):
                value, state = None, 'invalid'
            values[c['name']], states[c['name']] = value, state
        ledger.append({'source_row': row_number, 'retained': keep, 'duplicate_of': duplicate_of,
                       'cells': {c['name']: {'raw': raw[indices[c['name']]], 'state': states[c['name']]} for c in columns}})
        if keep:
            parsed.append({'source_row': row_number, 'values': values, 'states': states})
    metrics = [c['name'] for c in columns if c['type'] == 'number']

    def summarize(rows):
        return {m: statistics([r['values'][m] for r in rows if r['states'][m] == 'valid'], len(rows)) for m in metrics}

    quality = {c['name']: dict(Counter(r['states'][c['name']] for r in parsed)) for c in columns}
    identifiers = {}
    for c in columns:
        if c['type'] == 'identifier':
            by_id = defaultdict(list)
            for row in parsed:
                if row['states'][c['name']] == 'valid':
                    by_id[row['values'][c['name']]].append(row['source_row'])
            identifiers[c['name']] = {'unique': len(by_id), 'repeated': {k: v for k, v in by_id.items() if len(v) > 1}}
    groups = []
    if config.get('group_by'):
        key = config['group_by']
        buckets = {name: [] for name in config.get('expected_groups', [])}
        for row in parsed:
            buckets.setdefault(row['values'][key], []).append(row)
        for name, rows in buckets.items():
            groups.append({'group': name, 'rows': len(rows), 'metrics': summarize(rows)})
    trend = None
    if config.get('trend'):
        spec = config['trend']
        buckets, excluded = defaultdict(list), []
        for row in parsed:
            v = row['values'][spec['column']]
            if v is None or not spec['start'] <= v <= spec['end']:
                excluded.append(row['source_row'])
            else:
                buckets[v].append(row)
        trend = {'window': spec, 'excluded_rows': excluded,
                 'days': [{'day': day, 'metrics': summarize(rows)} for day, rows in sorted(buckets.items())],
                 'absent_days': 'No observation; never imputed as zero'}
    histograms = {}
    for field, edges in config.get('histograms', {}).items():
        bounds = [decimal(x) for x in edges]
        counts, outside = [0] * (len(bounds) - 1), 0
        for row in parsed:
            v = row['values'][field]
            if v is None:
                continue
            matched = False
            for i in range(len(counts)):
                if bounds[i] <= v < bounds[i + 1] or (i == len(counts) - 1 and v == bounds[-1]):
                    counts[i] += 1
                    matched = True
                    break
            outside += not matched
        histograms[field] = {'edges': [number(v) for v in bounds], 'counts': counts, 'outside': outside,
                             'closure': '[left,right), final bin includes right',
                             'unavailable': sum(r['values'][field] is None for r in parsed)}
    result = {'schema_version': 1, 'expert_version': VERSION, 'title': config['title'],
              'question': config['question'], 'source': {'filename': path.name, 'sha256': source_sha, 'label': config['source_label'], 'sheet': sheet},
              'dictionary': columns, 'unused_columns': [n for n in header if n not in indices],
              'cleaning': {'before': len(raw_rows), 'after': len(parsed), 'duplicate_policy': config['duplicate_policy'],
                           'exact_repeats': sum(r['duplicate_of'] is not None for r in ledger),
                           'removed': sum(not r['retained'] for r in ledger), 'cell_quality': quality, 'identifiers': identifiers},
              'metrics': summarize(parsed), 'groups': groups, 'trend': trend, 'histograms': histograms,
              'interpretation': ['Known sums cover valid cells only; unavailable is not zero.',
                                 'Sample variance uses n-1; quartiles use linear interpolation (type 7).',
                                 'Descriptive observations are not causal or significance claims.']}
    cleaned = [{'source_row': r['source_row'], **{k: number(v) if isinstance(v, Decimal) else v for k, v in r['values'].items()}} for r in parsed]
    return result, ledger, cleaned


def report(result):
    esc = lambda value: html.escape(str(value), quote=True)
    data = dump(result).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    table = '<table><caption>描述统计 · 已知数值口径</caption><thead><tr>' + ''.join('<th>'+s+'</th>' for s in ['字段', '单位', '有效 / 总行', '缺失或无效', '已知合计', '均值', '中位数', 'Q1 / Q3', '样本标准差']) + '</tr></thead><tbody>'
    units = {c['name']: c['unit'] for c in result['dictionary']}
    for key, m in result['metrics'].items():
        display = lambda k: '不可计算' if m[k] is None else m[k]
        cells = [key, units[key], f"{m['valid']} / {m['rows']}", m['unavailable'], display('known_sum'), display('mean'), display('median'), f"{display('q1_type7')} / {display('q3_type7')}", display('sample_stddev')]
        table += '<tr>'+''.join('<td>'+esc(v)+'</td>' for v in cells)+'</tr>'
    table += '</tbody></table>'
    return '''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>''' + esc(result['title']) + '''</title><link rel="stylesheet" href="yijie-tokens.css"><style>
*{box-sizing:border-box}body{margin:0;background:var(--yj-color-bg-page);color:var(--yj-color-text-primary);font:var(--yj-font-size-body)/var(--yj-line-height-body) var(--yj-font-family-sans)}main{max-width:1200px;margin:auto;padding:var(--yj-space-8)}header{display:flex;gap:var(--yj-space-4);justify-content:space-between;align-items:start}h1{font-size:var(--yj-font-size-page-title);line-height:var(--yj-line-height-page-title);margin:0}h2{font-size:var(--yj-font-size-section-title)}p{color:var(--yj-color-text-secondary)}section{padding-block:var(--yj-space-6);border-top:var(--yj-border-width) solid var(--yj-color-border-default)}button,select{font:inherit;color:inherit;background:var(--yj-color-bg-card);border:var(--yj-border-width) solid var(--yj-color-border-control);padding:var(--yj-space-2) var(--yj-space-3);border-radius:var(--yj-radius-md)}:focus-visible{outline:var(--yj-focus-ring-width) solid var(--yj-color-focus-ring);outline-offset:var(--yj-space-1)}.scroll{overflow:auto}table{width:100%;border-collapse:collapse;text-align:left}th,td{padding:var(--yj-space-3);border-bottom:var(--yj-border-width) solid var(--yj-color-border-subtle);white-space:nowrap}caption{text-align:left;color:var(--yj-color-text-secondary);padding-block:var(--yj-space-3)}pre{white-space:pre-wrap;overflow-wrap:anywhere}#chart{height:340px}a{color:var(--yj-color-chart-series-2)}@media(max-width:600px){main{padding:var(--yj-space-4)}header{flex-wrap:wrap}}
</style><main><header><div><p>易界 · 数据分析</p><h1>''' + esc(result['title']) + '''</h1></div><button id="theme" type="button">切换暗色</button></header><p>''' + esc(result['question']) + '''</p><p>来源：''' + esc(result['source']['label']) + ' · SHA256 ' + esc(result['source']['sha256']) + '''</p><section><h2>清洗与口径</h2><p>输入 ''' + str(result['cleaning']['before']) + ' 行，保留 ' + str(result['cleaning']['after']) + ' 行；移除完全重复 ' + str(result['cleaning']['removed']) + ''' 行。缺值与无效值不补零；合计仅覆盖已知数值。重复标识不自动删除。</p><details><summary>数据字典与质量记录</summary><pre>''' + esc(dump({'dictionary': result['dictionary'], 'cleaning': result['cleaning']})) + '''</pre></details></section><section><div class="scroll">''' + table + '''</div></section><section><h2>分组 / 趋势 / 分布</h2><label>图表 <select id="view"></select></label><div id="chart" role="img" aria-label="当前统计图表，下方提供同源数据表"></div><div class="scroll" id="chart-table"></div><p id="chart-note"></p></section><section><h2>复算与证据</h2><p>没有观测的日期不补零。样本方差使用 n−1；四分位数使用线性插值 Type 7。描述统计不能证明显著性或因果。</p><p><a href="analysis.json">分析 JSON</a> · <a href="row-ledger.json">逐行清洗账</a> · <a href="cleaned.csv">清洗数据</a> · <a href="summary.md">复算说明</a></p></section></main><script src="vendor/echarts.cjs"></script><script type="application/json" id="data">''' + data + '''</script><script>
const d=JSON.parse(document.getElementById('data').textContent), select=document.getElementById('view'), options=[];
const units=Object.fromEntries(d.dictionary.map(c=>[c.name,c.unit]));
for(const m of Object.keys(d.metrics)){
 if(d.groups.length)options.push({name:m+' · 分组已知合计',labels:d.groups.map(g=>g.group===null?'缺失/无效分组':g.group),values:d.groups.map(g=>g.metrics[m].known_sum),coverage:d.groups.map(g=>g.metrics[m].valid+'/'+g.metrics[m].rows),unit:units[m],type:'bar',note:'各组仅合计有效数值，空组不可计算。'});
 if(d.trend)options.push({name:m+' · 日期已知合计',labels:d.trend.days.map(g=>g.day),values:d.trend.days.map(g=>g.metrics[m].known_sum),coverage:d.trend.days.map(g=>g.metrics[m].valid+'/'+g.metrics[m].rows),unit:units[m],type:'bar',note:'仅列有观测日期；窗口外或日期无效排除 '+d.trend.excluded_rows.length+' 行。'});
 if(d.histograms[m]){const h=d.histograms[m];options.push({name:m+' · 分布',labels:h.counts.map((_,i)=>'['+h.edges[i]+','+h.edges[i+1]+(i===h.counts.length-1?']':')')),values:h.counts,coverage:h.counts.map(()=> '—'),unit:'行',type:'bar',note:'范围外 '+h.outside+' 行；缺失或无效 '+h.unavailable+' 行。'});}
}
options.forEach((o,i)=>{const node=document.createElement('option');node.value=i;node.textContent=o.name;select.append(node);});
const chart=echarts.init(document.getElementById('chart'));
function render(){const o=options[Number(select.value)];if(!o){document.getElementById('chart-note').textContent='未配置图表维度。';return;}
 const css=getComputedStyle(document.documentElement), table=document.createElement('table'), caption=table.createCaption();caption.textContent=o.name+' · 同源数据';
 const head=table.createTHead().insertRow();['维度',o.unit,'有效 / 总行'].forEach(t=>{const th=document.createElement('th');th.textContent=t;head.append(th);});const body=table.createTBody();o.labels.forEach((name,i)=>{const row=body.insertRow();[name,o.values[i]===null?'不可计算':o.values[i],o.coverage[i]].forEach(v=>{row.insertCell().textContent=v;});});document.getElementById('chart-table').replaceChildren(table);document.getElementById('chart-note').textContent=o.note;
 chart.setOption({backgroundColor:'transparent',color:[css.getPropertyValue('--yj-color-chart-series-1').trim()],textStyle:{fontFamily:css.getPropertyValue('--yj-font-family-sans'),color:css.getPropertyValue('--yj-color-text-primary').trim()},tooltip:{trigger:'axis'},grid:{left:70,right:30,bottom:60,top:35},xAxis:{type:'category',data:o.labels},yAxis:{type:'value',name:o.unit},series:[{type:o.type,data:o.values.map(v=>v===null?null:Number(v)),connectNulls:false}],animation:false},true);
}select.addEventListener('change',render);document.getElementById('theme').addEventListener('click',()=>{const dark=document.documentElement.dataset.theme!=='dark';document.documentElement.dataset.theme=dark?'dark':'light';document.getElementById('theme').textContent=dark?'切换亮色':'切换暗色';render();});window.addEventListener('resize',()=>chart.resize());render();
</script></html>'''


def run(manifest, output):
    if sys.version_info < (3, 10):
        raise ValueError('Python >=3.10 required')
    config = json.loads(manifest.read_text(encoding='utf-8'))
    path = (manifest.parent / config['source']).resolve()
    with localcontext() as context:
        context.prec = 50
        result, ledger, cleaned = analyze(config, path)
    # Compute before writing. Never overwrite a prior delivery or source.
    output.mkdir(parents=True, exist_ok=False)
    (output / 'analysis.json').write_text(dump(result), encoding='utf-8')
    (output / 'row-ledger.json').write_text(dump(ledger), encoding='utf-8')
    with (output / 'cleaned.csv').open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['source_row'] + [c['name'] for c in config['columns']])
        writer.writeheader()
        writer.writerows(cleaned)
    document = report(result)
    document, script = document.rsplit('<script>', 1)
    script = script.removesuffix('</script></html>')
    (output / 'report.js').write_text(script, encoding='utf-8')
    (output / 'report.html').write_text(document + '<script src="report.js"></script></html>', encoding='utf-8')
    shutil.copyfile(ROOT / 'templates/yijie-tokens.css', output / 'yijie-tokens.css')
    shutil.copytree(ROOT / 'vendor', output / 'vendor')
    replay = output / 'reproduce'
    (replay / 'scripts').mkdir(parents=True)
    (replay / 'templates').mkdir()
    for filename in ['analyze.py', 'tableio.py']:
        shutil.copyfile(ROOT / 'scripts' / filename, replay / 'scripts' / filename)
    shutil.copyfile(ROOT / 'templates/yijie-tokens.css', replay / 'templates/yijie-tokens.css')
    shutil.copytree(ROOT / 'vendor', replay / 'vendor')
    snapshot = replay / ('source' + path.suffix.lower())
    shutil.copyfile(path, snapshot)
    # A source changing during execution is not a reproducible success.
    if digest(snapshot) != result['source']['sha256'] or digest(path) != result['source']['sha256']:
        raise ValueError('Source changed during analysis; partial output must not be delivered as passed')
    copied = {**config, 'source': snapshot.name}
    (replay / 'input.json').write_text(dump(copied), encoding='utf-8')
    (output / 'input.json').write_text(dump(config), encoding='utf-8')
    (output / 'summary.md').write_text('# ' + config['title'] + '\n\n来源：' + config['source_label'] + '\n\n' +
        '清洗前 '+str(result['cleaning']['before'])+' 行；清洗后 '+str(result['cleaning']['after'])+' 行。\n\n' +
        'analysis.json 保存有效样本数、缺值、已知合计、均值、Type7分位数及n−1样本方差。row-ledger.json保留每行处理原因和原值。重复ID仅提示，不自行删行；无观测日期不补零；没有推断统计或因果结论。\n\n' +
        '复算（使用已安装 Python3.10+；输出必须是新目录）：\n\n```sh\npython3 reproduce/scripts/analyze.py --input reproduce/input.json --output replay-output\n```\n\n' +
        '复算后的 source.filename 因快照名不同而变化；其余分析值和 source.sha256 应一致。浏览器打开与交互需单独验证，本脚本没有验证浏览器。\n', encoding='utf-8')
    files = {str(p.relative_to(output)): digest(p) for p in sorted(output.rglob('*')) if p.is_file()}
    (output / 'receipt.json').write_text(dump({'schema_version': 1, 'expert_version': VERSION,
        'python': sys.version.split()[0], 'dependencies': 'Python standard library; bundled Apache ECharts',
        'source_sha256': result['source']['sha256'], 'browser_validation': 'NOT RUN', 'files': files}), encoding='utf-8')
    print(dump({'output': str(output.resolve()), 'rows': result['cleaning']}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        run(args.input.resolve(), args.output.resolve())
    except (ValueError, OSError, KeyError, InvalidOperation) as error:
        parser.exit(2, 'Analysis incomplete: ' + str(error) + '\n')
