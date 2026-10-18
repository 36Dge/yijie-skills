"""YiJie local research IO; standard library, no network or credential access."""
import csv
import hashlib
import json
import re
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path


def number(value, label, minimum=None, maximum=None, optional=False):
    if value is None and optional:
        return None
    if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):
        raise ValueError(label + ': explicit finite number required')
    try:
        result = Decimal(str(value))
    except InvalidOperation as error:
        raise ValueError(label + ': invalid number') from error
    if not result.is_finite() or abs(result) > Decimal('1e20'):
        raise ValueError(label + ': unsupported number')
    if minimum is not None and result < minimum or maximum is not None and result > maximum:
        raise ValueError(label + ': outside supported range')
    return result


def text(value, label):
    if not isinstance(value, str) or not value.strip() or len(value) > 4000:
        raise ValueError(label + ': non-empty text required (max 4000)')
    if any(ord(c) < 32 and c not in '\t\n\r' for c in value):
        raise ValueError(label + ': unsupported control character')
    return value


def day(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        raise ValueError('Date must be YYYY-MM-DD')
    return date.fromisoformat(value)


def read_json(path):
    path = Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 2_000_000:
        raise ValueError('Input must be an ordinary JSON file, at most 2 MB')
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate JSON key: ' + key)
            result[key] = value
        return result
    return json.loads(path.read_text(), parse_float=Decimal, object_pairs_hook=unique,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError('Nonfinite JSON')))


def dumps(value):
    return json.dumps(value, ensure_ascii=False, indent=2,
                      default=lambda v: str(v) if isinstance(v, Decimal) else (_ for _ in ()).throw(TypeError(type(v).__name__))) + '\n'


def sources(data):
    result = data['sources']
    if not isinstance(result, list) or not 1 <= len(result) <= 100:
        raise ValueError('1–100 sources required')
    ids = set()
    for source in result:
        sid = text(source['id'], 'source id')
        if sid in ids:
            raise ValueError('Duplicate source id')
        ids.add(sid)
        text(source['locator'], 'source locator')
        text(source['description'], 'source description')
        day(source['as_of'])
        if source['kind'] not in ('synthetic', 'user-file', 'qualified-connector'):
            raise ValueError('Unsupported source kind')
    return ids


def cite(value, ids):
    if value not in ids:
        raise ValueError('Unknown source_id: ' + str(value))


def output_folder(path):
    path = Path(path).absolute()
    here = Path(__file__).resolve().parent
    package = here.parent if here.name == 'scripts' else here
    if path.is_symlink() or package == path.resolve() or package in path.resolve().parents:
        raise ValueError('Outputs must be outside managed expert resources')
    path.mkdir(parents=False, exist_ok=False)
    return path


def save_json(path, value):
    with Path(path).open('x') as stream:
        stream.write(dumps(value))


def save_csv(path, rows, fields):
    with Path(path).open('x', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def receipt(out):
    files = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.iterdir()) if p.is_file()}
    save_json(out / 'receipt.json', {'schema_version': 1, 'files': files, 'network_calls': 0})


