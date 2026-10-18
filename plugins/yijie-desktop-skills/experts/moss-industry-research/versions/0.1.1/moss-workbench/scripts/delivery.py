"""One frozen evidence version produces every requested format; no model pass flags."""
import hashlib
import json
import os
import re
import shutil
import subprocess
from decimal import Decimal
from html import escape
from pathlib import Path
from common import output_folder, read_json, save_json
from research import calculate, digest


def display(value):
    if value is None:return 'N/A'
    if isinstance(value,(Decimal,int)) or isinstance(value,str) and re.fullmatch(r'-?\d+(?:\.\d+)?',value):
        return format(Decimal(str(value)),'.8f').rstrip('0').rstrip('.') or '0'
    return str(value)


def blocks_for(state,result):
    blocks=[{'title':'研究范围与计划','lines':[
        state['plan']['decision'], '；'.join({'industry':'行业','geography':'地域','boundary':'范围','currency':'币种','year':'统计年','as_of':'研究日'}[k]+'：'+str(v) for k,v in state['scope'].items()),
        '研究模式：'+state['mode']+'。本地程序没有调用 MOSS 或在线搜索。',
        '研究问题：'+'；'.join(state['plan']['questions']),
        '执行步骤：'+'；'.join(state['plan']['steps'])]}]
    findings=[]
    for f in result['findings']:
        findings.extend([f['id']+' ['+f['kind']+'] '+f['text'], '依据：'+', '.join(f['fact_ids'])+'。限制：'+f['limitations'], '下一步：'+f['next_action']])
    blocks.append({'title':'研究判断与行动','lines':findings})
    calculations=[]
    for cid,c in result['calculations'].items():
        calculations.extend([cid+'：'+'；'.join(k+' = '+display(v) for k,v in c['values'].items()),c['formula'],'依据：'+', '.join(c['fact_ids'])+'。'+' '.join(c['notes'])])
        if 'ranks' in c:calculations.append('排序：'+'；'.join(k+' = '+display(v) for k,v in c['ranks'].items()))
    blocks.append({'title':'计算与敏感性','lines':calculations or ['本次未请求数值计算。']})
    facts=[]
    for f in state['facts']:
        facts.extend([f['id']+' ['+f['status']+'] '+display(f['value'])+' '+f['unit']+'；'+str(f['year'])+'；'+f['geography']+'；'+f['boundary'],
                      '来源 '+f['source_id']+' 原文：'+f['quote'],'限制：'+f['limitation']])
    blocks.append({'title':'证据台账','lines':facts})
    source_lines=[]
    for s in state['sources']:
        source_lines.extend([s['id']+' '+s['title']+' ['+s['kind']+']',s['locator']+'；发布 '+s['published_on']+'；取得 '+s['retrieved_on'],'保留原文：'+s['content']])
    blocks.append({'title':'来源档案','lines':source_lines})
    blocks.append({'title':'缺口与适用限制','lines':state['gaps']+[
        '机械校验覆盖引用、口径、计算和文件一致性，不能证明来源真实或推断正确。',
        '模型生成文稿仍须结合保留原文审阅。情景、评分与排序不是事实或收益承诺。']})
    return blocks


def checked_frozen(path):
    frozen=read_json(path)
    if set(frozen)!= {'schema_version','state','result','content_sha256'} or frozen['schema_version']!=1:raise ValueError('Invalid frozen package')
    payload={k:v for k,v in frozen.items() if k!='content_sha256'}
    if digest(payload)!=frozen['content_sha256'] or digest(calculate(frozen['state']))!=digest(frozen['result']):
        raise ValueError('Frozen content or calculation changed; create a new version')
    return frozen


