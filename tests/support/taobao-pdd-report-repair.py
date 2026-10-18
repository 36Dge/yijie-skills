import sys,json,csv,tempfile,unittest
from pathlib import Path
from html.parser import HTMLParser
package=Path(sys.argv.pop(1)).resolve();sys.path.insert(0,str(package/'scripts'))
expected_version=sys.argv.pop(1) if len(sys.argv)>1 else '0.1.1'
import diagnose as d
profile=json.loads((package/'profile.json').read_text())
class TableRows(HTMLParser):
 def __init__(self,body):
  super().__init__(convert_charrefs=True);self.rows=[];self.row=[];self.cell=None;self.feed(body)
 def handle_starttag(self,tag,attrs):
  if tag=='tr':self.row=[]
  elif tag=='td':self.cell=''
 def handle_data(self,data):
  if self.cell is not None:self.cell+=data
 def handle_endtag(self,tag):
  if tag=='td':self.row.append(self.cell);self.cell=None
  elif tag=='tr' and self.row:self.rows.append(self.row)
class ReportRepair(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.base=Path(self.temp.name)
  (self.base/'ads.csv').write_bytes((package/'examples/ads.csv').read_bytes())
  self.config=json.loads((package/'examples/manifest.json').read_text())
 def test_complete_normal_report_has_no_false_gap(self):
  report=d.analyze(self.config,self.base,profile);body=d.render(report)
  self.assertEqual(report['expert_version'],expected_version);self.assertIsNone(report['groups'][0]['finance']['reason'])
  self.assertIn('无计算缺口',body);self.assertIn('<p>无已检测缺口。</p>',body)
  self.assertNotIn(['计算缺口','待补充'],TableRows(body).rows)
 def test_rates_and_scores_are_visible_and_not_missing_totals(self):
  with (self.base/'service.csv').open('w',newline='') as f:csv.writer(f).writerows([['日期','回复率'],['2026-10-01','1.2%'],['2026-10-02','0%']])
  ds=dict(self.config['datasets'][0]);ds.update(id='service',path='service.csv',kind='service',grain='day',basis='service daily',columns={'date':{'header':'日期'},'reply_rate':{'header':'回复率','unit':'percent'}});self.config['datasets'].append(ds)
  system='店铺领航员' if profile['platforms']==['pdd'] else '真实体验分';unit='percent' if profile['platforms']==['pdd'] else 'points';value='80' if unit=='percent' else '4.5';maximum='100' if unit=='percent' else '5'
  with (self.base/'score.csv').open('w',newline='') as f:csv.writer(f).writerows([['日期','对象','体系','分数'],['2026-10-01','店铺',system,value]])
  ds=dict(self.config['datasets'][0]);ds.update(id='score',path='score.csv',kind='scores',basis='score snapshot',columns={'date':{'header':'日期'},'id':{'header':'对象'},'system':{'header':'体系'},'score':{'header':'分数','unit':unit}},score_scales={system:{'min':'0','max':maximum,'source':'synthetic declared scale'}});self.config['datasets'].append(ds)
  report=d.analyze(self.config,self.base,profile);body=d.render(report)
  self.assertIn('不适用（按行快照）',body);rows=TableRows(body).rows
  self.assertIn(['2026-10-01','store','reply_rate','1.2','%'],[r[:5] for r in rows])
  self.assertIn(['2026-10-02','store','reply_rate','0','%'],[r[:5] for r in rows])
  self.assertIn([system,'店铺','2026-10-01',value,'%' if unit=='percent' else '分'],[r[:5] for r in rows])
  for group in report['groups'][1:]:self.assertTrue(all(v['total'] is None for v in group['aggregates'].values()))
 def test_real_gap_still_visible(self):
  del self.config['gross_margin'];body=d.render(d.analyze(self.config,self.base,profile));self.assertIn('explicit_margin_required',body);self.assertIn('待补充',body)
if __name__=='__main__':unittest.main()
