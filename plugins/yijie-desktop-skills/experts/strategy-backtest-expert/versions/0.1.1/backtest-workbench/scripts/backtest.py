"""Bounded single-asset daily long-only backtest. No data download or live orders."""
import argparse
import csv
import io
import math
import shutil
import statistics
import sys
from decimal import Decimal, ROUND_FLOOR
from pathlib import Path

sys.dont_write_bytecode = True
from common import fields, cite, day, dumps, number, output_folder, read_json, receipt, report, save_csv, save_json, sources, text

D=Decimal


def integer(value, name, low, high):
    if isinstance(value,bool) or not isinstance(value,int) or not low <= value <= high:
        raise ValueError(name+': explicit integer outside range')
    return value


def calculate(data):
    if type(data['schema_version']) is not int or data['schema_version'] != 1:
        raise ValueError('Unsupported schema_version')
    fields(data,['schema_version','symbol','currency','timezone','universe_selection','assumption_rationale','frequency','price_adjustment','corporate_actions','start','end','initial_cash','annual_sessions','risk_free_annual','calendar','bars','execution','strategy','sources','price_source_id','calendar_source_id'])
    ids=sources(data);cite(data['price_source_id'],ids);cite(data['calendar_source_id'],ids)
    for key in ('symbol','currency','timezone','universe_selection','assumption_rationale'):
        text(data[key],key)
    if data['frequency']!='daily' or data['price_adjustment']!='raw' or data['corporate_actions']!='none-in-window':
        raise ValueError('Only raw daily prices with explicitly no corporate actions in the window are supported')
    start,end=day(data['start']),day(data['end'])
    if start>end:
        raise ValueError('start must precede end')
    bars=data['bars']; calendar=data['calendar']
    if not isinstance(bars,list) or not 2<=len(bars)<=20000:
        raise ValueError('2–20000 price bars required')
    dates=[r['date'] for r in bars]
    if dates != calendar or dates != sorted(set(dates)):
        raise ValueError('Bars must exactly match the supplied ordered trading calendar, without duplicates/gaps')
    if data['start'] not in dates or data['end'] != dates[-1]:
        raise ValueError('Evaluation start/end must match provided sessions; no silent period truncation')
    clean=[]
    for row in bars:
        day(row['date'])
        if type(row['buyable']) is not bool or type(row['sellable']) is not bool:
            raise ValueError('Explicit buyable/sellable booleans required for each session')
        opening=number(row.get('open'),'open',D('.00000001'),optional=True)
        if opening is None and (row['buyable'] or row['sellable']):
            raise ValueError('Missing open on a tradable session')
        closing=number(row['close'],'close',D('.00000001'))
        clean.append(dict(row,open=opening,close=closing))
    policy=data['execution']
    fields(policy,['signal_timing','fill_timing','unfilled_policy','end_position','lot_size','minimum_holding_sessions','allocation','buy_commission','sell_commission','sell_tax','slippage','minimum_commission'])
    if policy['signal_timing']!='close' or policy['fill_timing']!='next-session-open' or policy['unfilled_policy']!='cancel' or policy['end_position']!='mark-to-close':
        raise ValueError('Unsupported execution policy')
    lot=integer(policy['lot_size'],'lot_size',1,1000000)
    hold=integer(policy['minimum_holding_sessions'],'minimum_holding_sessions',0,250)
    annual=integer(data['annual_sessions'],'annual_sessions',1,366)
    initial=number(data['initial_cash'],'initial_cash',D('.01'))
    allocation=number(policy['allocation'],'allocation',D('.000001'),1)
    fees={k:number(policy[k],k,0,D('.1')) for k in ('buy_commission','sell_commission','sell_tax','slippage')}
    minimum=number(policy['minimum_commission'],'minimum_commission',0)
    risk_free=number(data['risk_free_annual'],'risk_free_annual',D('-.5'),D('.5'))
    strategy=data['strategy'];signals={}
    if strategy['type']=='sma_cross':
        fields(strategy,['type','fast','slow'])
        fast=integer(strategy['fast'],'fast',1,5000);slow=integer(strategy['slow'],'slow',2,5000)
        if fast>=slow or dates.index(data['start'])<slow:
            raise ValueError('SMA requires fast<slow and at least slow warmup sessions for prior crossover state')
    elif strategy['type']=='close_signals':
        fields(strategy,['type','source_id','signals'])
        cite(strategy['source_id'],ids)
        for signal in strategy['signals']:
            if signal['date'] not in dates or signal['known_at_close'] != signal['date'] or signal['action'] not in ('buy','sell') or signal['date'] in signals:
                raise ValueError('Signals require one explicit action per supplied close date, known_at_close equal to date')
            signals[signal['date']]=signal['action']
    else:
        raise ValueError('Only sma_cross and close_signals implemented; no events/grid/portfolio/short engine')
    cash=initial;position=0;entry=None;pending=None;fills=[];trades=[];equity=[];decisions=[];closes=[];previous_spread=None
    peak=initial;previous=initial;total_costs=D(0)
    for i,row in enumerate(clean):
        current=day(row['date']);closes.append(row['close']);spread=None
        if strategy['type']=='sma_cross' and len(closes)>=slow:
            spread=sum(closes[-fast:])/fast-sum(closes[-slow:])/slow
        if current<start:
            previous_spread=spread
            continue  # indicators only: no pending orders, fills, position or NAV records
        if pending is not None:
            action,signal_date=pending;status='no-position-change';pending=None
            if not row['buyable' if action=='buy' else 'sellable']:
                status='cancelled-not-tradable'
            elif action=='buy' and position==0:
                price=row['open']*(1+fees['slippage']);budget=cash*allocation
                # Both proportional and minimum fees must fit the budget. No future close used.
                by_rate=budget/(price*(1+fees['buy_commission']))
                by_minimum=max(D(0),budget-minimum)/price
                size=int((min(by_rate,by_minimum)/lot).to_integral_value(rounding=ROUND_FLOOR))*lot
                if size:
                    commission=max(minimum,size*price*fees['buy_commission']);cost=size*price+commission
                    cash-=cost;position=size;total_costs+=commission
                    entry={'date':row['date'],'bar':i,'price':price,'cost':cost,'size':size,'commission':commission}
                    fills.append({'date':row['date'],'signal_date':signal_date,'action':'buy','size':size,'price':price,'commission':commission,'tax':D(0),'cash_delta':-cost,'cash_after':cash,'position_after':position})
                    status='filled'
                else:
                    status='cancelled-budget-below-lot-and-fees'
            elif action=='sell' and position>0:
                if i-entry['bar']<hold:
                    status='cancelled-minimum-holding'
                else:
                    price=row['open']*(1-fees['slippage']);gross=position*price;commission=max(minimum,gross*fees['sell_commission']);tax=gross*fees['sell_tax'];proceeds=gross-commission-tax
                    if proceeds<0:
                        raise ValueError('Sell proceeds do not cover fees; unsupported insolvent liquidation')
                    cash+=proceeds;total_costs+=commission+tax;pnl=proceeds-entry['cost']
                    trades.append({'entry_date':entry['date'],'exit_date':row['date'],'side':'long','size':position,'entry_price':entry['price'],'exit_price':price,'pnl':pnl,'net_return':pnl/entry['cost'],'gross_price_return':price/entry['price']-1,'holding_sessions':i-entry['bar'],'symbol':data['symbol']})
                    fills.append({'date':row['date'],'signal_date':signal_date,'action':'sell','size':position,'price':price,'commission':commission,'tax':tax,'cash_delta':proceeds,'cash_after':cash,'position_after':0})
                    position=0;entry=None;status='filled'
            decisions.append({'date':row['date'],'signal_date':signal_date,'action':action,'status':status})
        if strategy['type']=='sma_cross':
            action='buy' if previous_spread is not None and spread is not None and previous_spread<=0<spread else 'sell' if previous_spread is not None and spread is not None and previous_spread>=0>spread else None
        else:
            action=signals.get(row['date'])
        if action:
            if current<end:
                pending=(action,row['date'])
            else:
                decisions.append({'date':row['date'],'signal_date':row['date'],'action':action,'status':'not-submitted-no-next-session'})
        value=cash+position*row['close'];peak=max(peak,value)
        equity.append({'date':row['date'],'cash':cash,'position':position,'close':row['close'],'value':value,'daily_return':value/previous-1 if previous else D(0),'drawdown':value/peak-1})
        previous=value;previous_spread=spread
        if cash<0:
            raise ValueError('Cash reconciliation failed')
    final=equity[-1]['value']; realized=sum((t['pnl'] for t in trades),D(0));unrealized=D(0) if entry is None else position*clean[-1]['close']-entry['cost']
    if abs(final-initial-realized-unrealized)>D('0.00000001'):
        raise ValueError('Equity does not reconcile to realized and open-position PnL')
    returns=[float(x['daily_return']) for x in equity];daily_rf=(1+float(risk_free))**(1/annual)-1
    std=statistics.stdev(returns) if len(returns)>1 else 0
    sharpe=None if std==0 else (statistics.mean(returns)-daily_rf)/std*math.sqrt(annual)
    n=len(equity)
    # Short samples are not annualized into persuasive-looking performance claims.
    annual_return=None if n<annual or final<=0 else float(final/initial)**(annual/n)-1
    summary={'schema_version':1,'symbol':data['symbol'],'currency':data['currency'],'return_units':'decimal, not percent','start':data['start'],'end':data['end'],'initial_cash':initial,'final_value':final,'total_return':final/initial-1,'annual_return':annual_return,'sharpe':sharpe if n>=annual else None,'max_drawdown':-min(x['drawdown'] for x in equity),'closed_trades':len(trades),'fills':len(fills),'win_rate':None if not trades else D(sum(t['pnl']>0 for t in trades))/len(trades),'realized_pnl':realized,'unrealized_pnl_including_entry_fee':unrealized,'fees_and_tax':total_costs,'open_position':entry,'ending_shares':position,'annualization_note':'Annual return and Sharpe unavailable below one explicit annual_sessions sample.','limitations':['User-supplied calendar, tradability and absence of corporate actions are assertions, not independently authenticated market facts.','Next-open fills assume liquidity for the full order; no volume/queue/auction model.','No cash interest, dividends, FX, corporate actions, shorting, broker execution or automatic online data.','Synthetic/backtested results are hypothetical, not achieved returns.']}
    return summary,equity,trades,fills,decisions


