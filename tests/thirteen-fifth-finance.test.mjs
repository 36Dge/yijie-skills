import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync, writeFileSync, rmSync, readdirSync, existsSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';

const base=path.resolve('plugins/yijie-desktop-skills/experts');
const root={equity:path.join(base,'equity-research/versions/0.1.2/equity-workbench'),backtest:path.join(base,'strategy-backtest-expert/versions/0.1.1/backtest-workbench')};
const sample=kind=>JSON.parse(readFileSync(path.join(root[kind],'examples/input.json')));
const close=(a,b)=>assert.ok(Math.abs(Number(a)-Number(b))<1e-8,`${a} != ${b}`);
const hash=bytes=>createHash('sha256').update(bytes).digest('hex');
function run(kind,input,verify,ok=true){
 const cwd=mkdtempSync(path.join(tmpdir(),'yijie-finance-normal-'));
 try{
  const bytes=JSON.stringify(input);writeFileSync(path.join(cwd,'input.json'),bytes);
  const args=[path.join(root[kind],`scripts/${kind}.py`),'--input','input.json','--output','result'];
  const p=spawnSync('python3',args,{cwd,encoding:'utf8'});
  if(!ok){assert.equal(p.status,2,p.stdout+p.stderr);assert.equal(existsSync(path.join(cwd,'result')),false);return;}
  assert.equal(p.status,0,p.stdout+p.stderr);assert.equal(p.stderr,'');
  assert.equal(readFileSync(path.join(cwd,'input.json'),'utf8'),bytes);
  const output=path.join(cwd,'result');const receipt=JSON.parse(readFileSync(path.join(output,'receipt.json')));
  assert.equal(receipt.network_calls,0);
  for(const [file,digest] of Object.entries(receipt.files))assert.equal(hash(readFileSync(path.join(output,file))),digest);
  const value=JSON.parse(readFileSync(path.join(output,kind==='equity'?'result.json':'summary.json')));
  verify?.(value,output);
  assert.equal(spawnSync('python3',args,{cwd,encoding:'utf8'}).status,2,'existing output cannot be overwritten');
  const rerun=spawnSync('python3',[`${kind}.py`,'--input','input.json','--output','../reproduced'],{cwd:output,encoding:'utf8'});
  assert.equal(rerun.status,0,rerun.stderr);
  assert.deepEqual(JSON.parse(readFileSync(path.join(cwd,'reproduced',kind==='equity'?'result.json':'summary.json'))),value);
  assert.equal(readdirSync(path.join(root[kind],'scripts')).includes('__pycache__'),false);
  return value;
 }finally{rmSync(cwd,{recursive:true,force:true});}
}

test('finance equity: one tax shield, full ordinary statements and independent valuation',()=>{
 run('equity',sample('equity'),r=>{
  close(r.wacc,.06875);assert.notEqual(Number(r.wacc),.0640625);
  const cash=[36.25,40,43.75];const w=.06875,g=.02;
  const ev=cash.reduce((s,c,i)=>s+c/(1+w)**(i+1),0)+cash[2]*(1+g)/(w-g)/(1+w)**3;
  close(r.enterprise_value,ev);close(r.per_share,(ev-10)/10);
  for(const h of r.history)for(const v of Object.values(h.checks))close(v,0);
  assert.equal(r.comps[1].pe,null);assert.equal(r.comps[1].ev_ebitda,null);close(r.comps[0].pe,10);close(r.comps[0].ev_ebitda,8.4);
  close(r.sensitivity.find(x=>Number(x.wacc)===w&&Number(x.growth)===g).enterprise_value,ev);
 });
});

test('finance equity: missing debt/shares stay unknown, negative EBIT has no invented tax refund',()=>{
 for(const k of ['net_debt','diluted_shares']){const x=sample('equity');x.assumptions[k]=null;run('equity',x,r=>{assert.equal(r.per_share,null);if(k==='net_debt')assert.equal(r.equity_value,null);});}
 const x=sample('equity');x.forecast[0].ebit=-5;run('equity',x,r=>{close(r.forecast[0].nopat,-5);close(r.forecast[0].fcff,-10);});
});

