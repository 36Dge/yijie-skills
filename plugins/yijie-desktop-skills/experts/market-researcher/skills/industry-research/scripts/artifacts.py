"""Own small OOXML writer adapted from YiJie local-quotation; no vendor Office code."""
from decimal import Decimal
from xml.sax.saxutils import escape
import zipfile
NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"

def column(index):
    result = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        result = chr(65 + remainder) + result
    return result


def write_xlsx(path, sheets):
    """Small value/formula workbook writer; tuple(formula, cache) is internal only."""
    content_types = ['<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>', '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>']
    workbook, links = [], []
    with zipfile.ZipFile(path, "x", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("_rels/.rels", '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="'+REL+'/officeDocument" Target="xl/workbook.xml"/></Relationships>')
        for index, (name, rows) in enumerate(sheets, 1):
            content_types.append(f'<Override PartName="/xl/worksheets/sheet{index}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>')
            workbook.append(f'<sheet name="{escape(name)}" sheetId="{index}" r:id="rId{index}"/>')
            links.append(f'<Relationship Id="rId{index}" Type="{REL}/worksheet" Target="worksheets/sheet{index}.xml"/>')
            body = []
            for r, row in enumerate(rows, 1):
                cells = []
                for c, value in enumerate(row, 1):
                    ref = column(c) + str(r)
                    if isinstance(value, tuple):
                        cache = 'N/A / NM' if value[1] is None else str(value[1])
                        kind = ' t="str"' if value[1] is None else ''
                        payload = f'<f>{escape(value[0])}</f><v>{escape(cache)}</v>'
                        cells.append(f'<c r="{ref}" s="2"{kind}>{payload}</c>')
                    elif isinstance(value, (Decimal, int)):
                        cells.append(f'<c r="{ref}" s="3"><v>{value}</v></c>')
                    else:
                        value = "" if value is None else str(value)
                        if any(ord(c) < 32 and c not in "\t\n\r" for c in value):
                            raise ValueError("unsupported XML cell text")
                        cells.append(f'<c r="{ref}" t="inlineStr" s="{1 if r == 1 else 0}"><is><t xml:space="preserve">{escape(value)}</t></is></c>')
                body.append(f'<row r="{r}" ht="24" customHeight="1">'+"".join(cells)+"</row>")
            z.writestr(f"xl/worksheets/sheet{index}.xml", f'<worksheet xmlns="{NS}"><sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" state="frozen"/></sheetView></sheetViews><cols><col min="1" max="20" width="20" customWidth="1"/></cols><sheetData>'+"".join(body)+"</sheetData></worksheet>")
        links.append(f'<Relationship Id="rIdStyles" Type="{REL}/styles" Target="styles.xml"/>')
        z.writestr("xl/_rels/workbook.xml.rels", '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'+"".join(links)+"</Relationships>")
        z.writestr("xl/workbook.xml", f'<workbook xmlns="{NS}" xmlns:r="{REL}"><sheets>'+"".join(workbook)+'<'+ '/sheets><calcPr calcId="191029" fullCalcOnLoad="1"/></workbook>')
        z.writestr("[Content_Types].xml", '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/>'+"".join(content_types)+"</Types>")
        z.writestr("xl/styles.xml", f'<styleSheet xmlns="{NS}"><numFmts count="1"><numFmt numFmtId="164" formatCode="#,##0.######"/></numFmts><fonts count="2"><font><sz val="11"/><name val="Arial"/></font><font><b/><sz val="11"/><color rgb="FFFFFFFF"/><name val="Arial"/></font></fonts><fills count="3"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill><fill><patternFill patternType="solid"><fgColor rgb="FF25282B"/><bgColor indexed="64"/></patternFill></fill></fills><borders count="1"><border/></borders><cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs><cellXfs count="4"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/><xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFont="1" applyFill="1"/><xf numFmtId="4" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/><xf numFmtId="164" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/></cellXfs><cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles></styleSheet>')



def workbook(path, result):
    headers = ['Security', 'Company', 'Revenue', 'EBITDA', 'Net income', 'Market cap', 'Debt', 'Cash', 'Preferred', 'Minority', 'EV', 'EV/Revenue', 'EV/EBITDA', 'P/E', 'EBITDA margin %', 'Status']
    rows = [headers]
    for i, c in enumerate(result['companies'], 2):
        values = c['normalized_millions']
        cells = [c['entity_id'], c['name']] + [Decimal(values[k]) if values[k] is not None else 'N/A' for k in ('revenue','ebitda','net_income','market_cap','debt','cash','preferred','minority')]
        formulas = [
            ('enterprise_value',f'IF(COUNT(F{i}:J{i})=5,F{i}+G{i}-H{i}+I{i}+J{i},"N/A / NM")'),
            ('ev_revenue',f'IF(AND(ISNUMBER(K{i}),ISNUMBER(C{i}),K{i}>0,C{i}>0),K{i}/C{i},"N/A / NM")'),
            ('ev_ebitda',f'IF(AND(ISNUMBER(K{i}),ISNUMBER(D{i}),K{i}>0,D{i}>0),K{i}/D{i},"N/A / NM")'),
            ('pe',f'IF(AND(ISNUMBER(F{i}),ISNUMBER(E{i}),F{i}>0,E{i}>0),F{i}/E{i},"N/A / NM")'),
            ('ebitda_margin_percent',f'IF(AND(ISNUMBER(D{i}),ISNUMBER(C{i}),C{i}>0),D{i}/C{i}*100,"N/A / NM")'),
        ]
        for key, formula in formulas:
            cells.append((formula, c['derived'][key]))
        rows.append(cells+[c['state']])
    evidence = [['Security','Metric','Original value','Scale','Currency','Basis','Period start','Period end','As of','Definition','Source ID','Exact quotation','Issue']]
    for c in result['companies']:
        for name in ('revenue','ebitda','net_income','market_cap','debt','cash','preferred','minority'):
            p=c['metrics'].get(name)
            p=p if isinstance(p,dict) else {}
            evidence.append([c['entity_id'],name]+[str(p.get(k,'')) for k in ('value','scale','currency','basis','period_start','period_end','as_of','definition','source_id','quote')]+[c['issues'].get(name,'')])
    sources=[['ID','Part','Kind','Title','Locator','Published','Retrieved','Content SHA256','Retained text']]
    for k,s in result['sources'].items():
        for start in range(0,len(s['content']),15000):
            sources.append([k,start//15000+1,s['kind'],s['title'],s['locator'],s['published_on'],s['retrieved_on'],s['content_sha256'],s['content'][start:start+15000]])
    notes=[['Field','Value']]+[[k,str(v)] for k,v in result['scope'].items()]+[['units','All normalized amounts are in millions of the stated currency; percentages are percent, multiples are x.'],['source check','Mechanical citation checks are not semantic/source authenticity validation.'],['missing','N/A or NM is excluded, never zero. No automatic forecasts, FX or publishing.']]
    write_xlsx(path,[('Comps',rows),('Evidence',evidence),('Sources',sources),('Method',notes)])
