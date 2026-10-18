"""Local quotation files only. Python 3.10+, standard library; no network or installs."""
import argparse
import csv
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape
import zipfile

NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
MONEY = Decimal("0.01")


def text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"missing text: {label}")
    if len(value) > 2000 or any(ord(c) < 32 and c not in "\t\n\r" for c in value):
        raise ValueError(f"unsupported text: {label}")
    return value.strip()


def number(value, label, positive=False):
    if isinstance(value, bool) or value is None or str(value).strip() == "":
        raise ValueError(f"missing number: {label}; unknown is not zero")
    try:
        n = Decimal(str(value))
    except InvalidOperation as error:
        raise ValueError(f"invalid number: {label}") from error
    if not n.is_finite() or n < 0 or n > Decimal("1000000000000") or (positive and n == 0):
        raise ValueError(f"out of range: {label}")
    if n.as_tuple().exponent < -6:
        raise ValueError(f"more than 6 decimals: {label}")
    return n


def money(n):
    return n.quantize(MONEY, rounding=ROUND_HALF_UP)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_json(path):
    p = Path(path)
    if p.stat().st_size > 8 * 1024 * 1024:
        raise ValueError("input exceeds 8 MiB")
    return json.loads(p.read_text(encoding="utf-8-sig"), parse_float=str)


def column(index):
    result = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        result = chr(65 + remainder) + result
    return result


def read_table(path, sheet=None):
    """Read values without evaluating formulas or modifying the user's workbook."""
    p = Path(path)
    if p.stat().st_size > 8 * 1024 * 1024:
        raise ValueError("table exceeds 8 MiB")
    if p.suffix.lower() == ".csv":
        with p.open(encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.reader(stream))
    elif p.suffix.lower() == ".xlsx":
        with zipfile.ZipFile(p) as z:
            names = z.namelist()
            if len(names) > 2048 or sum(i.file_size for i in z.infolist()) > 32 * 1024 * 1024:
                raise ValueError("workbook exceeds supported size")
            strings = []
            if "xl/sharedStrings.xml" in names:
                strings = ["".join(si.itertext()) for si in ET.fromstring(z.read("xl/sharedStrings.xml"))]
            sheets = ET.fromstring(z.read("xl/workbook.xml")).find(f"{{{NS}}}sheets")
            selected = [s for s in sheets if sheet is None or s.attrib["name"] == sheet]
            if len(selected) != 1:
                raise ValueError("specify a sheet name for a multi-sheet workbook")
            links = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
            link = next(r for r in links if r.attrib["Id"] == selected[0].attrib[f"{{{REL}}}id"])
            target = link.attrib["Target"]
            if link.attrib.get("TargetMode") == "External" or ".." in PurePosixPath(target).parts:
                raise ValueError("unsupported worksheet reference")
            target = target.lstrip("/") if target.startswith("/") else "xl/" + target
            rows = []
            for row in ET.fromstring(z.read(target)).findall(f".//{{{NS}}}sheetData/{{{NS}}}row"):
                values = {}
                for cell in row:
                    letters = re.match(r"[A-Z]+", cell.attrib["r"])[0]
                    index = 0
                    for char in letters:
                        index = index * 26 + ord(char) - 64
                    if index > 256:
                        raise ValueError("more than 256 columns")
                    kind = cell.attrib.get("t", "n")
                    value = cell.findtext(f"{{{NS}}}v", "")
                    if cell.find(f"{{{NS}}}f") is not None and not value:
                        raise ValueError(f"formula without cached value at {cell.attrib['r']}; recalculate in Excel first")
                    if kind == "s":
                        value = strings[int(value)]
                    elif kind == "inlineStr":
                        value = "".join(cell.find(f"{{{NS}}}is").itertext())
                    elif kind == "e":
                        raise ValueError(f"spreadsheet error at {cell.attrib['r']}")
                    values[index] = value
                rows.append([values.get(i, "") for i in range(1, max(values, default=0) + 1)])
    else:
        raise ValueError("table format must be .csv or .xlsx")
    if not rows or len(rows) > 10001:
        raise ValueError("table needs a header and at most 10000 rows")
    headers = rows[0]
    if not headers or len(headers) != len(set(headers)) or any(not h.strip() for h in headers):
        raise ValueError("headers must be nonempty and unique")
    result = []
    for row in rows[1:]:
        if not any(row):
            continue
        if len(row) > len(headers):
            raise ValueError("data outside named columns")
        result.append(dict(zip(headers, row + [""] * (len(headers) - len(row)))))
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
                        payload = f'<f>{escape(value[0])}</f><v>{value[1]}</v>'
                        cells.append(f'<c r="{ref}" s="2">{payload}</c>')
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


