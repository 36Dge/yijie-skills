"""YiJie MOSS adaptation: evidence-linked local calculations and frozen delivery.

No external API, credentials, background jobs, upstream executables or auto-install.
"""
import argparse
import sys
sys.dont_write_bytecode = True
import hashlib
import json
import re
from decimal import Decimal, localcontext
from pathlib import Path
from common import day, dumps, fields, number, output_folder, read_json, save_json, text

VERSION = '0.1.1'


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    separators=(',', ':'), default=str).encode()).hexdigest()


def items(value, label, maximum=100, empty=False):
    if not isinstance(value, list) or not (0 if empty else 1) <= len(value) <= maximum:
        raise ValueError(label + ': invalid list length')
    return value


def indexed(rows, label):
    result = {}
    for row in items(rows, label):
        key = text(row['id'], label + ' id')
        if not re.fullmatch(r'[a-zA-Z][a-zA-Z0-9_-]{0,63}', key) or key in result:
            raise ValueError(label + ': invalid or duplicate id')
        result[key] = row
    return result


def validate(state):
    fields(state, ['schema_version','research_id','revision','mode','title','scope','plan',
                   'sources','facts','calculations','findings','gaps','formats'])
    if state['schema_version'] != 1 or state['mode'] not in ('offline', 'connector-evidence'):
        raise ValueError('Unsupported schema or mode')
    text(state['research_id'], 'research_id'); text(state['revision'], 'revision')
    text(state['title'], 'title')
    scope = state['scope']
    fields(scope, ['industry','geography','boundary','currency','year','as_of'])
    for key in ['industry','geography','boundary','currency']: text(scope[key], key)
    if not isinstance(scope['year'], int) or isinstance(scope['year'], bool) or not 1900 <= scope['year'] <= 2200:
        raise ValueError('Explicit integer scope year required')
    day(scope['as_of'])
    plan = state['plan']; fields(plan, ['decision','depth','questions','steps'])
    text(plan['decision'], 'decision')
    if plan['depth'] not in ('standard','deep'): raise ValueError('Unsupported research depth')
    for key in ['questions','steps']:
        for value in items(plan[key], key, 20): text(value, key)
    sources = indexed(state['sources'], 'sources')
    for source in sources.values():
        fields(source, ['id','kind','title','locator','published_on','retrieved_on','content'], ['service_id','tool_ref','receipt_ref'])
        for key in ['title','locator','content']: text(source[key], key)
        if source['kind'] not in ('synthetic','user-file','qualified-connector'):
            raise ValueError('Unsupported source kind')
        if day(source['published_on']) > day(source['retrieved_on']) or day(source['retrieved_on']) > day(scope['as_of']):
            raise ValueError('Source dates inconsistent with research date')
        if source['kind'] == 'qualified-connector':
            if state['mode'] != 'connector-evidence': raise ValueError('Offline mode cannot claim connector execution')
            for key in ['service_id','tool_ref','receipt_ref']: text(source.get(key), key)
    facts = indexed(state['facts'], 'facts')
    for fact in facts.values():
        fields(fact, ['id','source_id','quote','value','unit','year','geography','boundary','status','limitation'])
        if fact['source_id'] not in sources: raise ValueError('Missing fact source')
        if text(fact['quote'], 'quote') not in sources[fact['source_id']]['content']:
            raise ValueError('Fact quotation is not in retained source')
        for key in ['unit','geography','boundary','limitation']: text(fact[key], key)
        if type(fact['year']) is not int: raise ValueError('Fact year must be explicit')
        if fact['status'] not in ('observed','assumption','unknown'): raise ValueError('Invalid fact status')
        number(fact['value'], 'fact value', optional=True)
        if (fact['value'] is None) != (fact['status'] == 'unknown'):
            raise ValueError('Unknown facts must have null value; missing is never zero')
    formats = items(state['formats'], 'formats', 5)
    if len(set(formats)) != len(formats) or set(formats) - {'html','xlsx','docx','pdf','pptx'}:
        raise ValueError('Unknown or repeated format')
    for gap in items(state['gaps'], 'gaps', 50, empty=True): text(gap, 'gap')
    return sources, facts


