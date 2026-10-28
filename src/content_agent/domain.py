"""Validation, exact money arithmetic, and the authoritative task state."""

from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from importlib.resources import files
from typing import Any, Callable

Clock = Callable[[], datetime]


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def iso(value: datetime) -> str:
    return value.isoformat(timespec="seconds")


def parse_time(value: str) -> datetime:
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError("时间必须包含时区，例如 2026-10-29T18:00:00+08:00")
    return result


def digest(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def load_data(name: str) -> Any:
    return json.loads(files("content_agent").joinpath("data", name).read_text(encoding="utf-8"))


def validate_request(raw: Any) -> tuple[dict, list[str], list[str]]:
    if not isinstance(raw, dict):
        return {}, [], ["输入必须是 JSON 对象"]
    missing = [key for key in ("topic", "budget", "deadline") if raw.get(key) in (None, "")]
    errors: list[str] = []
    result: dict[str, Any] = {}
    if "topic" not in missing:
        if not isinstance(raw["topic"], str) or not raw["topic"].strip() or len(raw["topic"]) > 200:
            errors.append("topic 必须是 1–200 字符的非空字符串")
        else:
            result["topic"] = raw["topic"].strip()
    if "budget" not in missing:
        try:
            if isinstance(raw["budget"], bool):
                raise ValueError
            amount = Decimal(str(raw["budget"]))
            if not amount.is_finite() or amount < 0 or amount > 1_000_000 or amount * 100 != (amount * 100).to_integral_value():
                raise ValueError
            result["budget_cents"] = int(amount * 100)
        except (ValueError, InvalidOperation):
            errors.append("budget 必须是 0–1000000 之间、最多两位小数的有限数字")
    if "deadline" not in missing:
        try:
            result["deadline"] = iso(parse_time(raw["deadline"]).astimezone(timezone.utc))
        except (ValueError, TypeError, AttributeError):
            errors.append("deadline 必须是带时区的 ISO 8601 时间")
    preference = raw.get("preferred_variant", "premium")
    if preference not in ("premium", "standard", "lean"):
        errors.append("preferred_variant 必须是 premium、standard 或 lean")
    result["preferred_variant"] = preference
    return result, missing, errors


def new_state(request: dict, request_id: str, clock: Clock, faults: dict | None = None) -> dict:
    return {
        "schema_version": 1, "request_id": request_id, "request": request,
        "status": "running", "reason": None, "started_at": iso(clock()),
        "elapsed_minutes": 0, "materials": {}, "searches": {}, "quotes": {},
        "scripts": {}, "selected_variant": None, "ledger": [], "events": [],
        "history": [], "cache": {}, "saved_plan": None, "total_decisions": 0,
        "run_count": 0, "faults": faults or {},
        "steps": {
            "materials": {"status": "pending", "depends_on": []},
            "estimate": {"status": "pending", "depends_on": []},
            "script": {"status": "pending", "depends_on": ["materials", "estimate"]},
            "save": {"status": "pending", "depends_on": ["script", "estimate"]},
        },
    }


def occupied_cents(state: dict) -> int:
    return sum(entry["cents"] for entry in state["ledger"])


def effective_now(state: dict, clock: Clock) -> datetime:
    simulated = parse_time(state["started_at"]) + timedelta(minutes=state["elapsed_minutes"])
    return max(clock(), simulated)


def quote(state: dict, variant: str, catalog: dict, clock: Clock) -> dict:
    config = catalog["variants"][variant]
    existing = variant in state["scripts"]
    script_cents = 0 if existing else config["script_cents"]
    script_minutes = 0 if existing else config["script_minutes"]
    total = occupied_cents(state) + script_cents + config["production_cents"]
    remaining_minutes = script_minutes + config["production_minutes"] + catalog["save_minutes"]
    ready = effective_now(state, clock) + timedelta(minutes=remaining_minutes)
    deadline = parse_time(state["request"]["deadline"])
    gap = max(0, total - state["request"]["budget_cents"])
    late = max(0, math.ceil((ready - deadline).total_seconds() / 60))
    return {
        "variant": variant, "total_cents": total, "spent_cents": occupied_cents(state),
        "currency": "SIM", "total_units": total / 100, "budget_units": state["request"]["budget_cents"] / 100,
        "budget_gap_units": gap / 100,
        "script_cents": script_cents, "production_cents": config["production_cents"],
        "remaining_minutes": remaining_minutes, "ready_by": iso(ready),
        "budget_gap_cents": gap, "deadline_gap_minutes": late,
        "within_budget": gap == 0, "within_deadline": ready <= deadline,
        "feasible": gap == 0 and ready <= deadline,
    }
