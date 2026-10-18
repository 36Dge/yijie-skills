#!/usr/bin/env python3
"""Local sales-video artifacts. No network, credentials, approval or polling."""
import argparse
import hashlib
import ipaddress
import json
from pathlib import Path
import sys
from urllib.parse import urlsplit

sys.dont_write_bytecode = True
VERSION = "0.1.0"
SHOTS = {
    "presenter_hold": "Presenter holds the exact reference product, speaking naturally to camera.",
    "product_closeup": "Close-up of the exact reference product; voice-over continues.",
    "tabletop": "The exact reference product rests on a plain table; voice-over continues.",
    "packshot": "Static final view of the exact reference product, with natural spoken delivery.",
}


def text(value, label, limit=1000):
    if not isinstance(value, str) or not value.strip() or len(value) > limit or "\0" in value:
        raise ValueError(f"{label}: expected nonempty text, at most {limit} characters")
    return value


def obj(value, required, optional=()):
    if not isinstance(value, dict) or set(value) - set(required) - set(optional) or set(required) - set(value):
        raise ValueError("object fields missing or unsupported")
    return value


def array(value, low, high, label):
    if not isinstance(value, list) or not low <= len(value) <= high:
        raise ValueError(f"{label}: expected {low}..{high} entries")
    return value


def integer(value, low, high, label):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{label}: expected integer {low}..{high}")
    return value


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def sha(value):
    if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
        raise ValueError("expected SHA256")
    return value


def media_url(value):
    text(value, "public image URL", 2000)
    p = urlsplit(value)
    if p.scheme != "https" or not p.hostname or "." not in p.hostname or p.username or p.password or p.query or p.fragment or p.port not in (None, 443) or any(c.isspace() for c in value) or p.hostname.endswith((".local", ".localhost")):
        raise ValueError("expected public HTTPS media URL without credentials or query; no upload is provided")
    try:
        ipaddress.ip_address(p.hostname)
    except ValueError:
        return value
    raise ValueError("literal IP media URL unsupported")


def brief(value):
    obj(value, ("product_name", "source_reference", "language", "sales_region", "target_audience", "actor", "claims", "unknowns", "image_urls", "video"))
    for key in ("product_name", "source_reference", "language", "sales_region", "target_audience", "actor"):
        text(value[key], key, 200)
    seen = set()
    for claim in array(value["claims"], 1, 12, "confirmed claims"):
        obj(claim, ("id", "source_text", "spoken_text", "source_reference"))
        for key in claim:
            text(claim[key], key, 300)
        if claim["id"] in seen:
            raise ValueError("duplicate claim ID")
        seen.add(claim["id"])
    for unknown in array(value["unknowns"], 0, 30, "unknown facts"):
        text(unknown, "unknown fact", 300)
    for image in array(value["image_urls"], 0, 9, "images"):
        media_url(image)
    if len(set(value["image_urls"])) != len(value["image_urls"]):
        raise ValueError("duplicate image URL")
    options = value["video"]
    obj(options, ("videoType", "videoTime", "aspectRatio", "resolution", "voice"), ("isPro",))
    if options["videoType"] not in ("SEED", "SEED_FAST") or type(options["videoTime"]) is not int or options["videoTime"] not in (5, 10, 15):
        raise ValueError("reviewed models SEED/SEED_FAST; duration 5/10/15 seconds")
    if options["aspectRatio"] not in ("16:9", "9:16") or options["resolution"] not in ("480p", "720p", "1080p") or options["voice"] is not True:
        raise ValueError("explicit supported ratio/resolution and voice=true required for talking video")
    if options["videoType"] == "SEED_FAST" and (options["resolution"] == "1080p" or "isPro" in options):
        raise ValueError("SEED_FAST does not support 1080p or isPro")
    if "isPro" in options and type(options["isPro"]) is not bool:
        raise ValueError("isPro must be boolean")
    return value


def plans(value):
    obj(value, ("brief", "schemes"))
    b = brief(value["brief"])
    claims = {c["id"] for c in b["claims"]}
    for i, scheme in enumerate(array(value["schemes"], 3, 3, "schemes"), 1):
        obj(scheme, ("id", "title", "shots"))
        if scheme["id"] != i or type(scheme["id"]) is not int:
            raise ValueError("scheme IDs must be 1, 2, 3 in order")
        text(scheme["title"], "scheme title", 100)
        duration = 0
        for shot in array(scheme["shots"], 1, 8, "shots"):
            obj(shot, ("seconds", "framing", "claim_ids"))
            duration += integer(shot["seconds"], 1, 15, "shot seconds")
            if shot["framing"] not in SHOTS:
                raise ValueError("unsupported framing")
            for claim in array(shot["claim_ids"], 1, 12, "claim IDs"):
                if not isinstance(claim, str) or claim not in claims:
                    raise ValueError("shot cites an unconfirmed claim")
            if len(set(shot["claim_ids"])) != len(shot["claim_ids"]):
                raise ValueError("duplicate claim in shot")
        if duration != b["video"]["videoTime"]:
            raise ValueError("shot duration sum must equal target duration")
    if len({digest(s["shots"]) for s in value["schemes"]}) != 3:
        raise ValueError("three distinct shot plans required")
    return value