def calculate(config, items):
    for key in ["quote_id", "date", "supplier", "customer", "currency", "tax_mode", "source", "terms"]:
        text(config.get(key), key)
    date.fromisoformat(config["date"])
    if not re.fullmatch(r"[A-Z]{3}", config["currency"]):
        raise ValueError("currency needs explicit 3-letter code")
    if config.get("currency_decimals") != 2:
        raise ValueError("this worksheet requires explicit currency_decimals=2")
    if config["tax_mode"] not in ("included", "excluded"):
        raise ValueError("tax_mode must be included or excluded")
    rate = number(config.get("tax_rate"), "tax_rate")
    if rate > 1:
        raise ValueError("tax_rate must be a fraction in [0,1]")
    freight = number(config.get("freight"), "freight")
    if money(freight) != freight:
        raise ValueError("freight needs explicit final amount to 2 decimals")
    if config.get("freight_basis") != "final_amount":
        raise ValueError("freight_basis=final_amount required; no implied freight tax")
    if not items or len(items) > 10000:
        raise ValueError("need 1 to 10000 item rows")
    lines = []
    for i, row in enumerate(items, 1):
        line = {k: text(row.get(k), f"row {i} {k}") for k in ("sku", "name", "spec", "unit")}
        qty = number(row.get("quantity"), f"row {i} quantity", True)
        price = number(row.get("unit_price"), f"row {i} unit_price")
        amount = money(qty * price)
        net = amount if config["tax_mode"] == "excluded" else money(amount / (1 + rate))
        tax = money(net * rate) if config["tax_mode"] == "excluded" else amount - net
        if net + tax > Decimal("1000000000000"):
            raise ValueError("line amount exceeds supported worksheet precision")
        lines.append({**line, "quantity": qty, "unit_price": price, "net": net, "tax": tax, "gross": net + tax})
    totals = {k: sum((line[k] for line in lines), Decimal("0.00")) for k in ("net", "tax", "gross")}
    if totals["gross"] + freight > Decimal("1000000000000"):
        raise ValueError("total exceeds supported worksheet precision")
    return {"schema_version": 1, "quote": config, "lines": lines, "totals": {**totals, "freight": freight, "grand_total": totals["gross"] + freight}, "rounding": "ROUND_HALF_UP, per line, 2 decimals; freight is final amount"}


def quotation_sheets(result):
    q, lines, totals = result["quote"], result["lines"], result["totals"]
    rows = [["SKU", "品名", "规格", "单位", "数量", "税率", "单价", "未税金额", "税额", "含税金额"]]
    for i, line in enumerate(lines, 2):
        net = f"ROUND(E{i}*G{i},2)" if q["tax_mode"] == "excluded" else f"ROUND(ROUND(E{i}*G{i},2)/(1+F{i}),2)"
        tax = f"ROUND(H{i}*F{i},2)" if q["tax_mode"] == "excluded" else f"ROUND(E{i}*G{i},2)-H{i}"
        rows.append([line["sku"], line["name"], line["spec"], line["unit"], line["quantity"], Decimal(str(q["tax_rate"])), line["unit_price"], (net, line["net"]), (tax, line["tax"]), (f"H{i}+I{i}", line["gross"])])
    last = len(rows)
    rows.append(["合计", "", "", "", "", "", "", (f"SUM(H2:H{last})", totals["net"]), (f"SUM(I2:I{last})", totals["tax"]), (f"SUM(J2:J{last})", totals["gross"])])
    rows.append(["运费最终额", "", "", "", "", "", "", "", "", totals["freight"]])
    rows.append(["总计", "", "", "", "", "", "", "", "", (f"J{last+1}+J{last+2}", totals["grand_total"])])
    meta = [["字段", "内容"]] + [[k, v] for k, v in q.items() if k != "items"] + [["rounding", result["rounding"]], ["scope", "用户提供价格；本地文件；未发送；未查询实时行情"]]
    return [("报价明细", rows), ("条款与来源", meta)]


