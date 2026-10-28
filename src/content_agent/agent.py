"""Bounded model -> tool -> observation loop, with checkpoints after each action."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict
import json

from .domain import Clock, digest, effective_now, iso, load_data, new_state, occupied_cents, parse_time, utcnow, validate_request
from .models import ModelError, ModelProtocolError
from .storage import Store, StoreError
from .tools import BusinessTools


def public_report(state: dict, replayed: bool = False) -> dict:
    selected = state["selected_variant"]
    budget = state["request"].get("budget_cents", 0)
    occupied = occupied_cents(state)
    return {
        "schema_version": state["schema_version"], "request_id": state["request_id"],
        "status": state["status"], "reason": state["reason"], "replayed": replayed,
        "request": state["request"], "model": state.get("model"), "run_count": state["run_count"],
        "total_decisions": state["total_decisions"], "selected_variant": selected,
        "steps": deepcopy(state["steps"]), "materials": list(state["materials"].values()),
        "scripts": deepcopy(state["scripts"]), "quotes": deepcopy(state["quotes"]),
        "cost": {"currency": "SIM", "budget_units": budget / 100, "total_units": occupied / 100,
                 "incurred_units": sum(e["cents"] for e in state["ledger"] if e["kind"] == "incurred") / 100,
                 "reserved_units": sum(e["cents"] for e in state["ledger"] if e["kind"] == "reserved") / 100,
                 "remaining_units": (budget - occupied) / 100, "ledger": deepcopy(state["ledger"])},
        "elapsed_simulated_minutes": state["elapsed_minutes"], "reference_started_at": state["started_at"],
        "saved_plan": deepcopy(state["saved_plan"]), "trace": deepcopy(state["events"]),
        "mock_boundary": "业务工具和费用均为合成模拟。offline 是规则策略，只验证工程流程；live 才调用外部模型，不保证效果。",
    }


def run_agent(raw: dict, model, store: Store, *, request_id: str | None = None, max_steps: int = 16,
              resume: bool = False, faults: dict | None = None, clock: Clock = utcnow) -> dict:
    if not 1 <= max_steps <= 64:
        raise ValueError("max_steps 必须是 1–64")
    request, missing, errors = validate_request(raw)
    fingerprint = digest(request)
    rid = request_id or "job-" + fingerprint[:16]
    state = new_state(request, rid, clock, faults)
    if missing or errors:
        state["status"] = "needs_input" if missing and not errors else "invalid_input"
        state["reason"] = {"code": "MISSING_FIELDS" if missing and not errors else "INVALID_INPUT", "missing_fields": missing, "errors": errors,
                           "message": "请补充必填字段或修正输入；未调用模型及业务工具"}
        return public_report(state)
    try:
        state, replayed = store.acquire(state, fingerprint, resume)
    except StoreError as exc:
        state["status"], state["reason"] = "incomplete", {"code": exc.code, "message": str(exc)}
        return public_report(state)
    if replayed:
        return public_report(state, True)
    catalog = load_data("catalog.json")
    tools = BusinessTools(catalog, load_data("materials.json"), clock)
    state["run_count"] += 1
    state["status"], state["reason"] = "running", None
    state["model"] = {"mode": model.mode, "name": model.name}
    if hasattr(model, "base_url"):
        state["model"]["base_url"] = model.base_url
    store.checkpoint(state)
    try:
        for turn in range(max_steps):
            if effective_now(state, clock) >= parse_time(request["deadline"]):
                state["status"], state["reason"] = "incomplete", {"code": "DEADLINE_EXCEEDED", "message": "截止时间已到，保留已成功步骤"}
                break
            context = {"catalog": catalog, "steps_remaining": max_steps - turn,
                       "effective_now": iso(effective_now(state, clock)), "selected_variant": state["selected_variant"],
                       "materials": state["materials"], "quotes": state["quotes"], "scripts": state["scripts"],
                       "ledger": state["ledger"], "steps": state["steps"],
                       "recent_observations": state["events"][-6:], "request": request}
            state["total_decisions"] += 1
            try:
                decision = model.decide(state, context)
            except ModelProtocolError as exc:
                event = {"sequence": len(state["events"]) + 1, "run": state["run_count"], "kind": "model_error",
                         "decision_source": model.mode, "code": exc.code, "message": str(exc), "observed_at": iso(utcnow())}
                state["events"].append(event)
                state["history"].append({"role": "user", "content": str(exc) + "。请修正为一个工具调用。"})
                store.checkpoint(state)
                continue
            except ModelError as exc:
                state["status"], state["reason"] = "incomplete", {"code": exc.code, "message": str(exc), "http_status": exc.http_status}
                state["events"].append({"sequence": len(state["events"]) + 1, "run": state["run_count"], "kind": "model_error",
                                       "decision_source": model.mode, "observed_at": iso(utcnow()), **state["reason"]})
                break
            result = tools.execute(decision.tool, decision.arguments, state)
            state["events"].append({
                "sequence": len(state["events"]) + 1, "run": state["run_count"], "kind": "tool",
                "decision_source": model.mode, "model": model.name, "tool": decision.tool,
                "parameters": deepcopy(decision.arguments), "rationale": decision.arguments.get("reason", ""),
                "observation": deepcopy(result), "observed_at": iso(utcnow()),
                "response_id": decision.response_id, "usage": decision.usage,
            })
            if decision.message:
                state["history"].append(decision.message)
                state["history"].append({"role": "tool", "tool_call_id": decision.message["tool_calls"][0]["id"], "content": json.dumps(result, ensure_ascii=False)})
            else:
                # Offline/test decisions never masquerade as native model responses.
                state["history"].append({"role": "user", "content": json.dumps({"offline_action": asdict(decision), "observation": result}, ensure_ascii=False)})
            store.checkpoint(state)
            if state["status"] in ("completed", "incomplete"):
                break
        else:
            state["status"], state["reason"] = "incomplete", {"code": "STEP_LIMIT", "message": f"本轮达到 {max_steps} 次模型决策上限；未完成，可显式 --resume 续跑"}
        store.checkpoint(state)
        return public_report(state)
    finally:
        store.release(rid)
