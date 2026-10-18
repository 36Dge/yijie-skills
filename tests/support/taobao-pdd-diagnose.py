"""Normal data regressions only. No process/permission/runtime/attack fixtures."""
import copy
import csv
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, tostring

PACKAGE = Path(sys.argv.pop(1)).resolve()
sys.path.insert(0, str(PACKAGE/'scripts'))
import diagnose as d
PROFILE = json.loads((PACKAGE/'profile.json').read_text())


def write_xlsx(path, rows, percent_cols=(), dates=False, epoch1904=False):
    ns='http://schemas.openxmlformats.org/spreadsheetml/2006/main'
    sheet=Element('worksheet', xmlns=ns); data=SubElement(sheet,'sheetData')
    for n,row in enumerate(rows,1):
        rr=SubElement(data,'row',r=str(n))
        for col,val in enumerate(row):
            name=chr(65+col)+str(n)
            if n>1 and col in percent_cols:
                c=SubElement(rr,'c',r=name,s='1');SubElement(c,'v').text=str(val)
            elif n>1 and dates and col==0:
                from datetime import date
                dd=date.fromisoformat(val)
                base=date(1904,1,1) if epoch1904 else date(1899,12,30)
                c=SubElement(rr,'c',r=name,s='2');SubElement(c,'v').text=str((dd-base).days)
            else:
                c=SubElement(rr,'c',r=name,t='inlineStr');SubElement(SubElement(c,'is'),'t').text=str(val)
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml','<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/><Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/></Types>')
        z.writestr('_rels/.rels','<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>')
        z.writestr('xl/workbook.xml',f'<workbook xmlns="{ns}" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><workbookPr date1904="{int(epoch1904)}"/><sheets><sheet name="数据" sheetId="1" r:id="rId1"/></sheets></workbook>')
        z.writestr('xl/_rels/workbook.xml.rels','<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Target="worksheets/sheet1.xml" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet"/><Relationship Id="rId2" Target="styles.xml" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles"/></Relationships>')
        z.writestr('xl/styles.xml',f'<styleSheet xmlns="{ns}"><fonts count="1"><font><sz val="11"/><name val="Calibri"/></font></fonts><fills count="2"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill></fills><borders count="1"><border/></borders><cellStyleXfs count="1"><xf numFmtId="0"/></cellStyleXfs><cellXfs count="3"><xf numFmtId="0"/><xf numFmtId="10"/><xf numFmtId="14"/></cellXfs></styleSheet>')
        z.writestr('xl/worksheets/sheet1.xml',tostring(sheet,encoding='utf-8'))