def load_input(input_path):
    data=read_json(input_path)
    if 'bars_file' in data:
        path=input_path.parent/data['bars_file']
        if Path(data['bars_file']).is_absolute() or '..' in Path(data['bars_file']).parts or path.is_symlink() or not path.is_file() or path.stat().st_size>2_000_000:
            raise ValueError('bars_file must be a local relative ordinary CSV (max 2 MB)')
        rows=list(csv.DictReader(io.StringIO(path.read_text(encoding='utf-8-sig'))))
        for r in rows:
            for k in ('buyable','sellable'):
                if r[k] not in ('true','false'):
                    raise ValueError('CSV tradability requires true/false')
                r[k]=r[k]=='true'
            if r['open']=='':r['open']=None
        if 'bars' in data:
            raise ValueError('Use bars or bars_file, not both')
        data['bars']=rows;del data['bars_file']
    return data


def compare(previous_data,data,previous,current):
    for key in ('symbol','currency','start','end','frequency','price_adjustment'):
        if previous_data[key]!=data[key]:raise ValueError('Version comparison requires matching '+key)
    changes=[]
    def walk(a,b,path=''):
        if isinstance(a,dict) and isinstance(b,dict):
            for key in sorted(a.keys()|b.keys()):walk(a.get(key),b.get(key),path+'/'+key)
        elif a!=b:changes.append({'path':path,'previous':a,'current':b})
    walk(previous_data,data)
    metrics=[]
    for key in ('initial_cash','final_value','total_return','annual_return','sharpe','max_drawdown','closed_trades','fills','win_rate','realized_pnl','unrealized_pnl_including_entry_fee','fees_and_tax','ending_shares'):
        a=None if previous[key] is None else D(str(previous[key]));b=None if current[key] is None else D(str(current[key]))
        metrics.append({'metric':key,'previous':a,'current':b,'absolute_change':None if a is None or b is None else b-a,'relative_change':None if a is None or b is None or a<=0 else b/a-1})
    return {'schema_version':1,'currency':data['currency'],'start':data['start'],'end':data['end'],'comparison_basis':'Both saved inputs recalculated with the current reviewed calculator; no causal attribution between multiple changed inputs.','input_changes':changes,'metrics':metrics}


