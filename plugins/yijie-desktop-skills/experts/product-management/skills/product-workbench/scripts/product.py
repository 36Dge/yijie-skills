#!/usr/bin/env python3
"""Local PM documents and arithmetic. No network, credentials or app database."""
import argparse
import hashlib
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path

KINDS = {
    "prd": "需求规格", "roadmap": "路线图", "stakeholder": "利益相关者报告",
    "research": "用户研究综合", "competitive": "竞品分析", "metrics": "指标复盘",
}
LIMIT = 4 * 1024 * 1024


def require(condition, message):
    if not condition:
        raise ValueError(message)


def text(value, label):
    require(isinstance(value, str) and bool(value.strip()), f"{label}: expected non-empty text")
    return value


def read_json(file):
    p = Path(file)
    require(p.is_file() and not p.is_symlink() and p.stat().st_size <= LIMIT, "input must be a bounded regular file")
    raw = p.read_bytes()
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


def number(value, label, minimum=None, maximum=None):
    if value is None:
        return None
    require(not isinstance(value, bool) and isinstance(value, (str, int, float)), f"{label}: expected number or null")
    try:
        n = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError(f"{label}: invalid number") from exc
    require(n.is_finite(), f"{label}: finite number required")
    require(minimum is None or n >= minimum, f"{label}: below minimum")
    require(maximum is None or n <= maximum, f"{label}: above maximum")
    return n


def rice(data, source_ids):
    if data is None:
        return None
    period = text(data.get("reach_period"), "reach_period")
    unit = text(data.get("effort_unit"), "effort_unit")
    rows = data.get("items")
    require(isinstance(rows, list) and 0 < len(rows) <= 200, "RICE items required (1–200)")
    result, seen = [], set()
    for row in rows:
        key = text(row.get("id"), "RICE id")
        require(key not in seen, "duplicate RICE id")
        seen.add(key)
        require(row.get("reach_period") == period and row.get("effort_unit") == unit, "mixed RICE period/unit")
        refs = row.get("source_ids")
        require(isinstance(refs, list) and refs and all(s in source_ids for s in refs), "RICE source references required")
        values = {k: number(row.get(k), k, Decimal(0), Decimal(1) if k == "confidence" else None)
                  for k in ("reach", "impact", "confidence", "effort")}
        require(values["effort"] is None or values["effort"] > 0, "effort must be positive; unknown is null")
        missing = [k for k, v in values.items() if v is None]
        score = None if missing else values["reach"] * values["impact"] * values["confidence"] / values["effort"]
        result.append({"id": key, "name": text(row.get("name"), "RICE name"),
                       "inputs": {k: None if v is None else str(v) for k, v in values.items()},
                       "source_ids": refs, "score": None if score is None else str(score), "missing": missing})
    known = sorted((r for r in result if r["score"] is not None), key=lambda r: -Decimal(r["score"]))
    return {"reach_period": period, "effort_unit": unit, "confidence_unit": "fraction_0_to_1",
            "formula": "reach * impact * confidence / effort", "items": result,
            "ranked_ids": [r["id"] for r in known], "unranked_ids": [r["id"] for r in result if r["score"] is None]}