class Diagnosis(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name)
        self.config=json.loads((PACKAGE/'examples/manifest.json').read_text())
        self.rows=[['日期','计划','消耗','归因成交额','曝光','点击'],['2026-10-01','A','100','200','1000','12'],['2026-10-02','A','0','0','0','0']]
        self.csv('ads.csv',self.rows)
    def csv(self,name,rows):
        with (self.base/name).open('w',newline='',encoding='utf-8-sig') as h:csv.writer(h).writerows(rows)
    def run_config(self,c=None):
        from decimal import localcontext
        with localcontext() as ctx:
            ctx.prec=40
            return d.analyze(c or self.config,self.base,PROFILE)
    def group(self,c=None):return self.run_config(c)['groups'][0]
    def test_exact_finance_and_zero(self):
        g=self.group();self.assertEqual(g['finance']['contribution'],'-20');self.assertEqual(g['finance']['loss_per_ad_yuan'],'0.2');self.assertEqual(g['finance']['breakeven_roi'],'2.5')
        self.assertEqual(g['rows'][1]['values']['spend'],'0');self.assertEqual(g['derived']['ad_roi']['value'],'2')
        self.assertEqual(g['finance']['mode'],'scenario');self.assertEqual(g['aggregates']['spend']['total'],'100')
    def test_missing_revenue_never_zero_or_profit(self):
        self.rows[1][3]='';self.csv('ads.csv',self.rows);g=self.group()
        self.assertIsNone(g['aggregates']['ad_gmv']['total']);self.assertEqual(g['aggregates']['ad_gmv']['known_subtotal'],'0')
        self.assertIsNone(g['derived']['ad_roi']['value']);self.assertIsNone(g['finance']['contribution'])
        self.assertEqual(self.run_config()['status'],'partial')
    def test_no_margin_defaults_and_explicit_zero(self):
        del self.config['gross_margin'];self.assertIsNone(self.group()['finance']['contribution'])
        self.config['gross_margin']={'value':'0','unit':'fraction','mode':'confirmed','source':'provided','basis':self.config['datasets'][0]['basis']}
        f=self.group()['finance'];self.assertEqual(f['contribution'],'-100');self.assertEqual(f['loss_per_ad_yuan'],'1');self.assertIsNone(f['breakeven_roi'])
    def test_decimal_currency(self):
        self.rows[1][2:4]=['0.1','0.2'];self.rows[2][2:4]=['0.2','0.4'];self.csv('ads.csv',self.rows)
        self.assertEqual(self.group()['aggregates']['spend']['total'],'0.3');self.assertEqual(self.group()['finance']['contribution'],'-0.06')
    def test_csv_xlsx_equivalence_and_dates(self):
        a=self.group()
        for epoch in (False,True):
            write_xlsx(self.base/'ads.xlsx',self.rows,dates=True,epoch1904=epoch)
            self.config['datasets'][0]['path']='ads.xlsx';b=self.group()
            for key in ('aggregates','derived','finance'):self.assertEqual(a[key],b[key])
            self.assertEqual([r['date'] for r in a['rows']],[r['date'] for r in b['rows']])
    def test_percent_text_numeric_and_excel(self):
        self.assertEqual(d.number_text(d.numeric(d.cell('1.2%'),'percent','reply_rate')[0]),'0.012')
        self.assertEqual(d.number_text(d.numeric(d.cell('1.2'),'percent','reply_rate')[0]),'0.012')
        self.assertEqual(d.number_text(d.numeric(d.cell('0.012'),'fraction','reply_rate')[0]),'0.012')
        self.assertEqual(d.number_text(d.numeric(d.cell('0.012','percent'),'percent','reply_rate')[0]),'0.012')
        self.assertIsNone(d.numeric(d.cell('1.2'),'fraction','reply_rate')[0]);self.assertIsNone(d.numeric(d.cell('1.2%'),'fraction','reply_rate')[0])
        rows=[['日期','回复率'],['2026-10-01','1.2%']];self.csv('service.csv',rows)
        ds=self.config['datasets'][0];ds.update(path='service.csv',kind='service',grain='day',columns={'date':{'header':'日期'},'reply_rate':{'header':'回复率','unit':'percent'}})
        a=self.group();write_xlsx(self.base/'service.xlsx',[rows[0],['2026-10-01','0.012']],percent_cols=(1,))
        ds['path']='service.xlsx';b=self.group();self.assertEqual(a['rows'][0]['values'],b['rows'][0]['values']);self.assertIsNone(b['aggregates']['reply_rate']['total'])
    def test_date_window_and_unknown_date(self):
        self.rows += [['2026-09-30','B','500','1000','1','1'],['','C','800','1600','1','1']];self.csv('ads.csv',self.rows)
        g=self.group();self.assertEqual(g['aggregates']['spend']['known_subtotal'],'100');self.assertIsNone(g['aggregates']['spend']['total'])
        self.assertEqual(len(g['rows']),2);self.assertEqual(len(g['excluded']),1)
    def test_platform_and_store_unconfirmed(self):
        self.config['datasets'][0]['platform']='unknown';r=self.run_config();self.assertEqual(r['status'],'needs_input');self.assertEqual(r['groups'],[])
        self.config['datasets'][0]['platform']=PROFILE['platforms'][0];self.config['datasets'][0]['store']='another';self.assertEqual(self.run_config()['status'],'needs_input')
    def test_foreign_row_isolated(self):
        self.rows[0]+= ['平台'];self.rows[1]+= ['another'];self.rows[2]+=[PROFILE['platforms'][0]];self.csv('ads.csv',self.rows)
        self.config['datasets'][0]['columns']['platform']={'header':'平台'}
        g=self.group();self.assertEqual(len(g['rows']),1);self.assertEqual(g['aggregates']['spend']['known_subtotal'],'0');self.assertIsNone(g['aggregates']['spend']['total'])
    def test_duplicate_equivalent_and_conflict(self):
        self.rows.append(self.rows[1][:]);self.csv('ads.csv',self.rows)
        g=self.group();self.assertEqual(g['aggregates']['spend']['total'],'100');self.assertEqual(len(g['duplicate_sources']),1)
        self.rows[-1][2]='101';self.csv('ads.csv',self.rows);g=self.group()
        self.assertEqual(len(g['rows']),1);self.assertIsNone(g['aggregates']['spend']['total']);self.assertEqual(g['excluded'][0]['reason'],'conflicting_duplicate')
    def test_csv_xlsx_duplicate_sources(self):
        write_xlsx(self.base/'ads.xlsx',self.rows)
        ds=copy.deepcopy(self.config['datasets'][0]);ds.update(id='ads-xlsx',path='ads.xlsx');self.config['datasets'].append(ds)
        g=self.group();self.assertEqual(g['aggregates']['spend']['total'],'100');self.assertEqual(len(g['duplicate_sources']),2)
    def test_distinct_basis_never_combined(self):
        del self.config['gross_margin'];self.csv('other.csv',self.rows)
        ds=copy.deepcopy(self.config['datasets'][0]);ds.update(id='other',path='other.csv',basis='different attribution');self.config['datasets'].append(ds)
        r=self.run_config();self.assertEqual(len(r['groups']),2);self.assertEqual([g['aggregates']['spend']['total'] for g in r['groups']],['100','100'])
    def test_daily_people_not_period_unique(self):
        self.csv('daily.csv',[['日期','访客','买家'],['2026-10-01','10','0'],['2026-10-02','10','2']])
        ds=self.config['datasets'][0];ds.update(path='daily.csv',kind='overview',grain='day',columns={'date':{'header':'日期'},'visitors':{'header':'访客','unit':'count'},'buyers':{'header':'买家','unit':'count'}})
        g=self.group();self.assertIn('not period-unique',g['aggregates']['visitors']['meaning']);self.assertEqual(g['derived']['buyers_per_visitor_daily_basis']['value'],'0.1')
    def test_scores_separate_units_latest_actual_date(self):
        systems = [('店铺领航员','percent','80','0','100'),('消费者服务体验分','points','4.5','0','5'),('店铺综合体验星级','stars','4','3','5')] if PROFILE['platforms']==['pdd'] else [('真实体验分','points','4.5','0','5'),('DSR','points','4','0','5')]
        base=copy.deepcopy(self.config['datasets'][0]);self.config['datasets']=[]
        for i,(system,unit,value,lo,hi) in enumerate(systems):
            name=f'score{i}.csv';self.csv(name,[['日期','对象','体系','分数'],['2026-10-01','店铺',system,value]])
            ds=copy.deepcopy(base);ds.update(id=str(i),path=name,kind='scores',columns={'date':{'header':'日期'},'id':{'header':'对象'},'system':{'header':'体系'},'score':{'header':'分数','unit':unit}},score_scales={system:{'min':lo,'max':hi,'source':'用户测试量表'}});self.config['datasets'].append(ds)
        r=self.run_config();snaps=[s for g in r['groups'] for s in g['latest_score_snapshots']]
        self.assertEqual(len(snaps),len(systems));self.assertTrue(all(s['date']=='2026-10-01' for s in snaps));self.assertTrue(all(g['aggregates']['score']['total'] is None for g in r['groups']))
        if PROFILE['platforms']==['pdd']:self.assertEqual(snaps[0]['values']['score'],'0.8')
    def test_explicit_mapping_and_no_sample_fallback(self):
        self.config['datasets']=[]
        with self.assertRaisesRegex(ValueError,'no sample fallback'):self.run_config()
    def test_valid_formula_value_requires_export(self):
        self.assertEqual(d.numeric(d.cell('2','formula'),'CNY','gmv'),(None,'export_values_required'))
    def test_missing_column_and_duplicate_header_not_guessed(self):
        del self.config['datasets'][0]['columns']['ad_gmv']
        self.assertIsNone(self.group()['finance']['contribution'])
        self.config['datasets'][0]['columns']['spend']['header']='不存在的列'
        with self.assertRaisesRegex(ValueError,'missing or duplicated'):self.run_config()
        self.config['datasets'][0]['columns']['spend']['header']='消耗'
        self.rows[0][3]='消耗';self.csv('ads.csv',self.rows)
        with self.assertRaisesRegex(ValueError,'missing or duplicated'):self.run_config()
    def test_all_zero_ads_preserved_without_zero_division(self):
        self.csv('ads.csv',[self.rows[0],self.rows[2]])
        g=self.group();self.assertEqual(g['aggregates']['spend']['total'],'0');self.assertEqual(g['finance']['contribution'],'0')
        self.assertIsNone(g['derived']['ad_roi']['value']);self.assertIsNone(g['finance']['loss_per_ad_yuan'])
    def test_cli_files_receipt_and_version_preservation(self):
        manifest=self.base/'manifest.json';manifest.write_text(json.dumps(self.config,ensure_ascii=False))
        out=self.base/'report-v1';cmd=[sys.executable,'-B',str(PACKAGE/'scripts/diagnose.py'),'--input',str(manifest),'--out',str(out)]
        result=subprocess.run(cmd,capture_output=True,text=True);self.assertEqual(result.returncode,0,result.stderr)
        receipt=json.loads((out/'receipt.json').read_text());before={p.name:p.read_bytes() for p in out.iterdir()}
        for f in receipt['files']:self.assertEqual(d.digest((out/f['path']).read_bytes()),f['sha256'])
        self.assertIn('10 结论与交付边界',(out/'report.html').read_text());self.assertNotIn('https://',(out/'report.html').read_text())
        second=subprocess.run(cmd,capture_output=True,text=True);self.assertEqual(second.returncode,2);self.assertIn('already exists',second.stderr)
        self.assertEqual(before,{p.name:p.read_bytes() for p in out.iterdir()})
        cmd[-1]=str(self.base/'report-v2');self.assertEqual(subprocess.run(cmd,capture_output=True).returncode,0)

if __name__=='__main__':unittest.main()