def comparison_markdown(comparison):
    def value(v):return 'N/A' if v is None else format(v,'.8f')
    lines=['# 程序生成的版本差异','',comparison['comparison_basis'],'',
           '来源：previous-input.json 与 input.json。币种 '+comparison['currency']+'，区间 '+comparison['start']+' 至 '+comparison['end']+'。收益率和回撤使用小数口径，非百分比。',
           '缺任一值时差值也为N/A；上版非正时相对变化为N/A。策略和费用同时改变不能把全部差异归因于某一项。', '',
           '| 指标 | 上版 | 本版 | 绝对变化 | 相对变化（小数） |','|---|---|---|---|---|']
    for r in comparison['metrics']:
        lines.append('| '+r['metric']+' | '+value(r['previous'])+' | '+value(r['current'])+' | '+value(r['absolute_change'])+' | '+value(r['relative_change'])+' |')
    lines += ['', '## 输入字段变更', '完整旧值/新值见comparison.json的input_changes。']
    lines += ['- '+r['path'] for r in comparison['input_changes']] or ['- 无字段变更']
    return '\n'.join(lines)+'\n'


def run(input_path,out_path,previous_input=None):
    data=load_input(input_path);summary,equity,trades,fills,decisions=calculate(data);comparison=None
    if previous_input is not None:
        previous_data=load_input(previous_input)
        comparison=compare(previous_data,data,calculate(previous_data)[0],summary)
    out=output_folder(out_path)
    if comparison is not None:
        save_json(out/'previous-input.json',previous_data);save_json(out/'comparison.json',comparison)
        (out/'change-note.md').write_text(comparison_markdown(comparison))
    save_json(out/'input.json',data);save_json(out/'summary.json',summary);save_json(out/'decisions.json',decisions)
    save_csv(out/'equity.csv',equity,['date','cash','position','close','value','daily_return','drawdown'])
    trade_fields=['entry_date','exit_date','side','size','entry_price','exit_price','pnl','net_return','gross_price_return','holding_sessions','symbol']
    fill_fields=['date','signal_date','action','size','price','commission','tax','cash_delta','cash_after','position_after']
    save_csv(out/'trades.csv',trades,trade_fields);save_csv(out/'fills.csv',fills,fill_fields)
    sections=[{'title':'收益摘要','columns':['指标','值'],'rows':[[k,v] for k,v in summary.items() if not isinstance(v,(dict,list))]},
              {'title':'权益明细','columns':['日期','现金','持股','收盘价','权益','日收益','回撤'],'rows':[list(x.values()) for x in equity]},
              {'title':'已平仓交易','columns':trade_fields,'rows':[[x[k] for k in trade_fields] for x in trades]},
              {'title':'成交流水','columns':fill_fields,'rows':[[x[k] for k in fill_fields] for x in fills]},
              {'title':'信号与未成交','columns':['日期','信号日期','方向','状态'],'rows':[list(x.values()) for x in decisions]},
              {'title':'来源与假设','columns':['字段','内容'],'rows':[[k,dumps(data[k]).strip()] for k in ('sources','strategy','execution','price_adjustment','corporate_actions','timezone','universe_selection','assumption_rationale')]}]
    report(out,data['symbol']+' · 策略回测',sections,[{'value':data['initial_cash']}]+equity)
    (out/'method.md').write_text('# 回测口径\n\n'+ '\n'.join('- '+s for s in summary['limitations'])+'\n\n用 python3 -B backtest.py --input input.json --output ../新版本目录 重跑；旧结果不覆盖。\n')
    for name in ('backtest.py','common.py'):
        shutil.copy2(Path(__file__).parent/name,out/name)
    receipt(out);print(dumps({'output':str(out),'summary':summary}))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--input',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--previous-input',type=Path);args=parser.parse_args()
    try:run(args.input,args.output,args.previous_input)
    except (ValueError,KeyError,TypeError,OSError,ArithmeticError) as error:parser.exit(2,'Backtest unavailable: '+str(error)+'\n')