def proxy(name, arguments):
    value = {"toolName": name, "arguments": arguments}
    if len(json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode()) > 16 * 1024:
        raise ValueError("request exceeds existing 16 KiB approval boundary; never truncate silently")
    return value


def prepare(value):
    p = plans(value)
    return {"expert_version": VERSION, "state": "awaiting_user_selection", "plan_sha256": digest(p), "plan": p,
            "external_calls": 0, "fact_semantics_verified": False, "speech_timing_verified": False}


def video(value):
    obj(value, ("plan", "selection"))
    p = plans(value["plan"])
    selection = obj(value["selection"], ("plan_sha256", "scheme_id", "user_message"))
    if sha(selection["plan_sha256"]) != digest(p):
        raise ValueError("selection refers to a different plan; request a current selection")
    index = integer(selection["scheme_id"], 1, 3, "scheme selection") - 1
    text(selection["user_message"], "literal user selection message", 2000)
    b = p["brief"]
    if not b["image_urls"]:
        raise ValueError("video request needs a user-authorized public product image URL; local planning remains available")
    scheme = p["schemes"][index]
    claims = {c["id"]: c["spoken_text"] for c in b["claims"]}
    lines = [f"Product: {b['product_name']}. Preserve the exact reference product appearance.",
             f"Spoken language: {b['language']}. Market: {b['sales_region']}. Audience: {b['target_audience']}.",
             f"Actor direction: {b['actor']}.",
             "Use only the exact spoken words below; no additional factual, price, performance or certification claims. No music. Keep voice clear; no new logos or product features."]
    elapsed = 0
    for shot in scheme["shots"]:
        words = " ".join(claims[c] for c in shot["claim_ids"])
        lines.append(f"[{elapsed}-{elapsed + shot['seconds']}s] {SHOTS[shot['framing']]} Speak: {words}")
        elapsed += shot["seconds"]
    prompt = "\n".join(lines)
    if len(prompt) > 2000:
        raise ValueError("final prompt exceeds 2000 characters; revise plan with user, do not truncate")
    request = proxy("aigc/multiImageVideoGenAsync", {**b["video"], "imageList": b["image_urls"], "prompt": prompt, "promptOptimizer": False})
    return {"expert_version": VERSION, "state": "video_prepared_not_submitted", "plan_sha256": digest(p),
            "selection": selection, "selected_scheme": scheme, "request": request, "request_sha256": digest(request),
            "external_calls": 0, "current_tool_schema_verified": False, "approval_granted": False,
            "fact_semantics_verified": False, "speech_timing_verified": False, "local_file": None}


def payload(result):
    if not isinstance(result, dict) or result.get("isError", False) is not False:
        return None, "mcp_error"
    decoded = result.get("structuredContent")
    blocks = result.get("content", [])
    if not isinstance(blocks, list):
        return None, "unreadable_response"
    for block in blocks:
        if not isinstance(block, dict) or block.get("type") != "text":
            return None, "unreadable_response"
        try:
            candidate = json.loads(block["text"])
        except (ValueError, KeyError, TypeError):
            return None, "unreadable_response"
        if decoded is not None and candidate != decoded:
            return None, "conflicting_response"
        decoded = candidate
    for _ in range(3):
        if not isinstance(decoded, dict):
            return None, "unreadable_response"
        if any(k in decoded and (type(decoded[k]) is not int or decoded[k] != 200) for k in ("code", "errcode", "errorCode")) or decoded.get("success") is False or decoded.get("error"):
            return None, "business_error"
        if isinstance(decoded.get("data"), dict):
            decoded = decoded["data"]
        else:
            return decoded, None
    return None, "unreadable_response"


