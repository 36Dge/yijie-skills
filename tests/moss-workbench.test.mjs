import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import path from "node:path";
import test from "node:test";

const root = path.resolve("plugins/yijie-desktop-skills/experts/moss-industry-research/versions/0.1.1/moss-workbench");
const setup = `import sys,copy,json,tempfile\nfrom pathlib import Path\nfrom decimal import Decimal\nsys.dont_write_bytecode=True\nsys.path.insert(0,${JSON.stringify(root + "/scripts")})\nfrom research import calculate,digest\nfrom common import read_json,save_json\nfrom delivery import deliver_frozen,verify_delivery\ns=read_json(${JSON.stringify(root + "/examples/input.json")})\ndef setfact(state,key,value,status=None):\n f=next(f for f in state['facts'] if f['id']==key);f['value']=value\n if status:f['status']=status\ndef rejected(state):\n try:calculate(state)\n except ValueError:return\n raise AssertionError('invalid ordinary data accepted')\n`;

function check(code) {
  assert.equal(execFileSync("python3", ["-B", "-c", setup + code + "\nprint('PASS')\n"], { encoding: "utf8" }).trim(), "PASS");
}

test("MOSS local market size, annual growth, concentration and cost-direction scores have independent answers", () => check(`
r=calculate(s)['calculations']
assert r['size']['values']=={'TAM':Decimal(12000000),'SAM':Decimal(4800000),'SOM':Decimal(480000)}
assert r['low']['values']['SOM']==240000 and r['high']['values']['SOM']==720000
assert abs(r['growth']['values']['CAGR']-Decimal('.1'))<Decimal('1e-25')
assert r['concentration']['values']=={'observed_share':Decimal(1),'CRn':Decimal('.7'),'HHI_10000':Decimal(3000)}
assert r['priority']['values']=={'a':Decimal(76),'b':Decimal(68),'c':None}
assert r['priority']['ranks']=={'a':1,'b':2,'c':None}
`));

test("MOSS missing market input propagates per metric while explicit zero stays zero", () => check(`
setfact(s,'capture',None,'unknown');v=calculate(s)['calculations']['size']['values']
assert v=={'TAM':Decimal(12000000),'SAM':Decimal(4800000),'SOM':None}
setfact(s,'capture','0','assumption');assert calculate(s)['calculations']['size']['values']['SOM']==0
setfact(s,'base','0');assert calculate(s)['calculations']['growth']['values']['CAGR'] is None
setfact(s,'base','10000000');setfact(s,'end','0');assert calculate(s)['calculations']['growth']['values']['CAGR']==-1
`));

test("MOSS partial market is a lower bound without normalizing unknown firms", () => check(`
c=next(c for c in s['calculations'] if c['id']=='concentration');c['coverage']='partial';c['shares']=['share_a','share_b']
r=calculate(s)['calculations']['concentration'];assert r['values']=={'observed_share':Decimal('.7'),'CRn':Decimal('.7'),'HHI_10000':Decimal(2500)}
assert 'lower bounds' in r['notes'][0]
c['coverage']='full';rejected(s)
`));

test("MOSS weights, unit/year/boundary, source dates and literal citations fail clearly on ordinary inconsistent data", () => check(`
for key,value in [('unit','CNY/customer/month'),('year',2024),('boundary','different scope')]:
 t=copy.deepcopy(s);next(f for f in t['facts'] if f['id']=='spend')[key]=value;rejected(t)
t=copy.deepcopy(s);setfact(t,'weight_demand','.8');rejected(t)
t=copy.deepcopy(s);t['sources'][0]['published_on']='2026-10-18';rejected(t)
t=copy.deepcopy(s);t['facts'][0]['quote']='not in source';rejected(t)
t=copy.deepcopy(s);t['findings'][0]['fact_ids']=['customers'];rejected(t)
`));