def calculate(state):
    sources, facts = validate(state); scope = state['scope']; results = {}

    def fact(fid, unit, year=None, low=None, high=None):
        if fid not in facts: raise ValueError('Missing numeric fact ' + str(fid))
        f = facts[fid]
        if f['unit'] != unit or f['year'] != (scope['year'] if year is None else year) or any(f[k] != scope[k] for k in ['geography','boundary']):
            raise ValueError('Incompatible unit, year or market boundary for ' + fid)
        return number(f['value'], fid, minimum=low, maximum=high, optional=True)

    def product(*values):
        result = Decimal(1)
        for value in values:
            if value is None: return None
            result *= value
        return result

    for spec in items(state['calculations'], 'calculations', 50, empty=True):
        cid = text(spec['id'], 'calculation id')
        if not re.fullmatch(r'[a-zA-Z][a-zA-Z0-9_-]{0,63}', cid) or cid in results: raise ValueError('Invalid calculation id')
        kind = spec['type']; refs = []; values = {}; formula = ''; notes = []
        if kind == 'market-size':
            fields(spec, ['id','type','customers','annual_spend','serviceable_share','capture_share'])
            refs = [spec[k] for k in ['customers','annual_spend','serviceable_share','capture_share']]
            n = fact(refs[0], 'customers', low=0)
            spend = fact(refs[1], scope['currency']+'/customer/year', low=0)
            sam = fact(refs[2], 'fraction', low=0, high=1); som = fact(refs[3], 'fraction', low=0, high=1)
            values = {'TAM':product(n,spend),'SAM':product(n,spend,sam),'SOM':product(n,spend,sam,som)}
            formula = 'TAM = customers × annual_spend; SAM = TAM × serviceable_share; SOM = SAM × capture_share'
            notes = [scope['currency']+'/year; annual bottom-up scenario, not verified market size. Missing inputs propagate independently.']
        elif kind == 'growth':
            fields(spec, ['id','type','base','end','base_year','end_year','unit'])
            if type(spec['base_year']) is not int or type(spec['end_year']) is not int or not 0 < spec['end_year']-spec['base_year'] <= 100:
                raise ValueError('Growth needs positive integer year interval')
            refs = [spec['base'],spec['end']]
            base = fact(refs[0], spec['unit'], spec['base_year'], low=0)
            end = fact(refs[1], spec['unit'], spec['end_year'], low=0)
            years = spec['end_year']-spec['base_year']
            with localcontext() as context:
                context.prec = 32
                values = {'CAGR': None if base in (None,0) or end is None else (end/base)**(Decimal(1)/years)-1}
            formula = '(end / base)^(1 / (end_year - base_year)) - 1'
            notes = ['CAGR is a fraction; base <= 0 or missing makes it unavailable, not zero.']
        elif kind == 'concentration':
            fields(spec, ['id','type','shares','coverage','top_n'])
            refs = items(spec['shares'], 'shares', 50)
            if len(refs)!=len(set(refs)) or spec['coverage'] not in ('full','partial') or type(spec['top_n']) is not int or not 1 <= spec['top_n'] <= len(refs):
                raise ValueError('Invalid concentration scope')
            shares = [fact(f, 'fraction', low=0, high=1) for f in refs]
            if any(x is None for x in shares):
                values = {'observed_share':None,'CRn':None,'HHI_10000':None}
                notes = ['Missing shares; no renormalization, no concentration estimate.']
            else:
                total = sum(shares)
                if total > 1 or spec['coverage']=='full' and total != 1: raise ValueError('Share coverage does not match explicit full/partial scope')
                values = {'observed_share':total,'CRn':sum(sorted(shares,reverse=True)[:spec['top_n']]),'HHI_10000':sum(x*x for x in shares)*10000}
                notes = ['Full market coverage.' if spec['coverage']=='full' else 'Partial coverage: CRn and HHI are observed lower bounds; unobserved share is not a single firm.']
            formula = 'CRn = sum of largest n shares; HHI_10000 = sum(share^2) × 10000; no rescaling'
        elif kind == 'weighted-score':
            fields(spec, ['id','type','criteria','alternatives'])
            criteria=indexed(spec['criteria'],'criteria'); alternatives=indexed(spec['alternatives'],'alternatives')
            weights={}
            for key,c in criteria.items():
                fields(c,['id','weight_fact','min','max','direction'])
                weights[key]=fact(c['weight_fact'],'fraction',low=0,high=1);refs.append(c['weight_fact'])
                lo=number(c['min'],'min');hi=number(c['max'],'max')
                if hi<=lo or c['direction'] not in ('benefit','cost'):raise ValueError('Invalid criterion scale/direction')
            if any(v is None for v in weights.values()) or sum(weights.values())!=1:raise ValueError('Explicit known weights must sum to 1')
            for aid,a in alternatives.items():
                fields(a,['id','scores'])
                if set(a['scores'])!=set(criteria):raise ValueError('Missing criterion mapping')
                score=Decimal(0);missing=False
                for key,c in criteria.items():
                    fid=a['scores'][key];refs.append(fid);lo=number(c['min'],'min');hi=number(c['max'],'max');v=fact(fid,'score',low=lo,high=hi)
                    if v is None:missing=True;continue
                    score+=weights[key]*((v-lo)/(hi-lo) if c['direction']=='benefit' else (hi-v)/(hi-lo))*100
                values[aid]=None if missing else score
            notes=['Scores are assumption-dependent, not objective ratings; incomplete alternatives remain unranked. Ties share rank.']
            formula='sum(weight × normalized score) × 100; cost direction reversed, no missing-weight renormalization'
        else: raise ValueError('Unsupported calculation type')
        results[cid]={'type':kind,'values':values,'formula':formula,'fact_ids':list(dict.fromkeys(refs)),'notes':notes}
        if kind=='weighted-score':
            known=sorted([v for v in values.values() if v is not None],reverse=True)
            results[cid]['ranks']={k:None if v is None else known.index(v)+1 for k,v in values.items()}
    findings=indexed(state['findings'],'findings')
    pattern=re.compile(r'\{\{calc:([A-Za-z0-9_-]+):([A-Za-z0-9_-]+)\}\}')
    rendered=[]
    for f in findings.values():
        fields(f,['id','kind','text','fact_ids','limitations','next_action'])
        if f['kind'] not in ('fact','inference','assumption','recommendation'):raise ValueError('Unknown finding kind')
        for fid in items(f['fact_ids'],'finding evidence',100):
            if fid not in facts:raise ValueError('Missing finding evidence')
        for k in ['text','limitations','next_action']:text(f[k],k)
        used=[]
        def replace(match):
            cid,key=match.groups()
            if cid not in results or key not in results[cid]['values']:raise ValueError('Unknown calculation placeholder')
            used.extend(results[cid]['fact_ids']);v=results[cid]['values'][key]
            return 'N/A' if v is None else format(v,'.8f').rstrip('0').rstrip('.')
        resolved=pattern.sub(replace,f['text'])
        if '{{' in resolved or '}}' in resolved:raise ValueError('Unresolved calculation placeholder')
        if set(used)-set(f['fact_ids']):raise ValueError('Finding omits calculation input evidence')
        rendered.append(dict(f,text=resolved))
    return {'calculator_version':VERSION,'calculations':results,'findings':rendered,
            'source_hashes':{k:hashlib.sha256(v['content'].encode()).hexdigest() for k,v in sources.items()},
            'scope':scope,'mode':state['mode'],'source_authenticity':'not mechanically verified',
            'online_moss':'not run by this local helper'}