def report(out, title, sections, curve=None):
    """Local tables and keyboard-operable section/row filters; no remote assets."""
    from html import escape
    here = Path(__file__).resolve().parent
    css_path = here.parent / 'templates/yijie-tokens.css' if here.name == 'scripts' else here / 'report.css'
    css = css_path.read_text()
    extra_css = '\nbody{max-width:1160px;margin:40px auto;padding:0 24px;font:14px/1.65 system-ui;color:#25282b}h1{font-size:26px}nav{display:flex;gap:8px;flex-wrap:wrap;margin:24px 0}button,input{font:inherit;padding:9px 14px;border:1px solid #dfe2e5;border-radius:8px;background:white}button[aria-pressed="true"]{background:#25282b;color:white}button:focus-visible,input:focus-visible{outline:3px solid #94c53c}table{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums}th,td{text-align:left;vertical-align:top;padding:10px;border-bottom:1px solid #e7e9eb;white-space:pre-wrap}th{background:#f5f6f7;font-weight:600}.scroll{overflow:auto}section[hidden]{display:none}canvas{width:100%;height:220px}footer{color:#6b7077;margin-top:30px}input{width:280px;max-width:90%}'
    if here.name == 'scripts':
        css += extra_css
    (out/'report.css').write_text(css)
    payload = {'title': title, 'sections': sections, 'curve': curve or []}
    (out/'data.js').write_text('window.researchData = ' + json.dumps(payload, ensure_ascii=True, default=str) + ';\n')
    script = r"""'use strict';
const data=window.researchData;const nav=document.querySelector('nav');const main=document.querySelector('main');
for(const [i,section] of data.sections.entries()){
 const b=document.createElement('button');b.type='button';b.textContent=section.title;b.setAttribute('aria-pressed',String(i===0));nav.append(b);
 const panel=document.createElement('section');panel.hidden=i!==0;const h=document.createElement('h2');h.textContent=section.title;panel.append(h);
 const p=document.createElement('p');p.textContent=section.note||'';panel.append(p);
 const input=document.createElement('input');input.type='search';input.placeholder='筛选当前表格';input.setAttribute('aria-label',section.title+'筛选');panel.append(input);
 const status=document.createElement('p');status.setAttribute('role','status');panel.append(status);
 const wrap=document.createElement('div');wrap.className='scroll';const table=document.createElement('table');const head=document.createElement('thead');const tr=document.createElement('tr');
 for(const col of section.columns){const th=document.createElement('th');th.scope='col';th.textContent=col;tr.append(th);}head.append(tr);table.append(head);
 const body=document.createElement('tbody');table.append(body);wrap.append(table);panel.append(wrap);main.append(panel);
 const render=()=>{body.replaceChildren();let n=0;for(const row of section.rows){if(!row.join(' ').toLowerCase().includes(input.value.toLowerCase()))continue;n++;const r=document.createElement('tr');for(const v of row){const c=document.createElement('td');c.textContent=v===null?'N/A':(/^-?\d+(\.\d+)?$/.test(String(v))?Number(v).toLocaleString('zh-CN',{maximumFractionDigits:6}):String(v));r.append(c);}body.append(r);}status.textContent=n+' / '+section.rows.length+' 行';};input.addEventListener('input',render);render();
 b.addEventListener('click',()=>{[...main.children].forEach((e,j)=>e.hidden=j!==i);[...nav.children].forEach((e,j)=>e.setAttribute('aria-pressed',String(j===i)));});
}
const canvas=document.querySelector('canvas');if(data.curve.length){const ctx=canvas.getContext('2d');const values=data.curve.map(p=>Number(p.value));let low=Math.min(...values),high=Math.max(...values);if(low===high){low-=1;high+=1;}ctx.strokeStyle='#516f32';ctx.lineWidth=3;ctx.beginPath();values.forEach((v,i)=>{const x=30+i*940/Math.max(1,values.length-1),y=180-(v-low)*150/(high-low);i?ctx.lineTo(x,y):ctx.moveTo(x,y);});ctx.stroke();ctx.fillStyle='#555';ctx.font='14px system-ui';ctx.fillText(high.toFixed(2),8,18);ctx.fillText(low.toFixed(2),8,205);}else canvas.hidden=true;
"""
    (out/'report.js').write_text(script)
    (out/'index.html').write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+escape(title)+'</title><link rel="stylesheet" href="report.css"><body><header><p>易界 · 本地研究</p><h1>'+escape(title)+'</h1><p>基于明确输入的研究计算。样例数据不是市场实绩，历史回测不代表未来收益。</p></header><canvas width="1000" height="220" aria-label="权益曲线；精确值见权益表" role="img"></canvas><nav aria-label="报告章节"></nav><main></main><footer>保留 input.json、代码与 receipt.json 可复算。来源真实性、预测合理性及线上时效需另核验。</footer><script src="data.js"></script><script src="report.js"></script></body></html>')


def fields(value, required, optional=()):
    if not isinstance(value, dict) or not set(required) <= value.keys() or value.keys() - set(required) - set(optional):
        raise ValueError('Input fields differ from the supported schema: ' + ', '.join(required))
