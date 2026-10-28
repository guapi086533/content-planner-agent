"""Inspect actual live traces for observation-dependent changes and retained state."""

import json
from pathlib import Path

from content_agent.domain import utcnow

ROOT = Path(__file__).resolve().parents[1]


def audit() -> dict:
    def report(name, first=False):
        directory = ROOT / "examples" / "live" / name
        if first:
            directory = directory / "first"
        return json.loads((directory / "result.json").read_text(encoding="utf-8"))

    normal = report("normal")
    budget = report("budget_replan")
    events = budget["trace"]
    premium = next((i for i, e in enumerate(events) if e.get("tool") == "estimate_cost" and e["observation"].get("variant") == "premium" and e["observation"]["status"] == "rejected" and e["observation"]["total_cents"] == 1200), None)
    standard = next((i for i, e in enumerate(events) if e.get("tool") == "estimate_cost" and e["observation"].get("variant") == "standard" and e["observation"]["status"] == "ok" and e["observation"]["total_cents"] == 800), None)
    repeated, original = report("repeat"), report("repeat", True)
    resumed, interrupted = report("resume_save"), report("resume_save", True)
    new_events = resumed["trace"][len(interrupted["trace"]):]
    partial = report("partial_success")
    partial_ids = {m["id"] for e in partial["trace"] if e.get("tool") == "search_materials" and e["observation"]["status"] == "partial" for m in e["observation"]["materials"]}
    failure = report("tool_failure")
    summary = json.loads((ROOT / "examples/live/summary.json").read_text(encoding="utf-8"))
    checks = {
        "all_14_status_and_cost_expectations": len(summary["cases"]) == 14 and all(c["matches_expected_status_and_cost"] for c in summary["cases"]),
        "normal_saved_premium_for_12": normal["status"] == "completed" and normal["selected_variant"] == "premium" and normal["cost"]["total_units"] == 12,
        "replan_observed_12_rejection_before_selecting_8": premium is not None and standard is not None and premium < standard and budget["status"] == "completed" and budget["selected_variant"] == "standard" and budget["cost"]["total_units"] == 8,
        "replan_has_native_model_response_ids": bool(events) and all(e.get("decision_source") == "live" and e.get("model") == "qwen3.8-27b" and e.get("response_id") for e in events),
        "injected_failure_visible_then_completed": failure["status"] == "completed" and any(e.get("observation", {}).get("status") == "error" for e in failure["trace"]),
        "repeat_does_not_add_calls_or_cost": repeated["replayed"] and repeated["trace"] == original["trace"] and repeated["cost"] == original["cost"] and repeated["run_count"] == 1,
        "resume_retains_successful_script_and_materials": resumed["status"] == "completed" and interrupted["status"] == "incomplete" and resumed["scripts"] == interrupted["scripts"] and resumed["materials"] == interrupted["materials"] and all(e.get("tool") not in ("generate_script", "search_materials") for e in new_events),
        "partial_materials_retained_in_saved_plan": bool(partial_ids) and bool(partial_ids & set((partial["saved_plan"] or {}).get("material_ids", []))),
    }
    corrected_root = ROOT / "examples/unit-clarification/live"
    corrected_summary = json.loads((corrected_root / "summary.json").read_text(encoding="utf-8"))
    corrected = json.loads((corrected_root / "budget_impossible/result.json").read_text(encoding="utf-8"))
    checks["unit_recheck_three_status_and_cost_expectations"] = len(corrected_summary["cases"]) == 3 and all(c["matches_expected_status_and_cost"] for c in corrected_summary["cases"])
    checks["unit_recheck_explains_3_sim_not_300_sim"] = "3 SIM" in corrected["reason"]["message"] and "300 SIM" not in corrected["reason"]["message"] and corrected["quotes"]["premium"]["budget_units"] == 3 and corrected["quotes"]["premium"]["total_units"] == 12
    responses = {}
    correction_responses = {}
    for path in [*(ROOT / "examples/live").rglob("result.json"), *corrected_root.rglob("result.json")]:
        value = json.loads(path.read_text(encoding="utf-8"))
        for event in value["trace"]:
            if event.get("response_id"):
                responses[event["response_id"]] = event.get("usage", {})
                if corrected_root in path.parents:
                    correction_responses[event["response_id"]] = event.get("usage", {})
    return {
        "checked_at": utcnow().isoformat(), "model": "qwen3.8-27b", "checks": checks,
        "passed": all(checks.values()), "unique_model_responses": len(responses),
        "usage_deduplicated_by_response_id": {key: sum(usage.get(key, 0) for usage in responses.values()) for key in ("prompt_tokens", "completion_tokens", "total_tokens")},
        "unit_recheck_unique_responses": len(correction_responses),
        "unit_recheck_tokens": sum(usage.get("total_tokens", 0) for usage in correction_responses.values()),
        "resume_new_actions": [e.get("tool", e["kind"]) for e in new_events],
        "scope": "首轮 14 场景及单位修正后 3 场景；调用外部真实模型，业务工具仍为合成工具，不代表泛化成功率。",
    }


if __name__ == "__main__":
    result = audit()
    (ROOT / "examples/verification/live-audit.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["passed"] else 1)
