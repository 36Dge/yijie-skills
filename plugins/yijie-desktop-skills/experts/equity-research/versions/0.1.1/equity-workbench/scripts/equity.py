"""Annual FCFF valuation from explicit, same-unit inputs. Python 3.10+, no network."""
import argparse
import shutil
import sys
from decimal import Decimal
from pathlib import Path

sys.dont_write_bytecode = True
from common import fields, cite, day, dumps, number, output_folder, read_json, receipt, report, save_json, sources, text
from artifacts import write_xlsx

D = Decimal


def calculate(data):
    if type(data['schema_version']) is not int or data['schema_version'] != 1:
        raise ValueError('Unsupported schema_version')
    fields(data, ['schema_version','company','currency','amount_scale','as_of','period_basis','discount_timing','sources','history','assumptions','forecast','sensitivity','comps'])
    ids = sources(data)
    text(data['company'], 'company')
    text(data['currency'], 'currency')
    as_of = day(data['as_of'])
    scale = number(data['amount_scale'], 'amount_scale', 1)
    if scale not in (1, 1000, 10000, 1000000, 100000000):
        raise ValueError('Unsupported amount_scale')
    if data['period_basis'] != 'annual' or data['discount_timing'] != 'year-end':
        raise ValueError('Only annual year-end FCFF is implemented')
    history = data['history']
    if not isinstance(history, list) or not 2 <= len(history) <= 10:
        raise ValueError('2–10 annual statements required')
    checked, last_end, last_cash = [], None, None
    keys = ['assets','liabilities','equity','cash_begin','cash_end','cfo','cfi','cff','fx',
            'revenue','ebit','net_income','noncash_adjustments','change_working_capital']
    for row in history:
        start, end = day(row['period_start']), day(row['period_end'])
        if not 360 <= (end-start).days <= 371 or end > as_of or last_end is not None and (start-last_end).days != 1:
            raise ValueError('Annual periods must be consecutive and end by as_of')
        cite(row['source_id'], ids)
        values = {k: number(row[k], k) for k in keys}
        residuals = {
            'balance': values['assets']-values['liabilities']-values['equity'],
            'cash_flow': values['cash_begin']+values['cfo']+values['cfi']+values['cff']+values['fx']-values['cash_end'],
            'income_to_cfo': values['net_income']+values['noncash_adjustments']-values['change_working_capital']-values['cfo'],
            'cash_continuity': D(0) if last_cash is None else values['cash_begin']-last_cash,
        }
        # Absolute tolerance is one cent of currency, expressed in the selected amount unit.
        if any(abs(v)*scale > D('.01') for v in residuals.values()):
            raise ValueError('Statements do not reconcile: '+row['period_end']+' '+dumps(residuals))
        checked.append(dict(row, **values, checks=residuals))
        last_end, last_cash = end, values['cash_end']
    if any(day(s['as_of']) > as_of for s in data['sources']):
        raise ValueError('Source observed after valuation as_of; use a new dated model')
    assumptions = data['assumptions']
    fields(assumptions,['source_id','rationale','cost_equity','debt_cost_pretax','tax_rate','equity_weight','debt_weight','terminal_growth'],['net_debt','diluted_shares'])
    cite(assumptions['source_id'], ids)
    text(assumptions['rationale'], 'assumption rationale')
    a = {k: number(assumptions[k], k, 0, 1) for k in ('cost_equity','debt_cost_pretax','tax_rate','equity_weight','debt_weight')}
    if a['equity_weight']+a['debt_weight'] != 1:
        raise ValueError('Capital market-value weights must sum to 1')
    a['terminal_growth'] = number(assumptions['terminal_growth'], 'terminal_growth', D('-.5'), D('.5'))
    a['net_debt'] = number(assumptions.get('net_debt'), 'net_debt', optional=True)
    a['diluted_shares'] = number(assumptions.get('diluted_shares'), 'diluted_shares', D('.00000001'), optional=True)
    wacc = a['cost_equity']*a['equity_weight']+a['debt_cost_pretax']*(1-a['tax_rate'])*a['debt_weight']
    if wacc <= a['terminal_growth'] or wacc <= 0:
        raise ValueError('DCF unavailable: WACC must be positive and greater than terminal_growth')
    forecasts = data['forecast']
    if not isinstance(forecasts, list) or not 1 <= len(forecasts) <= 10:
        raise ValueError('1–10 explicit future annual forecasts required')
    calculated = []
    for year, row in enumerate(forecasts, 1):
        fields(row, ['year','source_id','ebit','da','capex','delta_wc'])
        if type(row['year']) is not int or row['year'] != year:
            raise ValueError('Forecast years must be contiguous offsets 1..N after valuation date')
        cite(row['source_id'], ids)
        v = {k: number(row[k], k) for k in ('ebit','da','capex','delta_wc')}
        if v['da'] < 0 or v['capex'] < 0:
            raise ValueError('DA and capex must be nonnegative')
        # Loss-making forecasts do not receive an invented immediate tax refund.
        nopat = v['ebit']-max(v['ebit'], D(0))*a['tax_rate']
        fcff = nopat+v['da']-v['capex']-v['delta_wc']
        calculated.append(dict(row, **v, nopat=nopat, fcff=fcff, pv=fcff/(1+wacc)**year))
    if calculated[-1]['fcff'] <= 0:
        raise ValueError('Positive normalized terminal FCFF required; loss/restructuring models unsupported')
    def valuation(rate, growth):
        if rate <= growth or rate <= 0:
            return None
        return sum(row['fcff']/(1+rate)**row['year'] for row in calculated)+calculated[-1]['fcff']*(1+growth)/(rate-growth)/(1+rate)**len(calculated)
    terminal = calculated[-1]['fcff']*(1+a['terminal_growth'])/(wacc-a['terminal_growth'])
    ev = valuation(wacc, a['terminal_growth'])
    equity = None if a['net_debt'] is None else ev-a['net_debt']
    per_share = None if equity is None or a['diluted_shares'] is None else equity*scale/a['diluted_shares']
    sensitivity = data['sensitivity']
    rates = [number(x, 'sensitivity.wacc', D('.000001'), 1) for x in sensitivity['wacc']]
    growths = [number(x, 'sensitivity.growth', D('-.5'), D('.5')) for x in sensitivity['growth']]
    if not 1 <= len(rates) <= 9 or not 1 <= len(growths) <= 9:
        raise ValueError('Sensitivity axes require 1–9 entries each')
    comps = []
    if not isinstance(data['comps'], list) or len(data['comps']) > 50:
        raise ValueError('At most 50 comparable companies')
    for c in data['comps']:
        text(c['name'], 'comparable name'); cite(c['source_id'], ids)
        if c['currency'] != data['currency'] or number(c['amount_scale'], 'comps scale') != scale:
            raise ValueError('Comps require explicit same currency and amount_scale; no automatic FX')
        if day(c['as_of']) != as_of or c['period_start'] != history[-1]['period_start'] or c['period_end'] != history[-1]['period_end']:
            raise ValueError('Comps must share market as_of and latest historical earnings period')
        v = {k: number(c.get(k), k, optional=True) for k in ('market_cap','net_debt','ebitda','net_income')}
        ce = None if v['market_cap'] is None or v['net_debt'] is None else v['market_cap']+v['net_debt']
        def multiple(n, denominator):
            return None if n is None or denominator is None or n <= 0 or denominator <= 0 else n/denominator
        comps.append(dict(c, **v, enterprise_value=ce, ev_ebitda=multiple(ce,v['ebitda']), pe=multiple(v['market_cap'],v['net_income'])))
    return {'schema_version':1,'company':data['company'],'currency':data['currency'],'amount_scale':scale,'as_of':data['as_of'],
            'assumptions':a,'history':checked,'forecast':calculated,'wacc':wacc,'terminal_value':terminal,'enterprise_value':ev,
            'equity_value':equity,'per_share':per_share,'comps':comps,
            'sensitivity':[{'wacc':r,'growth':g,'enterprise_value':valuation(r,g)} for r in rates for g in growths],
            'limitations':['Forecasts are explicit assumptions, not verified facts.','Net debt must include all equity bridge adjustments; no automatic preferred/minority/pension inference.',
                           'Annual year-end FCFF; no loss carryforward, midyear convention, options or complex capital structure.',
                           'No automatic financial data retrieval, rating, target recommendation or full initiating-coverage document.']}