def html(out,title,blocks,identity):
    payload={'title':title,'blocks':blocks,'identity':identity}
    (out/'data.js').write_text('window.researchData='+json.dumps(payload,ensure_ascii=True)+';\n')
    (out/'report.css').write_text('''body{margin:48px auto;max-width:1050px;padding:0 28px;color:#25282b;font:15px/1.8 system-ui;background:#fff}h1{font-size:30px;font-weight:600}h2{font-size:22px;margin-top:40px}header{border-bottom:1px solid #e6e8ea;padding-bottom:24px}nav{display:flex;gap:16px;flex-wrap:wrap;margin:24px 0}a{color:#49662e}input{font:inherit;border:1px solid #b7bcc1;border-radius:8px;padding:10px;width:min(440px,90%)}p{overflow-wrap:anywhere}button:focus-visible,a:focus-visible,input:focus-visible{outline:3px solid #a4cc54}section{scroll-margin-top:20px}small{color:#666}li{padding:5px 0}footer{margin:48px 0;color:#70757a}@media(max-width:600px){body{padding:0 18px;margin:24px auto}h1{font-size:25px}}''')
    (out/'report.js').write_text(''''use strict';const d=window.researchData;document.querySelector('h1').textContent=d.title;document.querySelector('#version').textContent='内容版本 '+d.identity.revision+' · '+d.identity.mode+' · '+d.identity.content_sha256;const nav=document.querySelector('nav'),main=document.querySelector('main');d.blocks.forEach((b,i)=>{const a=document.createElement('a');a.href='#section-'+i;a.textContent=b.title;nav.append(a);const section=document.createElement('section');section.id='section-'+i;const h=document.createElement('h2');h.textContent=b.title;section.append(h);b.lines.forEach(line=>{const p=document.createElement('p');p.textContent=line;section.append(p)});main.append(section)});document.querySelector('input').addEventListener('input',e=>{let n=0;document.querySelectorAll('main p').forEach(p=>{p.hidden=!p.textContent.toLowerCase().includes(e.target.value.toLowerCase());if(!p.hidden)n++});document.querySelector('[role=status]').textContent=n+' 条匹配'});''')
    (out/'index.html').write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+escape(title)+'</title><link rel="stylesheet" href="report.css"><body><header><small>易界 · 行业研究</small><h1></h1><p id="version"></p></header><nav aria-label="报告章节"></nav><label>筛选研究内容 <input type="search" aria-label="筛选研究内容"></label><p role="status">全部内容</p><main></main><footer>来源、假设与缺口随冻结内容一起保留。更改输入须重新冻结并另存文件。</footer><script src="data.js"></script><script src="report.js"></script></body></html>')


