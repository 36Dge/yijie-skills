"""YiJie self-contained OOXML writer, adapted from the reviewed industry-research helper."""
from decimal import Decimal
from xml.sax.saxutils import escape, quoteattr
import zipfile
NS='http://schemas.openxmlformats.org/spreadsheetml/2006/main'
REL='http://schemas.openxmlformats.org/officeDocument/2006/relationships'


def column(index):
    result=''
    while index:
        index,remainder=divmod(index-1,26);result=chr(65+remainder)+result
    return result


def write_xlsx(path,sheets):
    types=['<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>','<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>']
    workbook=[];links=[]
    with zipfile.ZipFile(path,'x',compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr('_rels/.rels','<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="'+REL+'/officeDocument" Target="xl/workbook.xml"/></Relationships>')
        for index,(name,rows) in enumerate(sheets,1):
            types.append(f'<Override PartName="/xl/worksheets/sheet{index}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>')
            workbook.append(f'<sheet name={quoteattr(name)} sheetId="{index}" r:id="rId{index}"/>')
            links.append(f'<Relationship Id="rId{index}" Type="{REL}/worksheet" Target="worksheets/sheet{index}.xml"/>')
            count=max(map(len,rows));widths=[38 if i==0 else 23 for i in range(count)]
            if name in ('Summary','Inputs'):widths[1]=62
            if name=='Sources':widths=[38,24,52,22,70]
            body=[]
            for r,row in enumerate(rows,1):
                cells=[];height=30 if r==1 else 25
                for c,value in enumerate(row,1):
                    ref=column(c)+str(r);style=1 if r==1 else 0
                    if isinstance(value,tuple):
                        formula,cache=value;cache='N/A' if cache is None else cache
                        kind=' t="str"' if isinstance(cache,str) else ''
                        style=2 if name=='Summary' or '!' not in formula else 4
                        if name in ('Summary','DCF') and ref=='B2':style=5
                        payload=f'<f>{escape(formula)}</f><v>{escape(str(cache))}</v>'
                    elif isinstance(value,(Decimal,int)) and not isinstance(value,bool):
                        kind='';style=3;payload=f'<v>{value}</v>'
                        if name=='Inputs' and c==2 and 2<=r<=7 or name=='Sensitivity' and c<=2 and r>1:style=6
                        if name=='DCF' and c==1 or name=='Inputs' and r in (9,10):style=7
                    else:
                        kind=' t="inlineStr"';content='' if value is None else str(value)
                        if any(ord(char)<32 and char not in '\n\r\t' for char in content):raise ValueError('Invalid cell text')
                        # Wrap long text inside its own cell instead of spilling into other source columns.
                        display_width=sum(2 if ord(char)>127 else 1 for char in content)
                        height=max(height,18*((display_width+widths[c-1]-1)//widths[c-1]+content.count('\n')))
                        payload='<is><t xml:space="preserve">'+escape(content)+'</t></is>'
                    cells.append(f'<c r="{ref}" s="{style}"{kind}>{payload}</c>')
                body.append(f'<row r="{r}" ht="{min(max(height,25),180)}" customHeight="1">'+''.join(cells)+'</row>')
            cols=''.join(f'<col min="{i}" max="{i}" width="{w}" customWidth="1"/>' for i,w in enumerate(widths,1))
            pane='' if name=='Summary' else '<pane ySplit="1" topLeftCell="A2" state="frozen"/>'
            z.writestr(f'xl/worksheets/sheet{index}.xml',f'<worksheet xmlns="{NS}"><sheetViews><sheetView workbookViewId="0" showGridLines="0">{pane}</sheetView></sheetViews><cols>{cols}</cols><sheetData>'+''.join(body)+'</sheetData></worksheet>')
        links.append(f'<Relationship Id="rIdStyles" Type="{REL}/styles" Target="styles.xml"/>')
        z.writestr('xl/_rels/workbook.xml.rels','<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'+''.join(links)+'</Relationships>')
        z.writestr('xl/workbook.xml',f'<workbook xmlns="{NS}" xmlns:r="{REL}"><sheets>'+''.join(workbook)+'</sheets><calcPr calcId="191029" fullCalcOnLoad="1"/></workbook>')
        z.writestr('[Content_Types].xml','<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/>'+''.join(types)+'</Types>')
        fonts=''.join(f'<font><sz val="11"/><name val="Arial"/><color rgb="{color}"/>{bold}</font>' for color,bold in [('FF25282B',''),('FFFFFFFF','<b/>'),('FF2453A6',''),('FF2D7050','')])
        formats=[(164,'#,##0.00;(#,##0.00);"-"'),(165,'0.000%'),(166,'0.0000')]
        numfmts=''.join(f'<numFmt numFmtId="{i}" formatCode={quoteattr(code)}/>' for i,code in formats)
        xfs=[]
        for num,font,fill in [(0,0,0),(0,1,2),(164,0,0),(164,2,0),(164,3,0),(165,0,0),(166,2,0),(3,2,0)]:
            xfs.append(f'<xf numFmtId="{num}" fontId="{font}" fillId="{fill}" borderId="0" xfId="0" applyNumberFormat="1" applyFont="1" applyFill="1" applyAlignment="1"><alignment vertical="center" wrapText="1"/></xf>')
        z.writestr('xl/styles.xml',f'<styleSheet xmlns="{NS}"><numFmts count="3">{numfmts}</numFmts><fonts count="4">{fonts}</fonts><fills count="3"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill><fill><patternFill patternType="solid"><fgColor rgb="FF25282B"/><bgColor indexed="64"/></patternFill></fill></fills><borders count="1"><border/></borders><cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs><cellXfs count="8">'+''.join(xfs)+'</cellXfs><cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles></styleSheet>')