def workbook(path, data, result):
    a=result['assumptions']; f=result['forecast']; n=len(f); last=2+n
    inputs=[['输入 / 单位','值'],['权益成本（小数）',a['cost_equity']],['税前债务成本（小数）',a['debt_cost_pretax']],['税率（小数）',a['tax_rate']],['权益市值权重',a['equity_weight']],['债务市值权重',a['debt_weight']],['永续增长率（小数）',a['terminal_growth']],['净债务 / 含其他权益桥接项',a['net_debt']],['稀释股数 / 股',a['diluted_shares']],['金额倍率',result['amount_scale']],['币种',data['currency']],['估值时点',data['as_of']],['来源',data['assumptions']['source_id']],['假设依据',data['assumptions']['rationale']]]
    build=[['DCF / 年末现金流','EBIT','折旧摊销','资本支出','营运资本增加','NOPAT','FCFF','现值'],['WACC',('IF(AND(COUNT(Inputs!B2:B6)=5,Inputs!B5+Inputs!B6=1,MIN(Inputs!B2:B6)>=0,MAX(Inputs!B2:B6)<=1),Inputs!B2*Inputs!B5+Inputs!B3*(1-Inputs!B4)*Inputs!B6,"N/A")',result['wacc'])]]
    for i,row in enumerate(f,3):
        build.append([row['year'],row['ebit'],row['da'],row['capex'],row['delta_wc'],(f'IF(AND(COUNT(B{i}:E{i})=4,C{i}>=0,D{i}>=0,ISNUMBER(Inputs!$B$4)),B{i}-MAX(B{i},0)*Inputs!$B$4,"N/A")',row['nopat']),(f'IF(ISNUMBER(F{i}),F{i}+C{i}-D{i}-E{i},"N/A")',row['fcff']),(f'IF(AND(ISNUMBER($B$2),ISNUMBER(G{i})),G{i}/(1+$B$2)^A{i},"N/A")',row['pv'])])
    tv=last+2; ev=tv+1; eq=tv+2; ps=tv+3
    build += [[],['终值',(f'IF(AND(ISNUMBER(B2),B2>0,ISNUMBER(Inputs!B7),B2>Inputs!B7,Inputs!B7>=-0.5,Inputs!B7<=0.5,COUNT(G3:G{last})={n},G{last}>0),G{last}*(1+Inputs!B7)/(B2-Inputs!B7),"N/A")',result['terminal_value'])],['企业价值',(f'IF(ISNUMBER(B{tv}),SUM(H3:H{last})+B{tv}/(1+B2)^A{last},"N/A")',result['enterprise_value'])],['股权价值',(f'IF(AND(ISNUMBER(B{ev}),ISNUMBER(Inputs!B8)),B{ev}-Inputs!B8,"N/A")',result['equity_value'])],['每股价值',(f'IF(AND(ISNUMBER(B{eq}),ISNUMBER(Inputs!B9),Inputs!B9>0),B{eq}*Inputs!B10/Inputs!B9,"N/A")',result['per_share'])]]
    summary=[['估值结果 / '+data['company'],'值'],['WACC',('DCF!B2',result['wacc'])],['企业价值',(f'DCF!B{ev}',result['enterprise_value'])],['股权价值',(f'DCF!B{eq}',result['equity_value'])],['每股价值',(f'DCF!B{ps}',result['per_share'])],['金额单位',data['currency']+' × '+str(result['amount_scale'])],['每股单位',data['currency']+'/股'],['估值时点',data['as_of']],['预测属性','用户明确假设，非事实；未取在线数据']]
    history=[['期间','资产','负债','权益','期初现金','期末现金','经营现金流','投资现金流','融资现金流','汇率影响','收入','EBIT','净利润','非现金调整','营运资本变化','资产负债差','现金差','利润至现金差','现金连续差']]
    for i,row in enumerate(result['history'],2):
        history.append([row['period_end']]+[row[k] for k in ['assets','liabilities','equity','cash_begin','cash_end','cfo','cfi','cff','fx','revenue','ebit','net_income','noncash_adjustments','change_working_capital']]+[(f'B{i}-C{i}-D{i}',row['checks']['balance']),(f'E{i}+G{i}+H{i}+I{i}+J{i}-F{i}',row['checks']['cash_flow']),(f'M{i}+N{i}-O{i}-G{i}',row['checks']['income_to_cfo']),(f'E{i}-F{i-1}' if i>2 else '0',row['checks']['cash_continuity'])])
    comps=[['公司','市值','净债务','EBITDA','净利润','企业价值','EV/EBITDA','P/E']]
    for i,row in enumerate(result['comps'],2):
        comps.append([row['name']]+[row[k] for k in ['market_cap','net_debt','ebitda','net_income']]+[(f'IF(COUNT(B{i}:C{i})=2,B{i}+C{i},"N/A")',row['enterprise_value']),(f'IF(AND(ISNUMBER(F{i}),ISNUMBER(D{i}),F{i}>0,D{i}>0),F{i}/D{i},"NM")',row['ev_ebitda']),(f'IF(AND(ISNUMBER(B{i}),ISNUMBER(E{i}),B{i}>0,E{i}>0),B{i}/E{i},"NM")',row['pe'])])
    sensitivity=[['WACC / 情景输入','永续增长 / 情景输入','企业价值 / 金额单位']]
    for i,row in enumerate(result['sensitivity'],2):
        pv='+'.join(f'DCF!G{r}/(1+A{i})^DCF!A{r}' for r in range(3,last+1))
        formula=f'IF(AND(ISNUMBER(A{i}),ISNUMBER(B{i}),A{i}>0,A{i}<=1,A{i}>B{i},B{i}>=-0.5,B{i}<=0.5,COUNT(DCF!G3:G{last})={n}),{pv}+DCF!G{last}*(1+B{i})/(A{i}-B{i})/(1+A{i})^DCF!A{last},"N/A")'
        sensitivity.append([row['wacc'],row['growth'],(formula,row['enterprise_value'])])
    source_rows=[['ID','类型','位置','资料日期','说明']]+[[s[k] for k in ('id','kind','locator','as_of','description')] for s in data['sources']]
    source_rows += [['历史 '+r['period_end'],r['source_id']] for r in data['history']]+[['预测第 '+str(r['year'])+' 年',r['source_id']] for r in data['forecast']]+[['可比 '+r['name'],r['source_id']] for r in data['comps']]
    write_xlsx(path,[('Summary',summary),('DCF',build),('Sensitivity',sensitivity),('Comps',comps),('History',history),('Inputs',inputs),('Sources',source_rows)])


