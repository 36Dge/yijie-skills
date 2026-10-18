"""Bounded value-only CSV/XLSX reader. No extraction, formula evaluation or network."""
import csv
import io
import re
import zipfile
from datetime import datetime, timedelta
from pathlib import PurePosixPath
from xml.etree import ElementTree as ET

MAX_BYTES = 16 * 1024 * 1024
MAX_ROWS = 50000
MAX_COLS = 200
NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
      'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}


def cell(value='', kind='text'):
    return {'raw': value, 'kind': kind}


def xml(z, name):
    return ET.fromstring(z.read(name))


def column_index(ref):
    match = re.fullmatch(r'([A-Z]+)[1-9][0-9]*', ref)
    if not match:
        raise ValueError('XLSX cell address is missing or invalid')
    result = 0
    for letter in match[1]:
        result = result * 26 + ord(letter) - 64
    if result > MAX_COLS:
        raise ValueError('XLSX exceeds 200 columns')
    return result - 1


def read_table(path, sheet=None):
    if path.stat().st_size > MAX_BYTES:
        raise ValueError('Input exceeds 16 MiB')
    suffix = path.suffix.lower()
    if suffix == '.csv':
        if sheet is not None:
            raise ValueError('CSV must not specify a sheet')
        rows = []
        for i, values in enumerate(csv.reader(io.StringIO(path.read_text(encoding='utf-8-sig'))), 1):
            if i > MAX_ROWS or len(values) > MAX_COLS:
                raise ValueError('Table exceeds 50000 rows / 200 columns')
            rows.append((i, [cell(v) for v in values]))
        return 'CSV', rows
    if suffix != '.xlsx':
        raise ValueError('Only UTF-8 CSV and value-only XLSX are supported')
    with zipfile.ZipFile(path) as z:
        infos = z.infolist()
        if len(infos) > 512 or sum(i.file_size for i in infos) > 32 * 1024 * 1024:
            raise ValueError('XLSX exceeds read limits')
        if len({i.filename for i in infos}) != len(infos):
            raise ValueError('XLSX has duplicate entries')
        workbook = xml(z, 'xl/workbook.xml')
        props = workbook.find('s:workbookPr', NS)
        epoch1904 = props is not None and props.get('date1904') in ('1', 'true')
        relationships = {r.get('Id'): r for r in xml(z, 'xl/_rels/workbook.xml.rels')}
        sheets = workbook.findall('s:sheets/s:sheet', NS)
        if sheet is None and len(sheets) != 1:
            raise ValueError('Select an explicit sheet when workbook has multiple sheets')
        selected = [s for s in sheets if sheet is None or s.get('name') == sheet]
        if len(selected) != 1:
            raise ValueError('Sheet not found or ambiguous')
        chosen = selected[0]
        rel = relationships[chosen.get('{'+NS['r']+'}id')]
        if rel.get('TargetMode') == 'External':
            raise ValueError('Worksheet must be embedded')
        target = rel.get('Target', '')
        member = target.lstrip('/') if target.startswith('/') else 'xl/' + target
        if '..' in PurePosixPath(member).parts or member not in z.namelist():
            raise ValueError('Worksheet path is unsupported')
        shared = []
        if 'xl/sharedStrings.xml' in z.namelist():
            shared = [''.join(n.itertext()) for n in xml(z, 'xl/sharedStrings.xml').findall('s:si', NS)]
        styles = []
        if 'xl/styles.xml' in z.namelist():
            style = xml(z, 'xl/styles.xml')
            formats = {int(n.get('numFmtId')): n.get('formatCode', '') for n in style.findall('s:numFmts/s:numFmt', NS)}
            for xf in style.findall('s:cellXfs/s:xf', NS):
                fid = int(xf.get('numFmtId', '0'))
                fmt = formats.get(fid, '')
                bare = re.sub(r'"[^"]*"|\\.|\[[^]]*\]', '', fmt).lower()
                kind = 'number'
                if fid in (9, 10) or '%' in bare:
                    kind = 'percent'
                elif fid in (14, 15, 16, 17, 22) or ('y' in bare and 'd' in bare):
                    kind = 'date'
                styles.append(kind)
        rows = []
        seen_rows = set()
        for row in xml(z, member).findall('s:sheetData/s:row', NS):
            number = int(row.get('r', '0'))
            if number < 1 or number > MAX_ROWS or number in seen_rows:
                raise ValueError('Invalid/duplicate row number or row limit exceeded')
            seen_rows.add(number)
            values, seen_cells = [], set()
            for c in row.findall('s:c', NS):
                address = c.get('r', '')
                idx = column_index(address)
                if int(re.search(r'[0-9]+$', address)[0]) != number or idx in seen_cells:
                    raise ValueError('Invalid/duplicate cell address')
                seen_cells.add(idx)
                while len(values) <= idx:
                    values.append(cell())
                raw = c.findtext('s:v', default='', namespaces=NS)
                typ = c.get('t', 'n')
                if c.find('s:f', NS) is not None:
                    values[idx] = cell(raw, 'formula')
                elif typ == 's':
                    values[idx] = cell(shared[int(raw)])
                elif typ == 'inlineStr':
                    values[idx] = cell(''.join(c.find('s:is', NS).itertext()))
                elif typ in ('e', 'b'):
                    values[idx] = cell(raw, 'unsupported')
                elif typ in ('str', 'd'):
                    values[idx] = cell(raw)
                else:
                    si = int(c.get('s', '0'))
                    kind = styles[si] if si < len(styles) else 'number'
                    if raw and kind == 'date':
                        try:
                            serial = float(raw)
                            # Excel's fictional 1900-02-29 cannot be represented faithfully.
                            if not epoch1904 and 60 <= serial < 61:
                                raise ValueError('Excel fictional date')
                            base = datetime(1904, 1, 1) if epoch1904 else datetime(1899, 12, 31)
                            value = base + timedelta(days=serial if epoch1904 or serial < 60 else serial - 1)
                            values[idx] = {**cell(value.isoformat(), 'date'), 'stored_raw': raw}
                        except (ValueError, OverflowError):
                            values[idx] = cell(raw, 'unsupported')
                    else:
                        values[idx] = cell(raw, kind)
            rows.append((number, values))
        return chosen.get('name'), sorted(rows)
