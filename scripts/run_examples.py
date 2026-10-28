"""Regenerate real outputs from execution. No database or credentials are committed."""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from content_agent.agent import run_agent
from content_agent.cli import write_outputs
from content_agent.domain import parse_time, utcnow
from content_agent.models import ChatModel, OfflineModel
from content_agent.storage import Store

ROOT = Path(__file__).resolve().parents[1]
NOW = parse_time("2026-10-28T10:00:00+08:00")
BASE = {"topic": "校园秋日短视频挑战", "budget": 20, "deadline": "2026-10-28T18:00:00+08:00", "preferred_variant": "premium"}
CASES = {
    "normal": {"request": BASE, "expected": "completed", "cost": 12},
    "missing_budget": {"request": {k: v for k, v in BASE.items() if k != "budget"}, "expected": "needs_input", "cost": 0},
    "missing_deadline": {"request": {k: v for k, v in BASE.items() if k != "deadline"}, "expected": "needs_input", "cost": 0},
    "tool_failure": {"request": BASE, "faults": {"once": {"search_materials:primary": 1}}, "expected": "completed", "cost": 12},
    "budget_replan": {"request": {**BASE, "budget": 10}, "expected": "completed", "cost": 8},
    "budget_impossible": {"request": {**BASE, "budget": 3}, "expected": "incomplete", "cost": 0},
    "repeat": {"request": BASE, "repeat": True, "expected": "completed", "cost": 12},
    "partial_success": {"request": BASE, "faults": {"partial_sources": ["primary"]}, "expected": "completed", "cost": 12},
    "resume_save": {"request": {**BASE, "budget": 10}, "faults": {"once": {"save_plan": 1}}, "max_steps": 5, "resume": True, "expected": "completed", "cost": 8},
    "persistent_failure": {"request": BASE, "faults": {"always": ["generate_script"]}, "expected": "incomplete", "cost": 0},
    "no_materials": {"request": {**BASE, "topic": "深海矿业设备推广"}, "expected": "incomplete", "cost": 0},
    "deadline_replan": {"request": {**BASE, "deadline": "2026-10-28T10:20:00+08:00"}, "expected": "completed", "cost": 4},
    "deadline_impossible": {"request": {**BASE, "deadline": "2026-10-28T10:10:00+08:00"}, "expected": "incomplete", "cost": 0},
    "step_limit": {"request": BASE, "max_steps": 1, "expected": "incomplete", "cost": 0},
}


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["offline", "live"], default="offline")
    parser.add_argument("--cases", nargs="+", choices=list(CASES))
    args = parser.parse_args()
    names = args.cases or list(CASES)
    mode_root = ROOT / "examples" / args.mode
    mode_root.mkdir(parents=True, exist_ok=True)
    rows = []
    with tempfile.TemporaryDirectory(prefix="content-agent-examples-") as temporary:
        store = Store(Path(temporary) / "state.sqlite3")
        try:
            for name in names:
                case = CASES[name]
                destination = mode_root / name
                destination.mkdir(parents=True, exist_ok=True)
                write_json(destination / "input.json", case["request"])
                options = {"request_id": f"{args.mode}-{name}", "clock": lambda: NOW,
                           "faults": case.get("faults"), "max_steps": case.get("max_steps", 16)}
                write_json(destination / "options.json", {"reference_now": NOW.isoformat(), "mode": args.mode,
                           "faults": options["faults"], "max_steps": options["max_steps"], "repeat": case.get("repeat", False), "resume": case.get("resume", False)})
                model = OfflineModel() if args.mode == "offline" else ChatModel()
                result = run_agent(case["request"], model, store, **options)
                if case.get("repeat") or case.get("resume"):
                    write_outputs(result, destination / "first")
                    if case.get("resume"):
                        store.close()
                        store = Store(Path(temporary) / "state.sqlite3")
                        options.update(resume=True, max_steps=16)
                    result = run_agent(case["request"], model, store, **options)
                write_outputs(result, destination)
                passed = result["status"] == case["expected"] and result["cost"]["total_units"] == case["cost"]
                if args.mode == "offline":
                    assert passed, (name, result["status"], result["reason"])
                    if name == "repeat":
                        assert result["replayed"] and result["run_count"] == 1
                    if name == "resume_save":
                        assert result["run_count"] == 2 and result["trace"][-1]["tool"] == "save_plan"
                row = {"case": name, "expected_status": case["expected"], "actual_status": result["status"],
                       "total_units": result["cost"]["total_units"], "reason_code": (result.get("reason") or {}).get("code"),
                       "matches_expected_status_and_cost": passed, "decision_mode": args.mode,
                       "real_model_success_evidence": args.mode == "live" and result["status"] == "completed" and any(e.get("response_id") for e in result["trace"])}
                rows.append(row)
                print(json.dumps(row, ensure_ascii=False))
        finally:
            store.close()
    write_json(mode_root / "summary.json", {"generated_at": utcnow().isoformat(), "reference_now": NOW.isoformat(), "mode": args.mode, "cases": rows,
                                            "boundary": "offline 仅证明规则 Mock 与工程约束。live 出现 MODEL_UNAVAILABLE 时不构成真实决策成功证据。"})
    return 0 if all(row["matches_expected_status_and_cost"] for row in rows) else 2


if __name__ == "__main__":
    raise SystemExit(main())
