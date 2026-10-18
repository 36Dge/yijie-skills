#!/usr/bin/env python3
"""Validate and save versioned story files; structural checks are not literary review."""
import argparse
import hashlib
import json
import re
from pathlib import Path

LIMIT = 8 * 1024 * 1024
BRIEF = ("genre", "length", "protagonist", "conflict", "tone", "pov")
TRACKING = ("plot-tracker", "timeline", "character-state", "relationships")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def text(value, label):
    require(isinstance(value, str) and value.strip(), f"{label}: non-empty text required")
    return value


def load(file):
    p = Path(file)
    require(p.is_file() and not p.is_symlink() and p.stat().st_size <= LIMIT, "bounded regular input required")
    raw = p.read_bytes()
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


def indexed(rows, label, maximum=1000):
    require(isinstance(rows, list) and len(rows) <= maximum, f"{label}: bounded list required")
    result = {}
    for row in rows:
        key = row.get("id")
        require(isinstance(key, str) and re.fullmatch(r"[a-zA-Z][a-zA-Z0-9_-]{0,63}", key), f"{label}: stable ID required")
        require(key not in result, f"{label}: duplicate ID")
        result[key] = row
    return result


def refs(values, known, label):
    require(isinstance(values, list) and len(values) == len(set(values)) and all(v in known for v in values), f"{label}: invalid references")
    return values


def chapter_ref(value, chapters, optional=False):
    require((optional and value is None) or value in chapters, "unknown chapter reference")