def run(input_path, out_path):
    data=read_json(input_path); result=calculate(data); out=output_folder(out_path)
    previous,latest=result['history'][-2:]
    result['historical_growth']={key:None if previous[key]<=0 else latest[key]/previous[key]-1 for key in ('revenue','ebit','net_income','cfo')}
    result['terminal_pv_share']=None if result['enterprise_value']<=0 else result['terminal_value']/(1+result['wacc'])**len(result['forecast'])/result['enterprise_value']
    for cell in result['sensitivity']:
        cell['relative_to_base']=None if cell['enterprise_value'] is None or result['enterprise_value']<=0 else cell['enterprise_value']/result['enterprise_value']-1
    save_json(out/'input.json',data);save_json(out/'result.json',result)
    facts=['# 研究稿可引用计算', '', '仅描述输入和实际计算。合成资料不是市场事实。缺成本、费用、税项及非经常明细，无法归因利润变化。', '', '## 最新两期同比', '| 指标 | 同比变化 |', '|---|---|']
    labels={'revenue':'收入','ebit':'EBIT','net_income':'净利润','cfo':'经营现金流'}
    for key,value in result['historical_growth'].items():
        facts.append('| '+labels[key]+' | '+('N/A（上期非正）' if value is None else format(value*100,'.6f')+'%')+' |')
    facts += ['', '## 敏感性相对基准', '每行是该组WACC/g情景相对实际基准的变化，不是一律±1个百分点的效果。', '| WACC | g | 企业价值 | 相对基准变化 |', '|---|---|---|---|']
    for cell in result['sensitivity']:
        delta=cell['relative_to_base']
        facts.append('| '+str(cell['wacc'])+' | '+str(cell['growth'])+' | '+str(cell['enterprise_value'])+' | '+('N/A' if delta is None else format(delta*100,'.6f')+'%')+' |')
    share=result['terminal_pv_share']
    facts += ['', '终值现值占企业价值：'+('N/A' if share is None else format(share*100,'.6f')+'%')+'。占比高意味着对终值假设更敏感，不能据此保证未来收益。', '', '所有派生数字均可由 result.json 回溯；事实/假设/判断分别标记，因果解释须有额外来源。']
    (out/'memo-facts.md').write_text('\n'.join(facts)+'\n')
    workbook(out/'valuation.xlsx',data,result)
    sections=[{'title':'估值','columns':['指标','值'],'rows':[[k,result[k]] for k in ('wacc','enterprise_value','equity_value','per_share','currency','amount_scale','as_of')]},
              {'title':'现金流预测','columns':['年','EBIT','NOPAT','FCFF','现值'],'rows':[[r[k] for k in ('year','ebit','nopat','fcff','pv')] for r in result['forecast']]},
              {'title':'敏感性','columns':['WACC','永续增长','企业价值'],'rows':[[r[k] for k in ('wacc','growth','enterprise_value')] for r in result['sensitivity']]},
              {'title':'可比公司','note':'亏损、零分母或缺值为 N/A / NM，不能当作 0 倍。','columns':['公司','EV/EBITDA','P/E'],'rows':[[r[k] for k in ('name','ev_ebitda','pe')] for r in result['comps']]},
              {'title':'三表核对','columns':['年末','资产负债差','现金差','利润至现金差','期初衔接差'],'rows':[[r['period_end']]+list(r['checks'].values()) for r in result['history']]},
              {'title':'来源与边界','columns':['来源','类型','位置','日期','说明'],'rows':[[s[k] for k in ('id','kind','locator','as_of','description')] for s in data['sources']]}]
    report(out,data['company']+' · 股票研究',sections)
    (out/'research.md').write_text('# '+data['company']+'\n\n本文件为计算交付说明，研究判断应另存带来源的备忘录。\n\n'+ '\n'.join('- '+x for x in result['limitations'])+'\n\n金额单位 '+data['currency']+' × '+str(result['amount_scale'])+'；稀释股数为实际股数。\n')
    for name in ('equity.py','common.py','artifacts.py'):
        shutil.copy2(Path(__file__).parent/name,out/name)
    receipt(out)
    print(dumps({'output':str(out),'wacc':result['wacc'],'per_share':result['per_share']}))


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--input',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    try:
        run(args.input,args.output)
    except (ValueError,KeyError,TypeError,OSError,ArithmeticError) as error:
        parser.exit(2,'Equity calculation unavailable: '+str(error)+'\n')