test('finance equity: inconsistent ordinary inputs cannot become values or zeros',()=>{
 const changes=[x=>x.assumptions.terminal_growth=.06875,x=>x.assumptions.tax_rate=null,x=>x.assumptions.equity_weight=.6,x=>x.assumptions.diluted_shares=0,x=>x.history[1].assets=221,x=>x.history[1].cash_begin=41,x=>x.history[0].noncash_adjustments=11,x=>x.comps[0].currency='USD',x=>x.comps[0].period_end='2023-12-31',x=>x.forecast[0].source_id='unavailable',x=>x.forecast[2].ebit=-20];
 for(const change of changes){const x=sample('equity');change(x);run('equity',x,null,false);}
});

test('finance equity: explicit zero debt, unit scaling and sensitivity boundaries',()=>{
 const x=sample('equity');x.assumptions.net_debt=0;x.sensitivity.wacc=[.01,.06875];
 run('equity',x,r=>{close(r.equity_value,r.enterprise_value);assert.equal(r.sensitivity[0].enterprise_value,null);});
 const y=sample('equity');y.assumptions.diluted_shares=20000000;run('equity',y,r=>close(r.per_share,42.23136858239967));
});

test('finance backtest: nine fills independent cash ledger and final-day T+1 holding',()=>{
 run('backtest',sample('backtest'),(r,out)=>{
  assert.equal(r.fills,9);assert.equal(r.closed_trades,4);assert.equal(r.ending_shares,400);
  close(r.final_value,11094.9157);close(r.realized_pnl,904.5205);close(r.unrealized_pnl_including_entry_fee,190.3952);close(r.total_return,.10949157);
  assert.equal(r.open_position.date,'2024-01-22');assert.equal(r.annual_return,null);assert.equal(r.sharpe,null);
  const lines=readFileSync(path.join(out,'fills.csv'),'utf8').trim().split(/\r?\n/).map(x=>x.trim().split(','));
  const cash=[5591.1956,9978.0044,5468.9999,10952.5109,5742.1057,10128.9145,5720.1101,10904.5205,6094.9157];
  for(let i=1;i<lines.length;i++){close(lines[i][8],cash[i-1]);assert.ok(lines[i][0]>lines[i][1]);}
  const trades=readFileSync(path.join(out,'trades.csv'),'utf8').trim().split(/\r?\n/).slice(1).map(x=>x.split(','));
  close(trades[0][6],-21.9956);close(trades[0][7],-21.9956/4408.8044);assert.notEqual(trades[0][7],trades[0][8]);
  const eq=readFileSync(path.join(out,'equity.csv'),'utf8').trim().split(/\r?\n/).slice(1).map(x=>x.split(','));
  assert.equal(eq[0][0],'2024-01-04');close(eq[0][4],10000);close(eq[0][5],0);
  for(const row of eq)close(Number(row[1])+Number(row[2])*Number(row[3]),row[4]);
 });
});

test('finance backtest: warmup, zero trades, no affordability and minimum holding are explicit',()=>{
 const x=sample('backtest');x.strategy.signals=x.strategy.signals.slice(0,1);run('backtest',x,r=>{assert.equal(r.fills,0);assert.equal(r.win_rate,null);close(r.final_value,10000);});
 const y=sample('backtest');y.initial_cash=1;run('backtest',y,r=>{assert.equal(r.fills,0);close(r.final_value,1);});
 const z=sample('backtest');z.execution.minimum_holding_sessions=30;run('backtest',z,r=>{assert.equal(r.fills,1);assert.equal(r.closed_trades,0);assert.equal(r.ending_shares,400);});
});

test('finance backtest: missing prices/calendar and unsupported corporate-action assumptions rejected',()=>{
 for(const change of [x=>x.bars[5].close=null,x=>x.bars[4].open=null,x=>x.bars.splice(5,1),x=>x.execution.buy_commission=null,x=>x.corporate_actions='split',x=>x.price_adjustment='adjusted',x=>x.execution.lot_size=0,x=>x.strategy.type='portfolio']){
  const x=sample('backtest');change(x);run('backtest',x,null,false);
 }
 const x=sample('backtest');Object.assign(x.bars[4],{open:null,buyable:false,sellable:false});run('backtest',x,r=>assert.equal(r.fills,7));
});