test("MOSS tied alternatives share rank and missing criteria never get imputed", () => check(`
setfact(s,'b_demand','8');setfact(s,'b_cost','3');r=calculate(s)['calculations']['priority']
assert r['ranks']=={'a':1,'b':1,'c':None}
setfact(s,'a_cost',None,'unknown');assert calculate(s)['calculations']['priority']['values']['a'] is None
`));

test("MOSS four dependency-free formats share one frozen version and revised research invalidates the old delivery", () => check(`
import zipfile,xml.etree.ElementTree as ET
s['formats']=['html','xlsx','docx','pptx']
payload={'schema_version':1,'state':s,'result':calculate(s)};frozen=dict(payload,content_sha256=digest(payload))
with tempfile.TemporaryDirectory() as temp:
 p=Path(temp);save_json(p/'frozen.json',frozen)
 r=deliver_frozen(p/'frozen.json',p/'v1');assert set(r['formats'])==set(s['formats'])
 assert verify_delivery(p/'v1',s)['status']=='verified'
 for ext in ['xlsx','docx','pptx']:
  with zipfile.ZipFile(p/'v1'/('research.'+ext)) as archive:
   for name in archive.namelist():
    if name.endswith('.xml') or name.endswith('.rels'):ET.fromstring(archive.read(name))
 revised=copy.deepcopy(s);revised['revision']='v2';setfact(revised,'capture','.2')
 try:verify_delivery(p/'v1',revised)
 except ValueError as error:assert 'stale' in str(error)
 else:raise AssertionError('stale delivery accepted')
 try:deliver_frozen(p/'frozen.json',p/'v1')
 except FileExistsError:pass
 else:raise AssertionError('existing outputs overwritten')
`));

test("MOSS missing PDF dependency fails before producing a claimed output", () => check(`
payload={'schema_version':1,'state':s,'result':calculate(s)};frozen=dict(payload,content_sha256=digest(payload))
with tempfile.TemporaryDirectory() as temp:
 p=Path(temp);save_json(p/'frozen.json',frozen)
 try:deliver_frozen(p/'frozen.json',p/'out')
 except ValueError as error:assert 'LibreOffice' in str(error)
 else:raise AssertionError('PDF dependency falsely satisfied')
 assert not (p/'out').exists()
`));

test("MOSS PPTX has a complete normal Office presentation, master, layout and theme graph", () => check(`
import zipfile,posixpath,xml.etree.ElementTree as ET
from office import pptx,P,R,PKG
with tempfile.TemporaryDirectory() as temp:
 path=Path(temp)/'report.pptx'
 count=pptx(path,'合成行业报告',[{'title':'来源','lines':['保留普通资料与未知值']}],{'mode':'offline','revision':'v1','content_sha256':'a'*64})
 with zipfile.ZipFile(path) as z:
  names=set(z.namelist())
  for name in names:
   if name.endswith('.rels'):
    base='' if name=='_rels/.rels' else posixpath.dirname(posixpath.dirname(name))
    for rel in ET.fromstring(z.read(name)):
     assert rel.get('TargetMode') is None
     assert posixpath.normpath(posixpath.join(base,rel.get('Target'))) in names
  pres=ET.fromstring(z.read('ppt/presentation.xml'))
  assert len(pres.find('{'+P+'}sldMasterIdLst'))==1
  assert len(pres.find('{'+P+'}sldIdLst'))==count
  for i in range(1,count+1):
   rel=ET.fromstring(z.read('ppt/slides/_rels/slide'+str(i)+'.xml.rels'))[0]
   assert rel.get('Type')==R+'/slideLayout'
  master=ET.fromstring(z.read('ppt/slideMasters/_rels/slideMaster1.xml.rels'))
  assert {r.get('Type') for r in master}=={R+'/slideLayout',R+'/theme'}
  layout=ET.fromstring(z.read('ppt/slideLayouts/_rels/slideLayout1.xml.rels'))[0]
  assert layout.get('Type')==R+'/slideMaster'
  assert 'ppt/presProps.xml' in names
`));