def ledger_rows(result, old):
    q = result["quote"]
    new = [{"record_id": f"{q['quote_id']}:{i}", "quote_id": q["quote_id"], "date": q["date"], "supplier": q["supplier"], "customer": q["customer"], "currency": q["currency"], "tax_mode": q["tax_mode"], "tax_rate": str(q["tax_rate"]), "source": q["source"], **{k: str(v) for k, v in line.items()}} for i, line in enumerate(result["lines"], 1)]
    required = set(new[0])
    for row in old:
        if not required.issubset(row) or any(not str(row[k]).strip() for k in required):
            raise ValueError("ledger requires explicit mapping to documented columns; no automatic schema conversion")
    ids = [r["record_id"] for r in old + new]
    if len(ids) != len(set(ids)):
        raise ValueError("quote record already exists; choose a new quote_id for an intentional revision")
    return old + new


def compare(rows, sku):
    selected = [r for r in rows if r.get("sku") == sku]
    groups = {}
    for row in selected:
        key = tuple(row[k] for k in ("spec", "unit", "currency", "tax_mode", "tax_rate"))
        groups.setdefault(key, []).append(row)
    return {"sku": sku, "matches": len(selected), "groups": [{"basis": dict(zip(("spec", "unit", "currency", "tax_mode", "tax_rate"), key)), "records": records, "min_unit_price": str(min(number(r["unit_price"], "ledger unit_price") for r in records)), "max_unit_price": str(max(number(r["unit_price"], "ledger unit_price") for r in records))} for key, records in groups.items()], "note": "仅同规格/单位/币种/税口径分组比较；未判定交货条款等价或实时价格合理性"}


def write_json(path, data):
    with Path(path).open("x", encoding="utf-8") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2, default=str)
        stream.write("\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--items", help="CSV or XLSX; otherwise config.items")
    parser.add_argument("--sheet")
    parser.add_argument("--ledger", help="previous generated CSV/XLSX, retained unchanged")
    parser.add_argument("--compare-sku")
    parser.add_argument("--output-dir", required=True, help="new folder inside current task workspace")
    args = parser.parse_args()
    config = load_json(args.config)
    result = calculate(config, read_table(args.items, args.sheet) if args.items else config.get("items"))
    old = read_table(args.ledger, "报价台账" if args.ledger.lower().endswith(".xlsx") else None) if args.ledger else []
    ledger = ledger_rows(result, old)
    comparison = compare(ledger, args.compare_sku) if args.compare_sku else None
    output = Path(args.output_dir).resolve()
    if not output.is_relative_to(Path.cwd().resolve()) or output == Path.cwd().resolve():
        raise ValueError("output must be a new subfolder of current task workspace")
    result["inputs"] = [{"file": Path(p).name, "sha256": digest(p)} for p in (args.config, args.items, args.ledger) if p]
    output.mkdir(parents=False, exist_ok=False)
    write_xlsx(output / "quotation.xlsx", quotation_sheets(result))
    write_json(output / "calculation.json", result)
    headers = list(dict.fromkeys(k for row in ledger for k in row))
    with (output / "ledger.csv").open("x", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, headers)
        writer.writeheader()
        writer.writerows(ledger)
    write_xlsx(output / "ledger.xlsx", [("报价台账", [headers] + [[r.get(k, "") for k in headers] for r in ledger])])
    if comparison is not None:
        write_json(output / "comparison.json", comparison)
    print(json.dumps({"status": "complete", "directory": str(output), "lines": len(result["lines"]), "ledger_rows": len(ledger), "grand_total": str(result["totals"]["grand_total"])}, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, KeyError, TypeError, StopIteration, ET.ParseError, zipfile.BadZipFile) as error:
        print(f"quotation not completed: {error}", file=sys.stderr)
        sys.exit(2)