test('finance backtest: explicit lot/minimum fee/slippage and prefix-only decisions',()=>{
 const x=sample('backtest');x.execution.lot_size=1;x.execution.minimum_commission=7;x.execution.slippage=0;
 run('backtest',x,(r,out)=>{assert.ok(r.fees_and_tax>0);const fill=readFileSync(path.join(out,'fills.csv'),'utf8').split(/\r?\n/)[1].split(',');close(fill[4],11);close(fill[5],7);assert.equal(Number(fill[3]),453);});
 const full=sample('backtest');const short=structuredClone(full);short.end=short.calendar[12];short.calendar=short.calendar.slice(0,13);short.bars=short.bars.slice(0,13);short.strategy.signals=short.strategy.signals.filter(s=>s.date<=short.end);
 let prefix;run('backtest',short,(r,out)=>prefix=readFileSync(path.join(out,'equity.csv'),'utf8').trim().split(/\r?\n/));
 run('backtest',full,(r,out)=>assert.deepEqual(readFileSync(path.join(out,'equity.csv'),'utf8').trim().split(/\r?\n/).slice(0,prefix.length),prefix));
});

test('finance backtest: SMA crossover uses warmup indicators without warmup orders',()=>{
 const x=sample('backtest');x.start=x.calendar[4];x.strategy={type:'sma_cross',fast:2,slow:3};
 run('backtest',x,(r,out)=>{assert.ok(r.fills>0);for(const row of readFileSync(path.join(out,'fills.csv'),'utf8').trim().split(/\r?\n/).slice(1))assert.ok(row.split(',')[1]>=x.start);});
 x.start=x.calendar[1];run('backtest',x,null,false);
});


test('finance equity: memo facts have calculated changes and no inferred profit cause',()=>{
 run('equity',sample('equity'),(r,out)=>{
  close(r.historical_growth.revenue,.15);close(r.historical_growth.ebit,.25);close(r.historical_growth.net_income,1/3);
  const cell=r.sensitivity.find(c=>Number(c.wacc)===.06875 && Number(c.growth)===.01);
  const cash=[36.25,40,43.75],w=.06875;const ev=g=>cash.reduce((s,c,i)=>s+c/(1+w)**(i+1),0)+43.75*(1+g)/(w-g)/(1+w)**3;
  close(cell.relative_to_base,ev(.01)/ev(.02)-1);
  close(r.terminal_pv_share,(43.75*1.02/(w-.02)/(1+w)**3)/ev(.02));
  const memo=readFileSync(path.join(out,'memo-facts.md'),'utf8');assert.match(memo,/无法归因/);assert.match(memo,/33.333333%/);assert.match(memo,/不是一律/);
 });
 const x=sample('equity');x.history[0].net_income=-5;x.history[0].noncash_adjustments=45;run('equity',x,r=>assert.equal(r.historical_growth.net_income,null));
});

