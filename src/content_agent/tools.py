"""Synthetic business tools. Guards validate actions; they never choose the next action."""

from __future__ import annotations

from copy import deepcopy
from datetime import timedelta

from .domain import Clock, digest, effective_now, iso, occupied_cents, quote, utcnow


class ToolFailure(Exception):
    def __init__(self, code: str, message: str, retryable: bool = False, **details):
        self.result = {"status": "error", "code": code, "message": message, "retryable": retryable, **details}
        super().__init__(message)


def schema(name: str, description: str, properties: dict, required: list[str]) -> dict:
    properties = {**properties, "reason": {"type": "string", "description": "一句简短的公开决策依据，不要内部思维过程。"}}
    return {"type": "function", "function": {"name": name, "description": description, "parameters": {
        "type": "object", "properties": properties, "required": [*required, "reason"], "additionalProperties": False,
    }}}


VARIANT = {"type": "string", "enum": ["premium", "standard", "lean"]}
TOOL_SCHEMAS = [
    schema("search_materials", "检索合成素材；primary 与 archive 为独立来源。可能返回部分结果或错误，已找到素材保留。", {
        "query": {"type": "string"}, "source": {"type": "string", "enum": ["primary", "archive"]},
    }, ["query", "source"]),
    schema("estimate_cost", "估算方案全部费用及完成时间，包含已花费用；超预算/超时返回 rejected，可据结果改选方案。", {"variant": VARIANT}, ["variant"]),
    schema("generate_script", "用已找到的素材与创意角度生成本地模板脚本；须先取得该档位可行估算。成功扣脚本费用，失败免费。", {
        "variant": VARIANT, "material_ids": {"type": "array", "items": {"type": "string"}, "minItems": 1},
        "angle": {"type": "string", "description": "结合活动主题的创意切入角度；不要虚构奖项、优惠、产品能力。"},
    }, ["variant", "material_ids", "angle"]),
    schema("save_plan", "校验依赖、预算和截止时间后保存方案；沿用已成功脚本，原子预留制作费用。", {"variant": VARIANT}, ["variant"]),
    schema("finish", "当无法完成时主动停止。只有 save_plan 成功能标记 completed。", {
        "code": {"type": "string", "enum": ["NO_FEASIBLE_PLAN", "NO_MATERIALS", "TOOL_FAILURE", "OTHER"]},
    }, ["code"]),
]
SCHEMA_BY_NAME = {item["function"]["name"]: item["function"]["parameters"] for item in TOOL_SCHEMAS}
STEP = {"search_materials": "materials", "estimate_cost": "estimate", "generate_script": "script", "save_plan": "save"}


def validate_args(name: str, args: dict) -> None:
    spec = SCHEMA_BY_NAME.get(name)
    if spec is None:
        raise ToolFailure("UNKNOWN_TOOL", "工具不在允许列表中")
    if not isinstance(args, dict) or set(spec["required"]) - args.keys() or args.keys() - spec["properties"].keys():
        raise ToolFailure("INVALID_ARGUMENTS", "工具参数缺失或包含未知字段")
    for key, value in args.items():
        rule = spec["properties"][key]
        if rule["type"] == "string" and (not isinstance(value, str) or not value.strip() or len(value) > (300 if key == "reason" else 500)):
            raise ToolFailure("INVALID_ARGUMENTS", f"{key} 必须是有长度限制的非空字符串")
        if "enum" in rule and value not in rule["enum"]:
            raise ToolFailure("INVALID_ARGUMENTS", f"{key} 不在枚举范围")
        if rule["type"] == "array" and (not isinstance(value, list) or not 1 <= len(value) <= 20 or any(not isinstance(x, str) or len(x) > 100 for x in value) or len(set(value)) != len(value)):
            raise ToolFailure("INVALID_ARGUMENTS", f"{key} 必须是 1–20 个不同的字符串")