def validate(data, previous=None):
    require(type(data.get("schema_version")) is int and data["schema_version"] == 1, "unsupported story schema")
    text(data.get("project_id"), "project_id")
    text(data.get("title"), "title")
    require(type(data.get("revision")) is int and data["revision"] > 0, "positive revision required")
    require(data.get("stage") in ("brief", "bible", "draft", "continuation", "revision"), "unknown stage")
    for key in BRIEF:
        text(data.get("brief", {}).get(key), f"brief.{key}")
    text(data.get("bible"), "bible")
    require(type(data.get("bible_confirmed")) is bool, "bible_confirmed must be boolean")
    if data["bible_confirmed"]:
        text(data.get("confirmation_source"), "confirmation_source (actual user instruction)")
    chars = indexed(data.get("characters"), "characters")
    require(chars, "at least one character required")
    for row in chars.values():
        text(row.get("name"), "character name")
        text(row.get("motivation"), "character motivation")
        text(row.get("voice"), "character voice")
    chapters = indexed(data.get("chapters"), "chapters")
    if chapters:
        require(data["bible_confirmed"], "confirm Bible before writing chapters")
    numbers = []
    for row in chapters.values():
        require(type(row.get("number")) is int and row["number"] > 0, "positive chapter number required")
        numbers.append(row["number"])
        require(row.get("pov") in chars, "unknown POV character")
        for key in ("title", "goal", "summary", "text"):
            text(row.get(key), f"chapter.{key}")
    require(sorted(numbers) == list(range(1, len(numbers) + 1)), "chapter sequence must be contiguous from 1")
    facts = indexed(data.get("facts"), "facts")
    for row in facts.values():
        text(row.get("text"), "fact text")
        require(row.get("character_id") is None or row["character_id"] in chars, "unknown fact character")
        chapter_ref(row.get("established_chapter"), chapters, True)
    for chapter in chapters.values():
        for fid in refs(chapter.get("fact_ids"), facts, "chapter facts"):
            established = facts[fid].get("established_chapter")
            require(established is None or chapters[established]["number"] <= chapter["number"], "chapter cites a future established fact")
    tracking = data.get("tracking")
    require(isinstance(tracking, dict) and set(tracking) == set(TRACKING), "exactly four continuity ledgers required")
    warnings = []
    for row in indexed(tracking["plot-tracker"], "plots").values():
        text(row.get("description"), "plot description")
        chapter_ref(row.get("planted_chapter"), chapters, True)
        require(row.get("status") in ("planned", "open", "resolved"), "unknown plot status")
        due = row.get("due_chapter")
        require(due is None or (type(due) is int and due > 0), "due_chapter must be positive or null")
        resolved = row.get("resolved_chapter")
        chapter_ref(resolved, chapters, True)
        if row["status"] == "resolved":
            require(resolved is not None and row.get("planted_chapter") is not None, "resolved plot needs planting and resolution")
            require(chapters[resolved]["number"] >= chapters[row["planted_chapter"]]["number"], "resolution precedes planting")
        else:
            require(resolved is None, "unresolved plot cannot have resolution")
        if row["status"] == "open":
            require(row.get("planted_chapter") is not None, "open plot needs planting chapter")
            if due is not None and due <= len(chapters):
                warnings.append(f"伏笔 {row['id']} 已到计划回收章但仍未解决；需人工复核")
    sequences, covered_chapters = set(), set()
    for row in indexed(tracking["timeline"], "timeline").values():
        chapter_ref(row.get("chapter_id"), chapters)
        covered_chapters.add(row["chapter_id"])
        seq = row.get("sequence")
        require(type(seq) is int and seq > 0 and seq not in sequences, "timeline sequence must be unique positive integer")
        sequences.add(seq)
        text(row.get("time_label"), "timeline time_label")
        text(row.get("event"), "timeline event")
        refs(row.get("character_ids"), chars, "timeline characters")
    require(covered_chapters == set(chapters), "every chapter needs a timeline event")
    states = tracking["character-state"]
    require(isinstance(states, list) and len(states) == len(chars), "one current state for every character required")
    state_ids = [row.get("character_id") for row in states]
    require(len(set(state_ids)) == len(chars) and set(state_ids) == set(chars), "duplicate/missing character state")
    for row in states:
        chapter_ref(row.get("as_of_chapter"), chapters, True)
        for key in ("location", "status"):
            text(row.get(key), f"character-state.{key}")
        for fid in refs(row.get("known_fact_ids"), facts, "known facts"):
            established = facts[fid].get("established_chapter")
            as_of = row.get("as_of_chapter")
            require(established is None or (as_of is not None and chapters[established]["number"] <= chapters[as_of]["number"]), "character state knows a future fact")
    for row in indexed(tracking["relationships"], "relationships").values():
        require(row.get("from") in chars and row.get("to") in chars and row["from"] != row["to"], "relationship characters invalid")
        text(row.get("description"), "relationship description")
        chapter_ref(row.get("as_of_chapter"), chapters, True)
    impact = {"changed_facts": [], "changed_chapters": [], "affected_chapters": [], "review_required_chapters": []}
    if previous is None:
        require(data["revision"] == 1, "later revisions require --previous")
    else:
        require(previous.get("project_id") == data["project_id"], "previous project mismatch")
        require(data["revision"] == previous.get("revision", 0) + 1, "revision must increment by one")
        old_chapters = indexed(previous["chapters"], "previous chapters")
        old_facts = indexed(previous["facts"], "previous facts")
        old_chars = indexed(previous["characters"], "previous characters")
        require(set(old_chapters) <= set(chapters) and set(old_facts) <= set(facts) and set(old_chars) <= set(chars), "retain old chapter/fact/character IDs")
        changed_facts = [key for key, row in old_facts.items() if facts[key] != row]
        changed_chapters = [key for key, row in old_chapters.items() if chapters[key] != row]
        setting_changed = data["bible"] != previous["bible"] or data["brief"] != previous["brief"] or any(chars[k] != v for k, v in old_chars.items())
        affected = sorted(set(changed_chapters) | {key for key, row in old_chapters.items() if setting_changed or set(row["fact_ids"]) & set(changed_facts)})
        if changed_facts or changed_chapters or setting_changed:
            text(data.get("change_reason"), "change_reason required for revision")
        impact = {"changed_facts": changed_facts, "changed_chapters": changed_chapters,
                  "affected_chapters": affected, "review_required_chapters": sorted(set(affected) - set(changed_chapters))}
        if impact["review_required_chapters"]:
            warnings.append("设定变更影响旧章节但尚未修改；不得声称全部连续性问题已解决")
    return impact, warnings