test('finance equity: version comparison is computed, receipted and preserves missing values',()=>{
 const cwd=mkdtempSync(path.join(tmpdir(),'yijie-equity-update-'));
 try{
  const old=sample('equity'),current=structuredClone(old);current.assumptions.debt_cost_pretax='.06';
  const execute=(prior,next,name)=>{
   writeFileSync(path.join(cwd,'previous.json'),JSON.stringify(prior));writeFileSync(path.join(cwd,'current.json'),JSON.stringify(next));
   const before=['previous.json','current.json'].map(f=>hash(readFileSync(path.join(cwd,f))));
   const r=spawnSync('python3',[path.join(root.equity,'scripts/equity.py'),'--input','current.json','--previous-input','previous.json','--output',name],{cwd,encoding:'utf8'});
   assert.deepEqual(['previous.json','current.json'].map(f=>hash(readFileSync(path.join(cwd,f)))),before);
   return r;
  };
  assert.equal(execute(old,current,'v2').status,0);
  const out=path.join(cwd,'v2'),c=JSON.parse(readFileSync(path.join(out,'comparison.json'))),m=Object.fromEntries(c.metrics.map(x=>[x.metric,x]));
  close(m.terminal_value.current,850);close(m.wacc.percentage_point_change,.375);
  close(m.enterprise_value.relative_change,-.07205096746230057);
  close(m.equity_value.relative_change,-.07290401781184961);assert.equal(m.equity_value.relative_change,m.per_share.relative_change);
  assert.deepEqual(c.input_changes.map(x=>x.path),['/assumptions/debt_cost_pretax']);
  assert.equal(c.matched_sensitivity_cells[0].previous_ev,c.matched_sensitivity_cells[0].current_ev);
  assert.notEqual(c.matched_sensitivity_cells[0].previous_relative_to_base,c.matched_sensitivity_cells[0].current_relative_to_base);
  const receipt=JSON.parse(readFileSync(path.join(out,'receipt.json')));for(const [file,digest] of Object.entries(receipt.files))assert.equal(hash(readFileSync(path.join(out,file))),digest);
  assert.ok(receipt.files['change-note.md']&&receipt.files['comparison.json']&&receipt.files['previous-input.json']);
  assert.match(readFileSync(path.join(out,'change-note.md'),'utf8'),/850\.000000/);
  const absent=structuredClone(current);absent.assumptions.diluted_shares=null;
  assert.equal(execute(current,absent,'no-shares').status,0);
  const missing=JSON.parse(readFileSync(path.join(cwd,'no-shares/comparison.json'))).metrics.find(x=>x.metric==='per_share');assert.equal(missing.current,null);assert.equal(missing.relative_change,null);
  const negative=structuredClone(old);negative.assumptions.net_debt=1000;
  assert.equal(execute(negative,current,'nonpositive-prior').status,0);
  const neg=JSON.parse(readFileSync(path.join(cwd,'nonpositive-prior/comparison.json'))).metrics.find(x=>x.metric==='equity_value');assert.equal(neg.relative_change,null);
  const another=structuredClone(current);another.company='另一合成主体';assert.equal(execute(old,another,'mismatch').status,2);assert.equal(existsSync(path.join(cwd,'mismatch')),false);
 }finally{rmSync(cwd,{recursive:true,force:true});}
});

test('finance backtest: update comparison keeps unavailable deltas unavailable',()=>{
 const cwd=mkdtempSync(path.join(tmpdir(),'yijie-backtest-update-'));
 try{
  const a=sample('backtest'),b=structuredClone(a);b.strategy={type:'sma_cross',fast:2,slow:3};b.execution.minimum_commission=8;
  writeFileSync(path.join(cwd,'previous.json'),JSON.stringify(a));writeFileSync(path.join(cwd,'input.json'),JSON.stringify(b));
  const p=spawnSync('python3',[path.join(root.backtest,'scripts/backtest.py'),'--input','input.json','--previous-input','previous.json','--output','next'],{cwd,encoding:'utf8'});assert.equal(p.status,0,p.stderr);
  const out=path.join(cwd,'next'),c=JSON.parse(readFileSync(path.join(out,'comparison.json'))),m=Object.fromEntries(c.metrics.map(x=>[x.metric,x]));
  close(m.final_value.current,7984.5066);close(m.final_value.absolute_change,-3110.4091);close(m.fees_and_tax.current,46.5934);
  for(const key of ['annual_return','sharpe'])for(const field of ['previous','current','absolute_change','relative_change'])assert.equal(m[key][field],null);
  assert.match(readFileSync(path.join(out,'change-note.md'),'utf8'),/annual_return \| N\/A \| N\/A \| N\/A \| N\/A/);
  const receipt=JSON.parse(readFileSync(path.join(out,'receipt.json')));for(const [file,digest] of Object.entries(receipt.files))assert.equal(hash(readFileSync(path.join(out,file))),digest);
  assert.ok(receipt.files['change-note.md']);assert.deepEqual(JSON.parse(readFileSync(path.join(cwd,'previous.json'))),a);assert.deepEqual(JSON.parse(readFileSync(path.join(cwd,'input.json'))),b);
 }finally{rmSync(cwd,{recursive:true,force:true});}
});
