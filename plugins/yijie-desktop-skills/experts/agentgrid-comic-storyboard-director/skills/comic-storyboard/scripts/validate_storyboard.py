#!/usr/bin/env python3
"""Validate local storyboard files using only the Python 3.10+ standard library.

Adapted from AgentGrid storyboard-continuity 1.0.0; no network or subprocesses.
Reads explicit inputs and exclusively creates a new output; never rewrites inputs.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any

STATUSES = {"draft", "approved", "locked", "blocked"}
TEXT_FIELDS = ("narrativePurpose", "framing", "camera", "action", "productionPrompt")


def number(value: Any, label: str, errors: list[str]) -> Decimal | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        errors.append(f"{label} must be a number")
        return None
    parsed = Decimal(str(value))
    if not parsed.is_finite():
        errors.append(f"{label} must be finite")
        return None
    return parsed


def strings(value: Any, label: str, errors: list[str]) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
        errors.append(f"{label} must be an array of non-empty strings")
        return []
    return value


def registry(value: Any, label: str, prefix: str, errors: list[str]) -> set[str]:
    items = strings(value, label, errors)
    if len(items) != len(set(items)):
        errors.append(f"{label} contains duplicate IDs")
    if any(re.fullmatch(rf"{prefix}-[0-9]{{3,}}", item) is None for item in items):
        errors.append(f"{label} IDs must use {prefix}-###")
    return set(items)


def validate(data: dict[str, Any], baseline: dict[str, Any] | None = None) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if data.get("schemaVersion") != "1.0":
        errors.append("schemaVersion must be 1.0")
    if not isinstance(data.get("episodeId"), str) or not data["episodeId"].strip():
        errors.append("episodeId is required")
    registries = data.get("registries")
    if not isinstance(registries, dict):
        registries = {}
        errors.append("registries must be an object")
    characters = registry(registries.get("characters"), "registries.characters", "CHAR", errors)
    scenes = registry(registries.get("scenes"), "registries.scenes", "SC", errors)
    props = registry(registries.get("props"), "registries.props", "PROP", errors)
    if not scenes:
        errors.append("registries.scenes must not be empty")
    shots = data.get("shots")
    if not isinstance(shots, list) or not shots:
        errors.append("shots must be a non-empty array")
        shots = []
    by_id: dict[str, dict[str, Any]] = {}
    total = Decimal("0")
    for index, shot in enumerate(shots):
        label = f"shots[{index}]"
        if not isinstance(shot, dict):
            errors.append(f"{label} must be an object")
            continue
        shot_id = shot.get("shotId")
        if not isinstance(shot_id, str) or re.fullmatch(r"SH-[0-9]{3,}", shot_id) is None:
            errors.append(f"{label}.shotId must use SH-###")
        elif shot_id in by_id:
            errors.append(f"{label}.shotId is duplicated: {shot_id}")
        else:
            by_id[shot_id] = shot
        duration = number(shot.get("durationSec"), f"{label}.durationSec", errors)
        if duration is not None:
            if duration <= 0:
                errors.append(f"{label}.durationSec must be positive")
            else:
                total += duration
        scene_id = shot.get("sceneId")
        if not isinstance(scene_id, str) or scene_id not in scenes:
            errors.append(f"{label}.sceneId must reference a registered scene")
        for field, known in (("characters", characters), ("props", props)):
            refs = strings(shot.get(field), f"{label}.{field}", errors)
            if len(refs) != len(set(refs)):
                errors.append(f"{label}.{field} contains duplicate references")
            if set(refs) - known:
                errors.append(f"{label}.{field} references unknown IDs: {sorted(set(refs) - known)}")
        version = shot.get("version")
        if isinstance(version, bool) or not isinstance(version, int) or version < 1:
            errors.append(f"{label}.version must be an integer >= 1")
        status = shot.get("status")
        if not isinstance(status, str) or status not in STATUSES:
            errors.append(f"{label}.status must be one of {sorted(STATUSES)}")
        for field in TEXT_FIELDS:
            if not isinstance(shot.get(field), str) or not shot[field].strip():
                errors.append(f"{label}.{field} must be a non-empty string")
        if not isinstance(shot.get("dialogue"), str):
            errors.append(f"{label}.dialogue must be a string (may be empty)")
        for field in ("continuityIn", "continuityOut"):
            strings(shot.get(field), f"{label}.{field}", errors)
    if "targetDurationSec" not in data:
        errors.append("targetDurationSec is required; use null when unknown")
    target = data.get("targetDurationSec")
    tolerance = number(data.get("durationToleranceSec"), "durationToleranceSec", errors)
    if tolerance is not None and tolerance < 0:
        errors.append("durationToleranceSec must be non-negative")
    duration_pass: bool | None = None
    if target is None:
        warnings.append("targetDurationSec is unknown; target alignment was not evaluated")
    else:
        target_value = number(target, "targetDurationSec", errors)
        if target_value is not None and target_value <= 0:
            errors.append("targetDurationSec must be positive")
        elif target_value is not None and tolerance is not None and tolerance >= 0:
            duration_pass = abs(total - target_value) <= tolerance
            if not duration_pass:
                errors.append(f"shot duration total {total} differs from target {target_value} beyond tolerance {tolerance}")
    changes: dict[str, Any] = {"baselineCompared": baseline is not None}
    if baseline is not None:
        prior_validation = validate(baseline)
        if prior_validation["status"] != "pass":
            errors.append("baseline must pass structural validation before comparison")
        else:
            if baseline["episodeId"] != data.get("episodeId"):
                errors.append("baseline episodeId differs from current episodeId")
            old = {shot["shotId"]: shot for shot in baseline["shots"]}
            changed, unchanged = [], []
            for shot_id in sorted(old.keys() & by_id.keys()):
                before, after = old[shot_id], by_id[shot_id]
                before_content = {k: v for k, v in before.items() if k != "version"}
                after_content = {k: v for k, v in after.items() if k != "version"}
                if before_content == after_content:
                    unchanged.append(shot_id)
                    if before.get("version") != after.get("version"):
                        errors.append(f"{shot_id}: unchanged shot must preserve version")
                else:
                    changed.append(shot_id)
                    version = after.get("version")
                    if isinstance(version, bool) or not isinstance(version, int) or version <= before["version"]:
                        errors.append(f"{shot_id}: changed shot must increase version")
                if before["status"] == "locked" and before != after:
                    errors.append(f"{shot_id}: locked shot must remain unchanged")
            removed = sorted(old.keys() - by_id.keys())
            for shot_id in removed:
                if old[shot_id]["status"] == "locked":
                    errors.append(f"{shot_id}: locked shot cannot be removed")
            changes.update(changedShotIds=changed, unchangedShotIds=unchanged,
                           addedShotIds=sorted(by_id.keys() - old.keys()), removedShotIds=removed)
    return {
        "schemaVersion": "1.0", "status": "pass" if not errors else "fail",
        "episodeId": data.get("episodeId"), "shotCount": len(shots),
        "actualDurationSec": float(total), "targetDurationSec": target,
        "durationPass": duration_pass, "errors": errors, "warnings": warnings,
        **changes,
        "scopeNote": "Structural, reference, ID, version and duration validation only; continuity meaning, creative quality, rights and media generation require separate review.",
    }


def read_document(path: Path) -> dict[str, Any]:
    def reject_constant(value: str) -> None:
        raise ValueError(f"non-JSON numeric constant: {value}")

    data = json.loads(path.read_text(encoding="utf-8-sig"), parse_constant=reject_constant)
    if not isinstance(data, dict):
        raise ValueError("JSON root must be an object")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--baseline", type=Path)
    args = parser.parse_args()
    try:
        data = read_document(args.input)
        baseline = read_document(args.baseline) if args.baseline else None
        result = validate(data, baseline)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        # Exclusive creation protects earlier validation evidence and source files.
        with args.output.open("x", encoding="utf-8") as output:
            output.write(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({key: result[key] for key in ("status", "shotCount", "actualDurationSec", "targetDurationSec", "durationPass")}, ensure_ascii=False))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