def deliver_frozen(frozen_path,output,soffice=None):
    frozen=checked_frozen(frozen_path);state=frozen['state'];result=frozen['result'];formats=state['formats']
    office=None
    if 'pdf' in formats:
        if not soffice or not Path(soffice).is_absolute() or not Path(soffice).is_file() or Path(soffice).name not in ('soffice','soffice.bin'):
            raise ValueError('PDF requires an explicitly selected existing normal LibreOffice soffice executable; no shim or auto-install')
        office=Path(soffice).resolve()
    blocks=blocks_for(state,result);identity={k:state[k] for k in ['revision','mode']};identity['content_sha256']=frozen['content_sha256']
    out=output_folder(output);save_json(out/'research_state.json',state);save_json(out/'frozen.json',frozen);save_json(out/'content.json',blocks)
    formal={};dependencies={'python':'standard-library','office':None}
    if 'html' in formats:html(out,state['title'],blocks,identity);formal['html']='index.html'
    if 'xlsx' in formats:
        from artifacts import write_xlsx
        sheets=[('Identity',[['Field','Value']]+[[k,v] for k,v in identity.items()])]
        from office import wrap
        for i,b in enumerate(blocks,1):
            sheets.append(('Section'+str(i),[['Section','Content']]+[[b['title'],part] for line in b['lines'] for part in wrap(line,180)]))
        sheets.append(('Facts',[['ID','Value','Unit','Year','Geography','Boundary','Status','Source']]+[[f['id'],Decimal(str(f['value'])) if f['value'] is not None else 'N/A',f['unit'],f['year'],f['geography'],f['boundary'],f['status'],f['source_id']] for f in state['facts']]))
        sheets.append(('Metrics',[['Calculation','Metric','Value','Formula','Evidence']]+[[cid,key,Decimal(str(value)) if value is not None else 'N/A',c['formula'],', '.join(c['fact_ids'])] for cid,c in result['calculations'].items() for key,value in c['values'].items()]))
        write_xlsx(out/'research.xlsx',sheets);formal['xlsx']='research.xlsx'
    if 'docx' in formats or 'pdf' in formats:
        from office import docx
        docx(out/'research.docx',state['title'],blocks,identity)
        if 'docx' in formats:formal['docx']='research.docx'
    if 'pptx' in formats:
        from office import pptx
        pages=pptx(out/'research.pptx',state['title'],blocks,identity);formal['pptx']='research.pptx';dependencies['slides']=pages
    if office:
        profile=out/'.office-profile';profile.mkdir()
        # Separate normal user profile, ordinary CLI conversion; no runtime interception,
        # no forced timeout/kill, no user preference or preexisting process changes.
        command=[str(office),'-env:UserInstallation='+profile.as_uri(),'--headless','--convert-to','pdf:writer_pdf_Export','--outdir',str(out),str(out/'research.docx')]
        env=dict(os.environ)
        font=Path('/System/Library/Fonts/STHeiti Medium.ttc')
        if font.is_file():
            config=out/'office-fonts.conf'
            config.write_text('<fontconfig><dir>/System/Library/Fonts</dir><cachedir>'+escape(str(profile/'font-cache'))+'</cachedir></fontconfig>')
            env['FONTCONFIG_FILE']=str(config)
            dependencies['cjk_font']={'path':str(font),'sha256':hashlib.sha256(font.read_bytes()).hexdigest(),'family':'Heiti SC'}
        run=subprocess.run(command,stdin=subprocess.DEVNULL,capture_output=True,text=True,check=False,env=env)
        if run.returncode or not (out/'research.pdf').is_file() or not (out/'research.pdf').read_bytes().startswith(b'%PDF-'):
            save_json(out/'conversion-failure.json',{'exit_code':run.returncode,'stdout':run.stdout,'stderr':run.stderr})
            raise ValueError('Normal Office conversion did not produce PDF; partial files retained, no successful receipt')
        dependencies['office']={'executable':str(office),'sha256':hashlib.sha256(office.read_bytes()).hexdigest(),'exit_code':run.returncode}
        formal['pdf']='research.pdf'
    here=Path(__file__).resolve().parent
    for name in ['research.py','delivery.py','common.py','artifacts.py','office.py']:
        shutil.copy2(here/name,out/name)
    files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.iterdir()) if p.is_file()}
    manifest={'schema_version':1,'content_sha256':frozen['content_sha256'],'formal_files':formal,'files':files,
              'dependencies':dependencies,'network_calls_by_helper':0,'structural_status':'generated-and-hashed',
              'visual_review':'requires actual rendering and inspection','semantic_review':'requires source/result review'}
    save_json(out/'receipt.json',manifest)
    verify_delivery(out,state)
    return {'status':'generated-and-verified','output':str(out),'formats':formal,'content_sha256':frozen['content_sha256'],
            'visual_review':'not inferred from file generation'}


def verify_delivery(out,state):
    frozen=checked_frozen(out/'frozen.json');receipt=read_json(out/'receipt.json')
    if digest(state)!=digest(frozen['state']):raise ValueError('Current research state differs; all format branches stale, refreeze and regenerate')
    if receipt['content_sha256']!=frozen['content_sha256'] or set(receipt['formal_files'])!=set(state['formats']):raise ValueError('Version or requested format mismatch')
    expected_content=blocks_for(state,frozen['result'])
    if digest(read_json(out/'content.json'))!=digest(expected_content):raise ValueError('Content differs from frozen evidence')
    for name,sha in receipt['files'].items():
        if Path(name).name!=name or not (out/name).is_file() or (out/name).is_symlink() or hashlib.sha256((out/name).read_bytes()).hexdigest()!=sha:
            raise ValueError('Delivery file differs from receipt: '+name)
    for name in receipt['formal_files'].values():
        if name not in receipt['files']:raise ValueError('Formal artifact missing from hashed files')
    return {'status':'verified','content_sha256':frozen['content_sha256'],'formats':sorted(receipt['formal_files']),
            'meaning':'Evidence/structure/calculation/file consistency only; not proof of source authenticity or visual quality'}
