import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync, writeFileSync, existsSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../plugins/yijie-desktop-skills/experts/market-researcher/skills/industry-research');
const sample=JSON.parse(readFileSync(path.join(root,'examples/research.json')));
const copy=()=>structuredClone(sample);
function run(action,input,accept=true){
 const cwd=mkdtempSync(path.join(tmpdir(),'yijie-research-normal-'));
 try{
  const raw=JSON.stringify(input,null,2)+'\n';writeFileSync(path.join(cwd,'request.json'),raw);
  const args=[path.join(root,'scripts/research.py'),action,'--input','request.json','--output-dir','result'];
  const result=spawnSync('python3',args,{cwd,encoding:'utf8'});
  if(!accept){assert.notEqual(result.status,0);assert.equal(existsSync(path.join(cwd,'result')),false);return;}
  assert.equal(result.status,0,result.stderr);assert.equal(JSON.parse(result.stdout).external_calls,0);
  assert.equal(readFileSync(path.join(cwd,'result/input.json'),'utf8'),raw);
  const parsed=JSON.parse(readFileSync(path.join(cwd,'result/inspection.json')));
  if(action==='build'){
   parsed.html=readFileSync(path.join(cwd,'result/report.html'),'utf8');
   const check=spawnSync('python3',['-c',`import json,zipfile,xml.etree.ElementTree as E
with zipfile.ZipFile('result/comps.xlsx') as z:
 for n in z.namelist(): E.fromstring(z.read(n))
 result={n:z.read(n).decode() for n in z.namelist() if 'worksheets/sheet' in n}
 ns='{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
 cells=E.fromstring(z.read('xl/worksheets/sheet3.xml')).iter(ns+'c')
 result['sourceText']=''.join(''.join(c.itertext()) for c in cells if c.get('r','').startswith('I') and c.get('r')!='I1')
 print(json.dumps(result))`],{cwd,encoding:'utf8'});
   assert.equal(check.status,0,check.stderr);parsed.sheets=JSON.parse(check.stdout);
  }
  assert.notEqual(spawnSync('python3',args,{cwd,encoding:'utf8'}).status,0,'previous output must be preserved');
  return parsed;
 }finally{rmSync(cwd,{recursive:true,force:true});}
}
const finance=()=>({kind:'finance',service_id:'eastmoney',purpose:'Query a public financial disclosure; synthetic schema only',tool:{name:'m_'+createHash('sha256').update('eastmoney\nsynthetic_public_query').digest('hex').slice(0,60),title:'eastmoney · synthetic_public_query',inputSchema:{type:'object',properties:{query:{type:'string'}},required:['query'],additionalProperties:false}},arguments:{query:'synthetic company FY2025'}});
const receipt=(plan,body)=>{const p=run('prepare',plan);return{plan,actual_service_id:p.service_id,actual_tool_name:p.tool_name,actual_arguments:p.arguments,source_operation_id:'synthetic-native-operation',retrieved_on:'2026-07-01',mcp_result:{structuredContent:body}};};