class BusinessTools:
    def __init__(self, catalog: dict, materials: list[dict], clock: Clock):
        self.catalog, self.materials, self.clock = catalog, materials, clock

    def execute(self, name: str, args: dict, state: dict) -> dict:
        try:
            validate_args(name, args)
            if name == "finish":
                state["status"] = "incomplete"
                state["reason"] = {"code": args["code"], "message": args["reason"]}
                gaps = [q for q in state["quotes"].values() if not q["feasible"]]
                if gaps:
                    state["reason"]["observed_gaps"] = gaps
                return {"status": "stopped", **state["reason"]}
            result = getattr(self, name)(args, state)
            return result
        except ToolFailure as exc:
            step = state["steps"].get(STEP.get(name, ""))
            if step and step["status"] != "succeeded":
                step["status"] = "partial" if name == "search_materials" and state["materials"] else "failed"
                step["last_error"] = exc.result["code"]
            return exc.result

    def _fault(self, name: str, args: dict, state: dict) -> None:
        faults = state["faults"]
        qualifier = args.get("source", args.get("variant", ""))
        for selector in (f"{name}:{qualifier}", name):
            if selector in faults.get("always", []):
                raise ToolFailure("TOOL_UNAVAILABLE", "合成业务工具被注入持续故障", retryable=False)
            remaining = faults.get("once", {}).get(selector, 0)
            if remaining > 0:
                faults["once"][selector] = remaining - 1
                raise ToolFailure("TOOL_UNAVAILABLE", "合成业务工具被注入一次故障；可重试或调整方案", retryable=True)

    def search_materials(self, args: dict, state: dict) -> dict:
        cache_key = digest({"tool": "search_materials", "source": args["source"], "query": args["query"]})
        if cache_key in state["cache"]:
            return {**deepcopy(state["cache"][cache_key]), "cached": True}
        self._fault("search_materials", args, state)
        query = args["query"].lower()
        found = [deepcopy(m) for m in self.materials if m["source"] == args["source"] and any(tag.lower() in query for tag in m["tags"])]
        if args["source"] in state["faults"].get("empty_sources", []):
            found = []
        partial = args["source"] in state["faults"].get("partial_sources", [])
        if partial:
            found = found[:1]
        state["elapsed_minutes"] += self.catalog["search_minutes"]
        state["materials"].update({m["id"]: m for m in found})
        result = {"status": "partial" if partial else "ok", "source": args["source"], "materials": found,
                  "count": len(found), "retained_count": len(state["materials"]), "cached": False}
        if partial:
            result["warning"] = "本来源仅部分分片成功；已成功素材保留，可检索 archive 补充或降低素材需求。"
        state["searches"][args["source"]] = {"count": len(found), "status": result["status"]}
        state["steps"]["materials"] = {**state["steps"]["materials"], "status": "partial" if partial else ("succeeded" if state["materials"] else "blocked")}
        state["cache"][cache_key] = deepcopy(result)
        return result

    def estimate_cost(self, args: dict, state: dict) -> dict:
        self._fault("estimate_cost", args, state)
        variant = args["variant"]
        value = quote(state, variant, self.catalog, self.clock)
        state["quotes"][variant] = value
        state["steps"]["estimate"]["status"] = "succeeded" if value["feasible"] else "blocked"
        state["steps"]["estimate"]["variant"] = variant
        if value["feasible"]:
            previous = state["selected_variant"]
            state["selected_variant"] = variant
            if previous != variant:
                state["steps"]["script"] = {"status": "succeeded" if variant in state["scripts"] else "pending", "depends_on": ["materials", "estimate"], "variant": variant}
                if variant in state["scripts"]:
                    state["steps"]["script"]["artifact_id"] = state["scripts"][variant]["id"]
                state["steps"]["save"] = {"status": "pending", "depends_on": ["script", "estimate"], "variant": variant}
        return {"status": "ok" if value["feasible"] else "rejected", **value,
                "alternatives": [quote(state, v, self.catalog, self.clock) for v in self.catalog["variants"] if v != variant]}

    def _require_quote(self, variant: str, state: dict) -> dict:
        previous = state["quotes"].get(variant)
        if not previous or not previous["feasible"]:
            raise ToolFailure("DEPENDENCY_NOT_MET", "须先对该档位调用 estimate_cost 并得到可行结果")
        current = quote(state, variant, self.catalog, self.clock)
        if not current["feasible"]:
            state["quotes"][variant] = current
            state["steps"]["estimate"].update(status="blocked", variant=variant)
            raise ToolFailure("CONSTRAINT_CHANGED", "预算或时间条件已变化，请重新估算", quote=current)
        return current

    def generate_script(self, args: dict, state: dict) -> dict:
        variant = args["variant"]
        if variant in state["scripts"]:
            state["selected_variant"] = variant
            state["steps"]["script"] = {"status": "succeeded", "depends_on": ["materials", "estimate"], "variant": variant, "artifact_id": state["scripts"][variant]["id"]}
            return {"status": "ok", "cached": True, "script": deepcopy(state["scripts"][variant])}
        self._require_quote(variant, state)
        config = self.catalog["variants"][variant]
        if any(mid not in state["materials"] for mid in args["material_ids"]) or len(args["material_ids"]) < config["min_materials"]:
            raise ToolFailure("MATERIALS_INSUFFICIENT", "素材不存在或数量不足", required=config["min_materials"], available=list(state["materials"]))
        self._fault("generate_script", args, state)
        script = {
            "id": "script-" + digest({"request": state["request_id"], "variant": variant})[:12],
            "variant": variant, "title": state["request"]["topic"], "angle": args["angle"],
            "format": config["format"], "material_ids": args["material_ids"],
            "sections": [
                {"stage": "开场", "text": f"{args['angle']}：用一个生活片段引出「{state['request']['topic']}」。"},
                {"stage": "主体", "text": " / ".join(state["materials"][mid]["content"] for mid in args["material_ids"])},
                {"stage": "行动", "text": "邀请观众围绕主题创作并发布作品；具体渠道、活动话题与审核规则由运营确认。"},
            ],
            "generator": "local-template-v1", "requires_editorial_review": True,
        }
        state["scripts"][variant] = script
        state["selected_variant"] = variant
        state["ledger"].append({"id": f"script:{variant}", "kind": "incurred", "cents": config["script_cents"]})
        state["elapsed_minutes"] += config["script_minutes"]
        state["steps"]["script"] = {"depends_on": ["materials", "estimate"], "status": "succeeded", "variant": variant, "artifact_id": script["id"]}
        state["steps"]["materials"]["status"] = "succeeded"
        return {"status": "ok", "cached": False, "script": deepcopy(script), "charged_cents": config["script_cents"]}

    def save_plan(self, args: dict, state: dict) -> dict:
        if state["saved_plan"] is not None:
            return {"status": "ok", "cached": True, "plan_id": state["saved_plan"]["id"]}
        variant = args["variant"]
        if variant not in state["scripts"]:
            raise ToolFailure("DEPENDENCY_NOT_MET", "该档位脚本尚未成功，不能保存")
        value = self._require_quote(variant, state)
        self._fault("save_plan", args, state)
        config = self.catalog["variants"][variant]
        ready_by = value["ready_by"]
        state["elapsed_minutes"] += self.catalog["save_minutes"]
        state["ledger"].append({"id": f"production:{variant}", "kind": "reserved", "cents": config["production_cents"]})
        state["selected_variant"] = variant
        state["steps"]["estimate"] = {"status": "succeeded", "depends_on": [], "variant": variant}
        state["steps"]["script"] = {"status": "succeeded", "depends_on": ["materials", "estimate"], "variant": variant, "artifact_id": state["scripts"][variant]["id"]}
        state["steps"]["save"] = {"status": "succeeded", "depends_on": ["script", "estimate"], "variant": variant}
        state["status"], state["reason"] = "completed", None
        production_start = effective_now(state, self.clock)
        state["saved_plan"] = {
            "id": "plan-" + digest(state["request_id"])[:12], "request_id": state["request_id"],
            "topic": state["request"]["topic"], "variant": variant, "format": config["format"],
            "script": deepcopy(state["scripts"][variant]), "material_ids": state["scripts"][variant]["material_ids"],
            "total_cents": occupied_cents(state), "budget_cents": state["request"]["budget_cents"],
            "ledger": deepcopy(state["ledger"]), "deadline": state["request"]["deadline"],
            "projected_ready_by": ready_by, "saved_at": iso(utcnow()), "reference_saved_at": iso(effective_now(state, self.clock)),
            "execution_plan": [
                {"step": "materials", "owner": "Agent", "status": "succeeded", "depends_on": []},
                {"step": "estimate", "owner": "Agent", "status": "succeeded", "depends_on": []},
                {"step": "script", "owner": "Agent", "status": "succeeded", "depends_on": ["materials", "estimate"]},
                {"step": "save", "owner": "Agent", "status": "succeeded", "depends_on": ["script", "estimate"]},
                {"step": "production", "owner": "运营/制作", "status": "planned", "depends_on": ["save"],
                 "start_at": iso(production_start), "end_at": iso(production_start + timedelta(minutes=config["production_minutes"]))},
                {"step": "review_and_publish", "owner": "运营", "status": "pending", "depends_on": ["production"],
                 "note": "确认文案、渠道与活动规则后执行。预估完成时间只覆盖素材制作，不含人工审核排队。"},
            ],
            "scope": "已保存可执行活动方案；制作与发布尚未执行，费用为模拟已发生及预留金额。",
        }
        return {"status": "ok", "cached": False, "plan_id": state["saved_plan"]["id"], "total_cents": occupied_cents(state), "projected_ready_by": ready_by}