def main():
    parser=argparse.ArgumentParser();sub=parser.add_subparsers(dest='command',required=True)
    freeze=sub.add_parser('freeze');freeze.add_argument('--state',required=True);freeze.add_argument('--out',required=True)
    deliver=sub.add_parser('deliver');deliver.add_argument('--frozen',required=True);deliver.add_argument('--out',required=True);deliver.add_argument('--soffice')
    verify=sub.add_parser('verify');verify.add_argument('--delivery',required=True);verify.add_argument('--state',required=True)
    args=parser.parse_args()
    if args.command=='freeze':
        state=read_json(args.state);result=calculate(state);payload={'schema_version':1,'state':state,'result':result}
        frozen=dict(payload,content_sha256=digest(payload));out=output_folder(args.out)
        save_json(out/'research_state.json',state);save_json(out/'frozen.json',frozen)
        print(dumps({'status':'frozen','content_sha256':frozen['content_sha256'],'path':str(out/'frozen.json')}))
    elif args.command=='deliver':
        from delivery import deliver_frozen
        print(dumps(deliver_frozen(Path(args.frozen),args.out,args.soffice)))
    else:
        from delivery import verify_delivery
        print(dumps(verify_delivery(Path(args.delivery),read_json(args.state))))


if __name__=='__main__':
    try: main()
    except (ValueError,KeyError,TypeError,OSError) as error:
        raise SystemExit('Research input/delivery rejected: '+str(error)) from error
