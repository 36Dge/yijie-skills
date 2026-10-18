"""Original small OOXML report writers. No upstream templates, Office shim or SDK.

Editable text only; long material is paginated, never silently truncated.
"""
import zipfile
from xml.sax.saxutils import escape

W='http://schemas.openxmlformats.org/wordprocessingml/2006/main'
A='http://schemas.openxmlformats.org/drawingml/2006/main'
P='http://schemas.openxmlformats.org/presentationml/2006/main'
R='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
PKG='http://schemas.openxmlformats.org/package/2006/relationships'


def xml(text):
    if any(ord(c)<32 and c not in '\n\t\r' for c in text): raise ValueError('Invalid document text')
    return escape(text)


def rels(rows):
    return '<Relationships xmlns="'+PKG+'">'+''.join(f'<Relationship Id="rId{i}" Type="{R}/{kind}" Target="{target}"/>' for i,kind,target in rows)+'</Relationships>'


def types(rows):
    return '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/>'+''.join(f'<Override PartName="/{part}" ContentType="application/vnd.openxmlformats-officedocument.{kind}+xml"/>' for part,kind in rows)+'</Types>'


def docx(path, title, blocks, identity):
    def para(value,style='Normal'):
        runs='<w:r><w:br/></w:r>'.join('<w:r><w:t xml:space="preserve">'+xml(line)+'</w:t></w:r>' for line in value.split('\n'))
        return '<w:p><w:pPr><w:pStyle w:val="'+style+'"/></w:pPr>'+runs+'</w:p>'
    body=para(title,'Title')+para('易界行业研究 · 用户资料模式' if identity['mode']=='offline' else '易界行业研究 · 已保留连接器证据')
    body+=para('内容版本 '+identity['revision']+'  冻结摘要 '+identity['content_sha256'])
    for block in blocks:
        body+=para(block['title'],'Heading1')
        body+=''.join(para(line) for line in block['lines'])
    styles=f'<w:styles xmlns:w="{W}"><w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:eastAsia="Heiti SC"/><w:sz w:val="22"/><w:color w:val="000000"/></w:rPr></w:rPrDefault><w:pPrDefault><w:pPr><w:spacing w:after="160" w:line="300" w:lineRule="auto"/></w:pPr></w:pPrDefault></w:docDefaults>'
    for name,size in [('Normal',22),('Title',40),('Heading1',28)]:
        styles+=f'<w:style w:type="paragraph" w:styleId="{name}"><w:name w:val="{name}"/><w:pPr><w:widowControl/>' + ('<w:keepNext/>' if name!='Normal' else '') + f'</w:pPr><w:rPr><w:sz w:val="{size}"/><w:color w:val="000000"/>' + ('<w:b/>' if name!='Normal' else '')+'</w:rPr></w:style>'
    styles+='</w:styles>'
    with zipfile.ZipFile(path,'x',compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml',types([('word/document.xml','wordprocessingml.document.main'),('word/styles.xml','wordprocessingml.styles')]))
        z.writestr('_rels/.rels',rels([(1,'officeDocument','word/document.xml')]))
        z.writestr('word/_rels/document.xml.rels',rels([(1,'styles','styles.xml')]))
        z.writestr('word/styles.xml',styles)
        z.writestr('word/document.xml',f'<w:document xmlns:w="{W}"><w:body>'+body+'<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1134" w:right="1134" w:bottom="1134" w:left="1134"/></w:sectPr></w:body></w:document>')


def wrap(value, units=70):
    rows=[];line='';width=0
    for c in value:
        size=2 if ord(c)>127 else 1
        if c=='\n' or width+size>units:
            rows.append(line);line='';width=0
        if c!='\n':line+=c;width+=size
    if line:rows.append(line)
    return rows or ['']


def pptx(path,title,blocks,identity):
    pages=[(title,['易界行业研究', '内容版本 '+identity['revision'], '用户资料离线模式' if identity['mode']=='offline' else '已保留的连接器证据', '冻结摘要 '+identity['content_sha256']])]
    for block in blocks:
        lines=[]
        for line in block['lines']:lines.extend(wrap(line))
        for offset in range(0,len(lines),9):
            pages.append((block['title']+('（续）' if offset else ''),lines[offset:offset+9]))
    def shape(sid,value,x,y,cx,cy,size,bold=False):
        paras=''.join('<a:p><a:pPr marL="0" indent="0"><a:lnSpc><a:spcPct val="115000"/></a:lnSpc></a:pPr><a:r><a:rPr lang="zh-CN" sz="'+str(size)+'" b="'+('1' if bold else '0')+'"><a:solidFill><a:srgbClr val="25282B"/></a:solidFill><a:latin typeface="Arial"/><a:ea typeface="Heiti SC"/></a:rPr><a:t>'+xml(line)+'</a:t></a:r></a:p>' for line in value)
        return f'<p:sp><p:nvSpPr><p:cNvPr id="{sid}" name="Text {sid}"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr><p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr><p:txBody><a:bodyPr wrap="square" lIns="0" rIns="0" tIns="0" bIns="0"/><a:lstStyle/>'+paras+'</p:txBody></p:sp>'
    group='<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>'
    content=[('ppt/presentation.xml','presentationml.presentation.main')];presrels=[];slideids=[]
    with zipfile.ZipFile(path,'x',compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr('_rels/.rels',rels([(1,'officeDocument','ppt/presentation.xml')]))
        for i,(heading,lines) in enumerate(pages,1):
            if len(wrap(heading,64))>2:raise ValueError('Slide heading too long')
            content.append((f'ppt/slides/slide{i}.xml','presentationml.slide'))
            presrels.append((i,'slide',f'slides/slide{i}.xml'));slideids.append(f'<p:sldId id="{255+i}" r:id="rId{i}"/>')
            textboxes=shape(2,wrap(heading,64),640000,420000,10900000,1150000,3000,True)
            textboxes+=shape(3,lines,640000,1780000,10900000,4300000,2200)
            textboxes+=shape(4,[f'{i} / {len(pages)}   '+identity['revision']+'   '+identity['content_sha256'][:16]],640000,6400000,10900000,250000,1000)
            z.writestr(f'ppt/slides/slide{i}.xml',f'<p:sld xmlns:p="{P}" xmlns:a="{A}" xmlns:r="{R}"><p:cSld><p:bg><p:bgPr><a:solidFill><a:srgbClr val="FFFFFF"/></a:solidFill><a:effectLst/></p:bgPr></p:bg><p:spTree>'+group+textboxes+'</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>')
        z.writestr('ppt/_rels/presentation.xml.rels',rels(presrels))
        z.writestr('ppt/presentation.xml',f'<p:presentation xmlns:p="{P}" xmlns:a="{A}" xmlns:r="{R}"><p:sldIdLst>'+''.join(slideids)+'</p:sldIdLst><p:sldSz cx="12192000" cy="6858000"/><p:notesSz cx="6858000" cy="9144000"/></p:presentation>')
        z.writestr('[Content_Types].xml',types(content))
    return len(pages)