def build(plan, sources):
    require(type(plan.get("schema_version")) is int and plan["schema_version"] == 1, "unsupported plan version")
    title = text(plan.get("title"), "title")
    records = sources.get("sources")
    require(isinstance(records, list) and 0 < len(records) <= 200, "sources required (1–200)")
    lookup = {}
    for source in records:
        sid = text(source.get("id"), "source id")
        require(sid not in lookup, "duplicate source id")
        text(source.get("locator"), "source locator")
        text(source.get("text"), "source text")
        lookup[sid] = source
    docs = plan.get("documents")
    require(isinstance(docs, list) and 0 < len(docs) <= 6, "documents required (1–6)")
    files, kinds = {}, set()
    for doc in docs:
        kind = doc.get("kind")
        require(kind in KINDS and kind not in kinds, "unknown/duplicate document kind")
        kinds.add(kind)
        refs = doc.get("source_ids")
        require(isinstance(refs, list) and refs and all(s in lookup for s in refs), "document source references required")
        sections = doc.get("sections")
        require(isinstance(sections, list) and 0 < len(sections) <= 30, "sections required")
        parts = [f"# {title} · {KINDS[kind]}", "本地工作稿；结构检查不代表事实、调研代表性或决策已获确认。"]
        for section in sections:
            parts += ["## " + text(section.get("heading"), "heading"), text(section.get("body"), "section body")]
        for quote in doc.get("quotes", []):
            sid = quote.get("source_id")
            q = text(quote.get("text"), "quote")
            require(sid in refs and q in lookup[sid]["text"], "quote does not match cited source")
            parts += [f"引用 [{sid}]：{q}"]
        parts += ["## 资料来源", *[f"- [{sid}] {lookup[sid]['locator']}" for sid in refs],
                  "## 待确认与假设", text(doc.get("open_questions"), "open_questions (write 无 when none)")]
        files[f"{kind}.md"] = "\n\n".join(parts) + "\n"
    result = rice(plan.get("rice"), lookup)
    if result is not None:
        require("roadmap" in kinds, "RICE requires roadmap document")
        files["rice.json"] = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
        lines = ["## RICE独立计算", f"覆盖周期：{result['reach_period']}；工作量单位：{result['effort_unit']}；置信度0–1。",
                 "排序仅包含参数完整项；分数辅助判断，不自动承诺排期。"]
        for row in result["items"]:
            lines.append(f"- {row['id']} {row['name']}：{row['score'] if row['score'] is not None else '待补充 ' + ', '.join(row['missing'])}")
        lines.append("完整项排序：" + "、".join(result["ranked_ids"]))
        files["roadmap.md"] += "\n" + "\n".join(lines) + "\n"
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--sources", required=True)
    parser.add_argument("--out", required=True, help="new directory; never overwrite an earlier version")
    args = parser.parse_args()
    try:
        plan, input_hash = read_json(args.input)
        sources, sources_hash = read_json(args.sources)
        files = build(plan, sources)
        out = Path(args.out).absolute()
        require(not out.exists() and not out.is_symlink(), "output exists; choose a new version directory")
        out = out.resolve()
        require(not out.is_relative_to(Path(__file__).resolve().parent.parent), "do not write inside installed expert resources")
        files["input.json"] = json.dumps(plan, ensure_ascii=False, indent=2) + "\n"
        files["sources.json"] = json.dumps(sources, ensure_ascii=False, indent=2) + "\n"
        require(all(len(content.encode("utf-8")) <= LIMIT for content in files.values()), "output exceeds the per-file limit")
        out.mkdir(parents=True, exist_ok=False)
        receipt = {"schema_version": 1, "expert_id": "product-management", "content_version": "0.1.0",
                   "input_sha256": input_hash, "sources_sha256": sources_hash,
                   "checks": "structure, source IDs, literal quotes and RICE arithmetic only; semantic review required",
                   "files": []}
        for name, content in files.items():
            data = content.encode("utf-8")
            with (out / name).open("xb") as file:
                file.write(data)
            receipt["files"].append({"path": name, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)})
        with (out / "receipt.json").open("x", encoding="utf-8") as file:
            json.dump(receipt, file, ensure_ascii=False, indent=2)
            file.write("\n")
        print(json.dumps({"status": "written", "directory": str(out), "files": len(files) + 1}, ensure_ascii=False))
    except (ValueError, TypeError, KeyError, OSError, AttributeError) as exc:
        parser.exit(2, f"Product output not completed: {exc}\nUse a new output directory after correcting the input; earlier files are retained.\n")


if __name__ == "__main__":
    main()
