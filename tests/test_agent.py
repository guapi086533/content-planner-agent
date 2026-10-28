from __future__ import annotations

import copy
import json
import tempfile
import unittest
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

from content_agent.agent import run_agent
from content_agent.domain import digest, load_data, new_state, parse_time, quote, validate_request
from content_agent.models import Decision, ModelError, ModelProtocolError, OfflineModel
from content_agent.storage import Store, StoreError

NOW = parse_time("2026-10-28T10:00:00+08:00")
REQUEST = {"topic": "校园秋日短视频挑战", "budget": 20, "deadline": "2026-10-28T18:00:00+08:00"}


def decision(tool, **args):
    return Decision(tool, {**args, "reason": "测试指定的公开动作依据"})


class SequenceModel:
    mode, name = "offline", "test-sequence"

    def __init__(self, actions):
        self.actions = iter(actions)

    def decide(self, state, context):
        result = next(self.actions)
        if isinstance(result, Exception):
            raise result
        return result


class NeverModel:
    mode, name = "offline", "must-not-be-called"

    def decide(self, state, context):
        raise AssertionError("不应调用模型")


class AgentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "state.sqlite3"
        self.store = Store(self.path)

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def run_case(self, *, budget=20, model=None, **kwargs):
        return run_agent({**REQUEST, "budget": budget}, model or OfflineModel(), self.store, clock=lambda: NOW, **kwargs)

    def test_normal_completes_with_exact_ledger(self):
        actual_event_time = NOW + timedelta(days=1)
        with patch("content_agent.agent.utcnow", return_value=actual_event_time):
            result = self.run_case()
        self.assertTrue(all(parse_time(e["observed_at"]) == actual_event_time for e in result["trace"]))
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["cost"]["total_units"], 12)
        self.assertEqual(result["cost"]["incurred_units"], 2)
        self.assertEqual(result["cost"]["reserved_units"], 10)
        self.assertTrue(all(s["status"] == "succeeded" for s in result["steps"].values()))
        self.assertEqual(result["saved_plan"]["execution_plan"][-2]["status"], "planned")
        self.assertEqual(self.store.db.execute("SELECT count(*) FROM plans").fetchone()[0], 1)

    def test_budget_12_to_8_changes_actions(self):
        result = self.run_case(budget=10)
        estimates = [e for e in result["trace"] if e.get("tool") == "estimate_cost"]
        self.assertEqual([(e["parameters"]["variant"], e["observation"]["total_cents"]) for e in estimates], [("premium", 1200), ("standard", 800)])
        self.assertEqual(estimates[0]["observation"]["status"], "rejected")
        self.assertEqual(result["cost"]["total_units"], 8)
        self.assertNotIn("premium", result["scripts"])

    def test_low_budget_selects_lean(self):
        result = self.run_case(budget=5)
        self.assertEqual(result["selected_variant"], "lean")
        self.assertEqual(result["cost"]["total_units"], 4)

    def test_no_affordable_option_has_gap_and_no_false_save(self):
        result = self.run_case(budget=3)
        self.assertEqual(result["status"], "incomplete")
        self.assertEqual(result["reason"]["code"], "NO_FEASIBLE_PLAN")
        self.assertEqual(min(q["budget_gap_cents"] for q in result["reason"]["observed_gaps"]), 100)
        self.assertIsNone(result["saved_plan"])
        self.assertEqual(result["steps"]["estimate"]["status"], "blocked")
        self.assertEqual(result["cost"]["total_units"], 0)

    def test_missing_budget_does_not_call_model(self):
        raw = {k: v for k, v in REQUEST.items() if k != "budget"}
        result = run_agent(raw, NeverModel(), self.store, clock=lambda: NOW)
        self.assertEqual(result["status"], "needs_input")
        self.assertEqual(result["reason"]["missing_fields"], ["budget"])
        self.assertEqual(result["trace"], [])

    def test_missing_deadline_does_not_call_model(self):
        raw = {k: v for k, v in REQUEST.items() if k != "deadline"}
        result = run_agent(raw, NeverModel(), self.store, clock=lambda: NOW)
        self.assertEqual(result["reason"]["missing_fields"], ["deadline"])
        self.assertEqual(result["total_decisions"], 0)

    def test_input_validation_rejects_bad_money(self):
        for budget in (True, -1, "NaN", "Infinity", "1.001", 1000001, [], {}):
            with self.subTest(budget=budget):
                result = self.run_case(budget=budget, model=NeverModel())
                self.assertEqual(result["status"], "invalid_input")

    def test_zero_budget_is_valid_but_not_feasible(self):
        result = self.run_case(budget=0)
        self.assertEqual(result["status"], "incomplete")
        self.assertEqual(result["reason"]["code"], "NO_FEASIBLE_PLAN")

    def test_validation_rejects_bad_dates_and_topic(self):
        for patch in ({"deadline": "2026-10-28T18:00:00"}, {"deadline": "tomorrow"}, {"topic": "   "}, {"topic": 4}, {"preferred_variant": "free"}):
            with self.subTest(patch=patch):
                result = run_agent({**REQUEST, **patch}, NeverModel(), self.store, clock=lambda: NOW)
                self.assertEqual(result["status"], "invalid_input")

    def test_non_object_input_is_rejected(self):
        result = run_agent([], NeverModel(), self.store, clock=lambda: NOW)
        self.assertEqual(result["status"], "invalid_input")

    def test_primary_failure_switches_source(self):
        result = self.run_case(faults={"once": {"search_materials:primary": 1}})
        searches = [e for e in result["trace"] if e.get("tool") == "search_materials"]
        self.assertEqual([e["parameters"]["source"] for e in searches], ["primary", "archive"])
        self.assertEqual(searches[0]["observation"]["status"], "error")
        self.assertEqual(result["status"], "completed")
        self.assertTrue(all(m["source"] == "archive" for m in result["materials"]))

    def test_partial_results_are_merged_and_retained(self):
        result = self.run_case(faults={"partial_sources": ["primary"]})
        searches = [e for e in result["trace"] if e.get("tool") == "search_materials"]
        self.assertEqual(searches[0]["observation"]["status"], "partial")
        first = searches[0]["observation"]["materials"][0]["id"]
        self.assertIn(first, result["saved_plan"]["material_ids"])
        self.assertEqual(len(result["materials"]), 3)
        self.assertEqual(result["status"], "completed")

    def test_script_failure_retries_only_failed_action(self):
        result = self.run_case(budget=10, faults={"once": {"generate_script": 1}})
        self.assertEqual(result["status"], "completed")
        self.assertEqual(sum(e.get("tool") == "search_materials" for e in result["trace"]), 1)
        scripts = [e for e in result["trace"] if e.get("tool") == "generate_script"]
        self.assertEqual([e["observation"]["status"] for e in scripts], ["error", "ok"])
        self.assertEqual(result["cost"]["total_units"], 8)

    def test_persistent_failure_never_marks_script_success(self):
        result = self.run_case(faults={"always": ["generate_script"]})
        self.assertEqual(result["status"], "incomplete")
        self.assertEqual(result["steps"]["script"]["status"], "failed")
        self.assertEqual(result["steps"]["materials"]["status"], "succeeded")
        self.assertIsNone(result["saved_plan"])
        self.assertEqual(result["cost"]["total_units"], 0)

    def test_unrelated_materials_are_not_fabricated(self):
        result = run_agent({**REQUEST, "topic": "深海矿业设备推广"}, OfflineModel(), self.store, clock=lambda: NOW)
        self.assertEqual(result["reason"]["code"], "NO_MATERIALS")
        self.assertEqual(result["materials"], [])
        self.assertEqual(result["scripts"], {})

    def test_duplicate_execution_does_not_call_model_or_charge(self):
        first = self.run_case()
        second = self.run_case(model=NeverModel())
        self.assertTrue(second["replayed"])
        self.assertEqual(first["trace"], second["trace"])
        self.assertEqual(second["cost"], first["cost"])
        self.assertEqual(self.store.db.execute("SELECT count(*) FROM plans").fetchone()[0], 1)

    def test_completed_request_stays_replayed_even_with_resume(self):
        self.run_case()
        result = self.run_case(resume=True, model=NeverModel())
        self.assertTrue(result["replayed"])
        self.assertEqual(result["run_count"], 1)

    def test_repeated_incomplete_does_not_implicitly_resume(self):
        first = self.run_case(max_steps=1)
        second = self.run_case(model=NeverModel())
        self.assertEqual(second["reason"]["code"], "STEP_LIMIT")
        self.assertTrue(second["replayed"])
        self.assertEqual(second["total_decisions"], first["total_decisions"])

    def test_save_failure_resume_keeps_materials_and_script(self):
        first = self.run_case(budget=10, max_steps=5, faults={"once": {"save_plan": 1}})
        self.assertEqual(first["status"], "incomplete")
        self.assertEqual(first["steps"]["save"]["status"], "failed")
        self.assertEqual(first["cost"]["total_units"], 1)
        self.store.close()
        self.store = Store(self.path)
        second = self.run_case(budget=10, resume=True)
        new_events = second["trace"][len(first["trace"]):]
        self.assertEqual([e["tool"] for e in new_events], ["save_plan"])
        self.assertEqual(first["scripts"], second["scripts"])
        self.assertEqual(first["materials"], second["materials"])
        self.assertEqual(second["cost"]["total_units"], 8)
        self.assertEqual(second["run_count"], 2)

    def test_explicit_id_rejects_different_input(self):
        self.run_case(request_id="same-id")
        result = self.run_case(budget=10, request_id="same-id", model=NeverModel())
        self.assertEqual(result["reason"]["code"], "ID_CONFLICT")
        self.assertIsNone(result["saved_plan"])

    def test_deadline_changes_variant(self):
        raw = {**REQUEST, "deadline": (NOW + timedelta(minutes=20)).isoformat()}
        result = run_agent(raw, OfflineModel(), self.store, clock=lambda: NOW)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["selected_variant"], "lean")
        self.assertEqual(parse_time(result["saved_plan"]["projected_ready_by"]), NOW + timedelta(minutes=20))

    def test_dependency_time_consumption_requires_reestimate(self):
        raw = {**REQUEST, "deadline": (NOW + timedelta(minutes=19)).isoformat()}
        result = run_agent(raw, OfflineModel(), self.store, clock=lambda: NOW)
        self.assertEqual(result["status"], "incomplete")
        self.assertTrue(any(e.get("observation", {}).get("code") == "CONSTRAINT_CHANGED" for e in result["trace"]))
        self.assertIsNone(result["saved_plan"])

    def test_past_deadline_calls_no_tools(self):
        raw = {**REQUEST, "deadline": (NOW - timedelta(seconds=1)).isoformat()}
        result = run_agent(raw, NeverModel(), self.store, clock=lambda: NOW)
        self.assertEqual(result["reason"]["code"], "DEADLINE_EXCEEDED")
        self.assertEqual(result["trace"], [])

    def test_model_cannot_save_without_dependencies(self):
        model = SequenceModel([decision("save_plan", variant="premium"), decision("finish", code="OTHER")])
        result = self.run_case(model=model)
        self.assertEqual(result["trace"][0]["observation"]["code"], "DEPENDENCY_NOT_MET")
        self.assertEqual(result["steps"]["save"]["status"], "failed")
        self.assertIsNone(result["saved_plan"])

    def test_model_cannot_generate_over_budget(self):
        model = SequenceModel([decision("estimate_cost", variant="premium"), decision("generate_script", variant="premium", material_ids=["campus-01", "campus-02"], angle="校园"), decision("finish", code="OTHER")])
        result = self.run_case(budget=10, model=model)
        self.assertEqual(result["trace"][1]["observation"]["code"], "DEPENDENCY_NOT_MET")
        self.assertEqual(result["cost"]["total_units"], 0)

    def test_unknown_tool_and_extra_parameters_are_rejected(self):
        model = SequenceModel([decision("shell_exec", command="whoami"), decision("save_plan", variant="standard", path="outside"), decision("finish", code="OTHER")])
        result = self.run_case(model=model)
        self.assertEqual([e["observation"].get("code") for e in result["trace"][:2]], ["UNKNOWN_TOOL", "INVALID_ARGUMENTS"])

    def test_duplicate_script_generation_is_free_and_immutable(self):
        script = decision("generate_script", variant="standard", material_ids=["campus-01"], angle="校园生活")
        model = SequenceModel([decision("estimate_cost", variant="standard"), decision("search_materials", query=REQUEST["topic"], source="primary"), script, copy.deepcopy(script), decision("save_plan", variant="standard")])
        result = self.run_case(budget=10, model=model)
        self.assertEqual(result["status"], "completed")
        self.assertTrue(result["trace"][3]["observation"]["cached"])
        self.assertEqual(result["elapsed_simulated_minutes"], 7)
        self.assertEqual(result["cost"]["total_units"], 8)

    def test_sunk_cost_is_included_when_switching_variants(self):
        model = SequenceModel([
            decision("estimate_cost", variant="premium"), decision("search_materials", query=REQUEST["topic"], source="primary"),
            decision("generate_script", variant="premium", material_ids=["campus-01", "campus-02"], angle="校园"),
            decision("estimate_cost", variant="standard"), decision("generate_script", variant="standard", material_ids=["campus-01"], angle="校园"),
            decision("save_plan", variant="premium"), decision("finish", code="OTHER")])
        result = self.run_case(budget=12, model=model)
        self.assertEqual(result["trace"][3]["observation"]["total_cents"], 1000)
        self.assertEqual(result["trace"][5]["observation"]["code"], "CONSTRAINT_CHANGED")
        self.assertEqual(result["trace"][5]["observation"]["quote"]["total_cents"], 1300)
        self.assertEqual(result["cost"]["total_units"], 3)
        self.assertEqual(set(result["scripts"]), {"premium", "standard"})
        self.assertIsNone(result["saved_plan"])

    def test_fabricated_material_id_is_rejected(self):
        model = SequenceModel([decision("estimate_cost", variant="premium"), decision("generate_script", variant="premium", material_ids=["fake1", "fake2"], angle="校园"), decision("finish", code="OTHER")])
        result = self.run_case(model=model)
        self.assertEqual(result["trace"][1]["observation"]["code"], "MATERIALS_INSUFFICIENT")
        self.assertEqual(result["scripts"], {})

    def test_protocol_errors_are_bounded(self):
        model = SequenceModel([ModelProtocolError("MODEL_PROTOCOL_ERROR", "bad response")] * 3)
        result = self.run_case(model=model, max_steps=3)
        self.assertEqual(result["total_decisions"], 3)
        self.assertEqual(result["reason"]["code"], "STEP_LIMIT")
        self.assertTrue(all(e["kind"] == "model_error" for e in result["trace"]))

    def test_live_model_error_does_not_switch_to_mock(self):
        model = SequenceModel([ModelError("MODEL_UNAVAILABLE", "HTTP 403", 403)])
        model.mode = "live"
        result = self.run_case(model=model)
        self.assertEqual(result["status"], "incomplete")
        self.assertEqual(result["reason"]["http_status"], 403)
        self.assertEqual(result["model"]["mode"], "live")
        self.assertEqual(result["cost"]["total_units"], 0)

    def test_active_lease_blocks_concurrent_execution(self):
        request, _, _ = validate_request(REQUEST)
        initial = new_state(request, "locked", lambda: NOW)
        self.store.acquire(initial, digest(request), False)
        another = Store(self.path)
        try:
            result = run_agent(REQUEST, NeverModel(), another, request_id="locked", clock=lambda: NOW)
            self.assertEqual(result["reason"]["code"], "JOB_BUSY")
        finally:
            another.close()
            self.store.release("locked")

    def test_interrupted_job_returns_explicit_incomplete(self):
        request, _, _ = validate_request(REQUEST)
        initial = new_state(request, "interrupted", lambda: NOW)
        self.store.acquire(initial, digest(request), False)
        self.store.release("interrupted")
        result = run_agent(REQUEST, NeverModel(), self.store, request_id="interrupted", clock=lambda: NOW)
        self.assertEqual(result["reason"]["code"], "INTERRUPTED")
        self.assertEqual(result["status"], "incomplete")

    def test_transaction_rolls_back_plan_and_state_together(self):
        request, _, _ = validate_request(REQUEST)
        state = new_state(request, "atomic", lambda: NOW)
        self.store.acquire(state, digest(request), False)
        state["saved_plan"] = {"id": "fake", "bad": object()}
        state["status"] = "completed"
        with self.assertRaises(TypeError):
            self.store.checkpoint(state)
        persisted = json.loads(self.store.db.execute("SELECT state FROM jobs WHERE id='atomic'").fetchone()[0])
        self.assertEqual(persisted["status"], "running")
        self.assertEqual(self.store.db.execute("SELECT count(*) FROM plans").fetchone()[0], 0)
        self.store.release("atomic")

    def test_step_limit_bounds_tools_and_can_resume(self):
        result = self.run_case(max_steps=1)
        self.assertEqual(len(result["trace"]), 1)
        self.assertEqual(result["reason"]["code"], "STEP_LIMIT")
        resumed = self.run_case(resume=True)
        self.assertEqual(resumed["status"], "completed")

    def test_invalid_step_limits_are_rejected(self):
        for limit in (0, 65):
            with self.assertRaises(ValueError):
                self.run_case(max_steps=limit)
