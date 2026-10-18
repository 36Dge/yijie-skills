"""Local, explicit-input TikTok report arithmetic. Python 3.10+, standard library."""
import argparse
import datetime as dt
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
from pathlib import Path
import re
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

METRICS = ("gmv", "orders", "paying_buyers", "visitors", "refund_orders")


def text(value, field):
    if not isinstance(value, str) or not value.strip() or len(value) > 500:
        raise ValueError(f"missing/invalid {field}")
    return value


def date(value, field):
    value = text(value, field)
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError(f"invalid date: {field}")
    return dt.date.fromisoformat(value)


def number(value, field):
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (str, int, Decimal)):
        raise ValueError(f"invalid decimal: {field}")
    raw = str(value)
    if not re.fullmatch(r"\d{1,12}(?:\.\d{1,6})?", raw):
        raise ValueError(f"expected nonnegative decimal up to 6 places: {field}")
    result = Decimal(raw)
    if field != "gmv" and result != result.to_integral_value():
        raise ValueError(f"count must be integer: {field}")
    return result


def display(value):
    if value is None:
        return None
    return format(value, "f")


def ratio(numerator, denominator, percent=False):
    if numerator is None or denominator is None:
        return {"value": None, "reason": "missing_input"}
    if denominator == 0:
        return {"value": None, "reason": "zero_denominator"}
    value = numerator / denominator * (100 if percent else 1)
    return {"value": display(value.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)), "reason": None}


def period(value, label):
    if not isinstance(value, dict):
        raise ValueError(f"missing/invalid {label}")
    for field in ("timezone", "currency", "basis"):
        text(value.get(field), f"{label}.{field}")
    if not re.fullmatch(r"[A-Z]{3}", value["currency"]):
        raise ValueError("currency must be explicit uppercase three-letter code")
    try:
        ZoneInfo(value["timezone"])
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise ValueError("timezone must be a known IANA timezone") from exc
    start, end = date(value.get("start"), "start"), date(value.get("end"), "end")
    available = date(value.get("data_available_date"), "data_available_date")
    if end < start or (end - start).days > 365 or end > available:
        raise ValueError("period must be complete, ordered, and no longer than 366 days")
    source_metrics = value.get("metrics")
    if not isinstance(source_metrics, dict) or set(source_metrics) != set(METRICS):
        raise ValueError("metrics must explicitly contain gmv/orders/paying_buyers/visitors/refund_orders; use null for missing")
    metrics = {key: number(source_metrics[key], key) for key in METRICS}
    # These are arithmetic constraints on the declared same-cohort input, not proofs of business definitions.
    if metrics["paying_buyers"] is not None and metrics["visitors"] is not None and metrics["paying_buyers"] > metrics["visitors"]:
        raise ValueError("paying_buyers exceeds visitors; confirm aligned scope before conversion")
    refund_basis = value.get("refund_basis", "unknown")
    if refund_basis not in ("same_order_cohort", "refund_event_date", "unknown"):
        raise ValueError("unknown refund_basis")
    refund_ratio = ({"value": None, "reason": "refund_cohort_unconfirmed"}
                    if refund_basis != "same_order_cohort" else ratio(metrics["refund_orders"], metrics["orders"], True))
    if refund_basis == "same_order_cohort" and metrics["refund_orders"] is not None and metrics["orders"] is not None and metrics["refund_orders"] > metrics["orders"]:
        raise ValueError("refund_orders exceeds orders in declared same cohort")
    result = {"metadata": {key: value[key] for key in ("start", "end", "timezone", "currency", "basis", "data_available_date")},
              "refund_basis": refund_basis, "days": (end - start).days + 1, "metrics": {key: display(val) for key, val in metrics.items()},
              "missing": [key for key, val in metrics.items() if val is None],
              "derived": {"order_average_value": ratio(metrics["gmv"], metrics["orders"]),
                          "paying_buyer_conversion_percent": ratio(metrics["paying_buyers"], metrics["visitors"], True),
                          "refund_order_percent": refund_ratio}}
    return result, metrics


def analyze(value):
    if not isinstance(value, dict) or set(value) - {"shop_id", "source", "current", "previous", "notes"}:
        raise ValueError("expected one shop report with source/current and optional previous/notes")
    shop, source = text(value.get("shop_id"), "shop_id"), text(value.get("source"), "source")
    if "notes" in value:
        text(value["notes"], "notes")
    current, c = period(value.get("current"), "current")
    result = {"schema_version": 1, "shop_id": shop, "source": source, "data_mode": "user_provided_report",
              "current": current, "comparison": {"available": False, "reasons": ["no_previous_period"]},
              "rounding": "Decimal; ratios/percentages ROUND_HALF_UP to 4 decimal places; no missing-to-zero substitution",
              "limitations": ["No remote shop query or authorization verification", "Input basis/source are user declarations; no causal or revenue guarantee"]}
    if value.get("previous") is None:
        return result
    previous, p = period(value["previous"], "previous")
    result["previous"] = previous
    reasons = [key + "_differs" for key in ("currency", "timezone", "basis") if current["metadata"][key] != previous["metadata"][key]]
    if current["days"] != previous["days"]:
        reasons.append("duration_differs")
    if previous["metadata"]["end"] >= current["metadata"]["start"]:
        reasons.append("previous_must_end_before_current")
    result["comparison"] = {"available": not reasons, "reasons": reasons}
    if not reasons:
        result["comparison"]["metrics"] = {}
        for key in METRICS:
            if key == "refund_orders" and (current["refund_basis"] == "unknown" or current["refund_basis"] != previous["refund_basis"]):
                result["comparison"]["metrics"][key] = {"difference": None, "change_percent": {"value": None, "reason": "refund_basis_unconfirmed_or_differs"}}
                continue
            difference = c[key] - p[key] if c[key] is not None and p[key] is not None else None
            result["comparison"]["metrics"][key] = {"difference": display(difference), "change_percent": ratio(difference, p[key], True)}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    source = Path(args.input)
    if source.stat().st_size > 2 * 1024 * 1024:
        raise ValueError("input exceeds 2 MiB")
    raw = source.read_bytes()
    value = json.loads(raw.decode("utf-8-sig"), parse_float=Decimal, parse_constant=lambda _: (_ for _ in ()).throw(ValueError("finite input required")))
    result = analyze(value)
    result["input_sha256"] = hashlib.sha256(raw).hexdigest()
    output = Path(args.output_dir)
    target = output.parent.resolve(strict=True) / output.name
    current = Path.cwd().resolve()
    if target == current or not target.is_relative_to(current):
        raise ValueError("output must be a new subdirectory of the current task workspace")
    target.mkdir()  # Existing paths fail; no input or earlier output is overwritten.
    with (target / "data.json").open("xb") as stream:
        stream.write(raw)
    with (target / "calculation.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"status": "complete", "directory": str(target), "comparable": result["comparison"]["available"]}))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError) as error:
        raise SystemExit("report not completed: " + str(error)) from None
