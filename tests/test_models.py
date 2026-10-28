from __future__ import annotations

import io
import json
import os
import unittest
import urllib.error
from unittest.mock import patch

from content_agent.agent import run_agent
from content_agent.domain import load_data, new_state, parse_time, validate_request
from content_agent.models import ChatModel, ModelError, ModelProtocolError
from content_agent.storage import Store

NOW = parse_time("2026-10-28T10:00:00+08:00")
RAW = {"topic": "校园秋日短视频挑战", "budget": 10, "deadline": "2026-10-28T18:00:00+08:00"}


def api_response(name="estimate_cost", **args):
    return {"id": "test-http-response", "choices": [{"finish_reason": "tool_calls", "message": {
        "role": "assistant", "content": None, "reasoning_content": "must never persist hidden reasoning",
        "tool_calls": [{"id": "call-test", "type": "function", "function": {"name": name, "arguments": json.dumps({**args, "reason": "基于上次工具结果选择此动作"})}}],
    }}], "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}}


class Response(io.BytesIO):
    def __init__(self, value):
        super().__init__(json.dumps(value).encode("utf-8"))


class ModelAdapterTests(unittest.TestCase):
    def setUp(self):
        request, _, _ = validate_request(RAW)
        self.state = new_state(request, "test", lambda: NOW)
        self.context = {"catalog": load_data("catalog.json")}
        self.model = ChatModel(base_url="https://example.com/v1", model="test-model", key="TEST-NOT-A-REAL-KEY")

    @patch("urllib.request.urlopen")
    def test_native_tool_call_is_parsed_and_thinking_not_stored(self, call):
        call.return_value = Response(api_response(variant="premium"))
        action = self.model.decide(self.state, self.context)
        self.assertEqual(action.tool, "estimate_cost")
        self.assertEqual(action.arguments["variant"], "premium")
        self.assertNotIn("reasoning_content", action.message)
        self.assertEqual(action.usage["total_tokens"], 30)
        payload = json.loads(call.call_args.args[0].data)
        self.assertFalse(payload["parallel_tool_calls"])
        self.assertEqual(payload["tool_choice"], "auto")
        self.assertNotIn("TEST-NOT-A-REAL-KEY", json.dumps(payload))

    @patch("urllib.request.urlopen")
    def test_react_feedback_is_sent_to_subsequent_model_call(self, call):
        responses = [api_response(variant="premium"), api_response(variant="standard"),
                     api_response("search_materials", query=RAW["topic"], source="primary"),
                     api_response("generate_script", variant="standard", material_ids=["campus-01"], angle="校园生活"),
                     api_response("save_plan", variant="standard")]
        call.side_effect = [Response(item) for item in responses]
        store = Store(":memory:")
        try:
            result = run_agent(RAW, self.model, store, clock=lambda: NOW)
        finally:
            store.close()
        self.assertEqual(result["status"], "completed")
        second_payload = json.loads(call.call_args_list[1].args[0].data)
        tool_messages = [m for m in second_payload["messages"] if m["role"] == "tool"]
        observation = json.loads(tool_messages[0]["content"])
        self.assertEqual(observation["status"], "rejected")
        self.assertEqual(observation["budget_gap_cents"], 200)
        self.assertEqual(tool_messages[0]["tool_call_id"], "call-test")
        # These responses are test doubles, not real-model execution evidence.

    @patch("urllib.request.urlopen")
    def test_multiple_tool_calls_are_rejected_without_execution(self, call):
        value = api_response(variant="premium")
        value["choices"][0]["message"]["tool_calls"] *= 2
        call.return_value = Response(value)
        with self.assertRaises(ModelProtocolError):
            self.model.decide(self.state, self.context)

    @patch("urllib.request.urlopen")
    def test_text_only_response_is_not_treated_as_completed(self, call):
        call.return_value = Response({"choices": [{"message": {"content": "已完成并保存"}}]})
        with self.assertRaises(ModelProtocolError):
            self.model.decide(self.state, self.context)

    @patch("urllib.request.urlopen")
    def test_truncated_response_is_rejected(self, call):
        value = api_response(variant="premium")
        value["choices"][0]["finish_reason"] = "length"
        call.return_value = Response(value)
        with self.assertRaises(ModelProtocolError):
            self.model.decide(self.state, self.context)

    @patch("urllib.request.urlopen")
    def test_malformed_json_arguments_are_rejected(self, call):
        value = api_response(variant="premium")
        value["choices"][0]["message"]["tool_calls"][0]["function"]["arguments"] = "not json"
        call.return_value = Response(value)
        with self.assertRaises(ModelProtocolError):
            self.model.decide(self.state, self.context)

    @patch("urllib.request.urlopen")
    def test_nonfinite_json_arguments_are_rejected_before_checkpoint(self, call):
        value = api_response(variant="premium")
        value["choices"][0]["message"]["tool_calls"][0]["function"]["arguments"] = '{"variant":NaN,"reason":"test"}'
        call.return_value = Response(value)
        with self.assertRaises(ModelProtocolError):
            self.model.decide(self.state, self.context)

    @patch("urllib.request.urlopen")
    def test_http_error_does_not_leak_response_or_key(self, call):
        body = io.BytesIO(json.dumps({"error": {"code": "TEST-NOT-A-REAL-KEY", "message": "sensitive response"}}).encode())
        call.side_effect = urllib.error.HTTPError("https://example.com/v1", 401, "unauthorized", {}, body)
        with self.assertRaises(ModelError) as caught:
            self.model.decide(self.state, self.context)
        self.assertNotIn("TEST-NOT-A-REAL-KEY", str(caught.exception))
        self.assertNotIn("sensitive response", str(caught.exception))
        self.assertEqual(caught.exception.http_status, 401)
        self.assertEqual(call.call_count, 1)

    @patch("urllib.request.urlopen", side_effect=TimeoutError("secret text"))
    def test_network_failure_is_not_retried(self, call):
        with self.assertRaises(ModelError) as caught:
            self.model.decide(self.state, self.context)
        self.assertNotIn("secret text", str(caught.exception))
        self.assertEqual(call.call_count, 1)

    @patch.dict(os.environ, {}, clear=True)
    def test_missing_key_is_explicit(self):
        model = ChatModel()
        with self.assertRaises(ModelError) as caught:
            model.decide(self.state, self.context)
        self.assertEqual(caught.exception.code, "MISSING_API_KEY")

    def test_unsafe_endpoint_is_rejected_and_local_endpoint_allowed(self):
        for url in ("http://example.com/v1", "https://user:pass@example.com/v1", "https://example.com/v1?key=secret"):
            with self.subTest(url=url), self.assertRaises(ModelError):
                ChatModel(base_url=url)
        self.assertEqual(ChatModel(base_url="http://localhost:8080/v1").base_url, "http://localhost:8080/v1")

    @patch("urllib.request.urlopen")
    def test_dashscope_uses_supported_token_and_thinking_settings(self, call):
        model = ChatModel(key="TEST", base_url="https://dashscope.aliyuncs.com/compatible-mode/v1")
        call.return_value = Response(api_response(variant="premium"))
        model.decide(self.state, self.context)
        payload = json.loads(call.call_args.args[0].data)
        self.assertFalse(payload["enable_thinking"])
        self.assertEqual(payload["max_tokens"], 1400)
        self.assertNotIn("max_completion_tokens", payload)