def previous_state(directory):
    root = Path(directory)
    receipt, _ = load(root / "receipt.json")
    require(receipt.get("expert_id") == "novel-creator" and receipt.get("schema_version") == 1, "previous receipt mismatch")
    entries = receipt.get("files")
    require(isinstance(entries, list), "previous files required")
    names = set()
    for entry in entries:
        name = entry["path"]
        require(isinstance(name, str) and re.fullmatch(r"(?:tracking/|chapters/)?[a-zA-Z0-9_-]+\.(?:md|json)", name), "invalid previous receipt path")
        require(name not in names, "duplicate previous receipt path")
        names.add(name)
        file = root / name
        require(file.is_file() and not file.is_symlink() and file.stat().st_size <= LIMIT, "previous file missing")
        require(hashlib.sha256(file.read_bytes()).hexdigest() == entry["sha256"], "previous file changed; reconcile manually before continuing")
    require("story.json" in names, "previous story missing from receipt")
    state, digest = load(root / "story.json")
    return state, digest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--previous", help="previous saved directory, read only")
    args = parser.parse_args()
    try:
        data, input_hash = load(args.input)
        previous, previous_hash = previous_state(args.previous) if args.previous else (None, None)
        impact, warnings = validate(data, previous)
        out = Path(args.out).absolute()
        require(not out.exists() and not out.is_symlink(), "output exists; choose new version directory")
        out = out.resolve()
        require(not out.is_relative_to(Path(__file__).resolve().parent.parent), "do not write inside installed resources")
        encode = lambda value: json.dumps(value, ensure_ascii=False, indent=2) + "\n"
        files = {"story.json": encode(data), "brief.md": "# 创作Brief\n\n" + "\n".join(f"- {k}: {data['brief'][k]}" for k in BRIEF) + "\n",
                 "bible.md": data["bible"] + "\n", "impact.json": encode(impact),
                 "review.md": "# 本版复核\n\n机器仅验证结构、引用、版本与文件完整性；人物动机、事实语义和文学质量须阅读正文复核。\n\n" + "\n".join(warnings) + "\n"}
        for chapter in data["chapters"]:
            files[f"chapters/{chapter['id']}.md"] = f"# {chapter['title']}\n\n{chapter['text']}\n"
        for name in TRACKING:
            files[f"tracking/{name}.json"] = encode(data["tracking"][name])
        require(all(len(content.encode("utf-8")) <= LIMIT for content in files.values()), "output exceeds the per-file limit")
        out.mkdir(parents=True, exist_ok=False)
        receipt = {"schema_version": 1, "expert_id": "novel-creator", "content_version": "0.1.0", "revision": data["revision"],
                   "input_sha256": input_hash, "previous_story_sha256": previous_hash, "warnings": warnings,
                   "semantic_review": "required", "files": []}
        for name, content in files.items():
            file = out / name
            file.parent.mkdir(exist_ok=True)
            raw = content.encode("utf-8")
            with file.open("xb") as target:
                target.write(raw)
            receipt["files"].append({"path": name, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})
        with (out / "receipt.json").open("x", encoding="utf-8") as target:
            target.write(encode(receipt))
        print(json.dumps({"status": "written_requires_semantic_review", "directory": str(out), "warnings": warnings}, ensure_ascii=False))
    except (ValueError, TypeError, KeyError, OSError, AttributeError) as exc:
        parser.exit(2, f"Story output not completed: {exc}\nEarlier versions retained; correct inputs and select a new output directory.\n")


if __name__ == "__main__":
    main()