def observe(value):
    obj(value, ("stage", "request_sha256", "source_operation_id", "mcp_result"), ("creation",))
    stage = value["stage"]
    if stage not in ("create", "query"):
        raise ValueError("stage must be create or query")
    request_sha = sha(value["request_sha256"])
    operation = text(value["source_operation_id"], "Native operation reference", 200)
    result = {"expert_version": VERSION, "state": "unknown", "request_sha256": request_sha, "source_operation_id": operation,
              "retry_creation": False, "external_calls": 0, "local_file": None, "visual_audio_quality": "not_verified"}
    expected = None
    if stage == "query":
        creation = value.get("creation", {})
        if not isinstance(creation, dict):
            raise ValueError("creation must be an original created receipt object")
        if creation.get("state") != "created" or creation.get("request_sha256") != request_sha:
            raise ValueError("query requires original created receipt for the same request")
        expected = text(creation.get("task_id"), "original task ID", 200)
        original_op = text(creation.get("source_operation_id"), "original creation operation", 200)
        if original_op == operation:
            raise ValueError("query must refer to its own Native operation")
        result["creation_operation_id"] = original_op
        result["task_id"] = expected
        result["query_request"] = proxy("aigc/taskQuery", {"taskId": expected})
    body, reason = payload(value["mcp_result"])
    if reason:
        result["reason"] = reason
        return result
    task = body.get("taskId")
    if not isinstance(task, str) or not task.strip() or len(task) > 200 or (expected is not None and task != expected):
        result["reason"] = "task_id_missing_or_mismatch"
        return result
    result["task_id"] = task
    status = body.get("status")
    if status == "FAILED":
        result.update(state="failed", reason="business_failure")
    elif stage == "create" and status in (None, "PROCESSING"):
        result.update(state="created", query_request=proxy("aigc/taskQuery", {"taskId": task}))
    elif stage == "query" and status == "PROCESSING":
        result["state"] = "processing"
    elif stage == "query" and status == "SUCCESS":
        rows = body.get("resultList")
        if isinstance(rows, list) and len(rows) == 1 and isinstance(rows[0], dict) and rows[0].get("type") == "video":
            try:
                result["result_url"] = media_url(rows[0].get("url"))
                result["state"] = "video_link_ready"
            except ValueError:
                result["reason"] = "unsupported_result_url"
        else:
            result["reason"] = "missing_or_ambiguous_video"
    else:
        result["reason"] = "unrecognized_status"
    return result


def render(result):
    lines = ["# 带货口播制作资料", "", f"状态：{result['state']}", "", "本地资料不代表提交、批准、视频生成、音轨或口型验收通过。", ""]
    if "plan" in result:
        p = result["plan"]
        b = p["brief"]
        lines += [f"商品：{b['product_name']}", f"市场：{b['sales_region']}；语言：{b['language']}；受众：{b['target_audience']}", f"方案摘要：{result['plan_sha256']}", "", "## 已确认事实与口播", ""]
        for c in b["claims"]:
            lines += [f"- {c['id']}：{c['source_text']} → {c['spoken_text']}（{c['source_reference']}）"]
        lines += ["", "## 未知，不进入宣传口播", "", *[f"- {x}" for x in b["unknowns"]]]
        for s in p["schemes"]:
            lines += ["", f"## 方案 {s['id']} · {s['title']}", ""]
            for shot in s["shots"]:
                lines += [f"- {shot['seconds']} 秒 / {shot['framing']} / 事实：{', '.join(shot['claim_ids'])}"]
        lines += ["", "请在易界会话中明确选择 1、2 或 3。选择之前停止；选择也不代替外部调用的逐次审批。"]
    elif "request" in result:
        lines += [f"选择：{result['selection']['scheme_id']}", f"方案摘要：{result['plan_sha256']}", f"请求摘要：{result['request_sha256']}", "", "## 最终提示词", "", result["request"]["arguments"]["prompt"]]
    else:
        lines += ["## 回执观察", "", json.dumps(result, ensure_ascii=False, indent=2)]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "video", "observe"))
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    try:
        source = Path(args.input)
        if source.is_symlink() or not source.is_file() or source.stat().st_size > 2 * 1024 * 1024:
            raise ValueError("input must be an ordinary JSON file of at most 2 MiB")
        raw = source.read_bytes()
        data = json.loads(raw, parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite JSON")))
        result = {"prepare": prepare, "video": video, "observe": observe}[args.action](data)
        output = Path(args.output_dir)
        target = output.resolve()
        if not target.is_relative_to(Path.cwd().resolve()) or target == Path.cwd().resolve() or output.exists() or output.is_symlink():
            raise ValueError("output must be a new child directory in the authorized working directory")
        files = {"input.json": raw, "inspection.json": (json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode(), "review.md": render(result).encode()}
        receipt = {"expert_version": VERSION, "action": args.action, "external_calls": 0,
                   "files": [{"path": name, "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()} for name, body in files.items()]}
        output.mkdir(parents=False, exist_ok=False)
        for name, body in files.items():
            (output / name).write_bytes(body)
        (output / "receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"output_dir": str(target), "state": result["state"], "external_calls": 0}, ensure_ascii=False))
    except (ValueError, TypeError, KeyError, OSError) as exc:
        print(f"Input/output unavailable: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