test('research search and daily preparation use exact existing methods without submission',()=>{
 const s=run('prepare',{kind:'search',query:'issuer annual filing'});assert.equal(s.arguments.toolName,'aiMode/googleSearch');assert.equal(s.execution_authorized,false);
 const p=run('prepare',{kind:'price',ts_code:'000001.SZ',trade_date:'20260630'});assert.equal(p.tool_name,'tushare_daily');assert.deepEqual(p.arguments,{ts_code:'000001.SZ',trade_date:'20260630'});
 for(const value of [{kind:'price',ts_code:'00700.HK',trade_date:'20260630'},{kind:'price',ts_code:'000001.SZ',trade_date:'20260230'},{kind:'search',query:''}])run('prepare',value,false);
});
test('research financial planning preserves actual Native tool identity and keeps schema authority in Native',()=>{
 const q=finance();const r=run('prepare',q);assert.equal(r.tool_name,q.tool.name);assert.deepEqual(r.arguments,q.arguments);assert.equal(r.schema_validation,'Native_required');
 run('prepare',{...q,service_id:'neodata'},false);run('prepare',{...q,tool:{...q.tool,name:'invented'}},false);
 run('prepare',{...q,tool:{...q.tool,title:'wind · synthetic_public_query'}},false);
});
test('research search replies remain discovery, not verified financial facts',()=>{
 const r=run('observe',receipt({kind:'search',query:'issuer filing'},{code:'200',stdout:'Issuer report may be available.',sourceUrl:'https://example.com/filing'}));
 assert.equal(r.state,'discovery_only');assert.equal(r.verified_financial_facts,false);
});
test('research Tushare validates exact date/security and never converts close into valuation',()=>{
 const q={kind:'price',ts_code:'000001.SZ',trade_date:'20260630'};
 const good={rows:[{ts_code:'000001.SZ',trade_date:'20260630',close:10}]};
 const r=run('observe',receipt(q,good));assert.equal(r.state,'unadjusted_price_only');assert.equal(r.market_cap,undefined);
 for(const row of [{...good.rows[0],trade_date:'20260629'},{...good.rows[0],ts_code:'000002.SZ'},{...good.rows[0],close:undefined}])run('observe',receipt(q,{rows:[row]}),false);
});
test('research refuses wrong service/tool/arguments and normal MCP failures',()=>{
 const r=receipt(finance(),{code:0,rows:[{value:100}]});
 assert.equal(run('observe',r).state,'source_requires_review');
 for(const extra of [{actual_service_id:'wind'},{actual_tool_name:'other'},{actual_arguments:{query:'other'}},{mcp_result:{isError:true}},{mcp_result:{structuredContent:{code:402}}},{mcp_result:{structuredContent:{}}}])run('observe',{...r,...extra},false);
});
test('research computes EV and comparable ratios with real formula cells and all peers retained',()=>{
 const r=run('build',copy());assert.equal(r.companies.length,2);const a=r.companies[0];
 assert.equal(a.derived.enterprise_value,'220');assert.equal(a.derived.ev_ebitda,'11');assert.equal(a.derived.pe,'20');assert.equal(Number(a.derived.ebitda_margin_percent),20);
 assert.match(r.sheets['xl/worksheets/sheet1.xml'],/COUNT\(F2:J2\)=5,F2\+G2-H2\+I2\+J2/);assert.match(r.sheets['xl/worksheets/sheet1.xml'],/ISNUMBER\(D2\).*K2\/D2/);
 assert.match(r.sheets['xl/worksheets/sheet2.xml'],/synthetic-source/);assert.match(r.html,/<svg/);assert.doesNotMatch(r.html,/<script|<iframe|<img/);
});
test('research missing and null inputs never become zero in EV or ratios',()=>{
 for(const key of Object.keys(sample.companies[0].metrics)){
  const v=copy();delete v.companies[0].metrics[key];const r=run('build',v);assert.equal(r.companies.length,2);assert.ok(r.companies[0].issues[key]);assert.equal(r.companies[0].normalized_millions[key],null);
 }
 const v=copy();v.companies[0].metrics.debt=null;assert.equal(run('build',v).companies[0].derived.enterprise_value,null);
});
test('research negative earnings stay negative, valuation NM is excluded from sample statistics',()=>{
 const r=run('build',copy());assert.equal(r.companies[1].derived.ev_ebitda,null);assert.equal(r.companies[1].derived.pe,null);assert.equal(r.companies[1].derived.ebitda_margin_percent,'-2.500');assert.equal(r.statistics.ev_ebitda.count,1);assert.equal(r.statistics.ev_ebitda.median,'11');
});
test('research rejects mixed currency, forecasts, dates and EBITDA definitions per metric',()=>{
 for(const change of [p=>p.currency='USD',p=>p.basis='NTM',p=>p.period_end='2025-09-30',p=>p.definition='adjusted_ebitda',p=>p.scale=null,p=>p.as_of='2025-12-30']){
  const v=copy();change(v.companies[0].metrics.ebitda);const c=run('build',v).companies[0];assert.ok(c.issues.ebitda);assert.equal(c.derived.ev_ebitda,null);
 }
});
test('research cannot silently use a different source security, period or substring number',()=>{
 for(const change of [v=>v.sources[0].entity_ids=['BBB.SYN'],v=>v.sources[0].period_ends=['2024-12-31'],v=>v.companies[0].metrics.revenue.value='10',v=>v.companies[0].metrics.revenue.quote='not in source']){
  const v=copy();change(v);assert.ok(run('build',v).companies[0].issues.revenue);
 }
});
test('research source publication and valuation dates prevent look-ahead',()=>{
 const v=copy();v.sources[0].published_on='2026-07-01';run('build',v,false);
 const w=copy();w.sources[0].published_on='2026-06-29';assert.ok(run('build',w).companies[0].issues.market_cap);
});
test('research four sections and traceable claims are required without invented sources',()=>{
 const v=copy();delete v.sections.watchlist;run('build',v,false);
 const w=copy();w.sections.overview=[{text:'A sourced claim',kind:'fact',source_ids:['missing']}];run('build',w,false);
 const z=copy();z.sections.overview=[{text:'A sourced claim',kind:'fact',source_ids:[]}];run('build',z,false);
});
test('research duplicate security or source is rejected instead of overwritten',()=>{
 const v=copy();v.companies.push(v.companies[0]);run('build',v,false);
 const w=copy();w.sources.push(w.sources[0]);run('build',w,false);
});
test('research actual provider excerpts must match retained tool response; search cannot masquerade as finance',()=>{
 const v=copy();const s=v.sources[0];s.kind='provider';s.receipt=receipt(finance(),s.content);assert.equal(run('build',v).companies[0].state,'inputs_consistent');
 const w=structuredClone(v);w.sources[0].content+=' invented addition';run('build',w,false);
 const z=copy();z.sources[0].kind='provider';z.sources[0].receipt=receipt({kind:'search',query:'research'},{code:'200',stdout:z.sources[0].content});run('build',z,false);
});
test('research normalized inputs preserve sub-million precision and long source text is chunked without loss',()=>{
 const v=copy();const p=v.companies[0].metrics.revenue;p.value='1';p.scale=1;p.quote='Revenue 1 CNY for synthetic company.';v.sources[0].content+='\n'+p.quote+'\n'+'普通来源文本。'.repeat(5000);
 const r=run('build',v);assert.equal(r.companies[0].normalized_millions.revenue,'0.000001');assert.match(r.sheets['xl/worksheets/sheet1.xml'],/<v>0.000001<\/v>/);
 assert.equal(r.sheets.sourceText,v.sources[0].content);
});
test('research explicit zero balances remain valid, ordinary punctuation is escaped, and unknown values stay visible',()=>{
 const v=copy();v.title='合成 & 同业 "比较"';const r=run('build',v);assert.equal(r.companies[0].normalized_millions.preferred,'0');assert.match(r.html,/合成 &amp; 同业 &quot;比较&quot;/);assert.match(r.html,/N\/A \/ NM/);
});
