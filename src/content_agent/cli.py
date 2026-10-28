from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

from .agent import run_agent
from .domain import iso, parse_time, utcnow
from .models import ChatModel, ModelError, OfflineModel
from .storage import Store


def write_outputs(report: dict, directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "result.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    trace = report.get("trace", [])
    (directory / "trace.jsonl").write_text("".join(json.dumps(e, ensure_ascii=False, allow_nan=False) + "\n" for e in trace), encoding="utf-8")
    lines = [f"# {report['request_id']} 执行记录", "", f"- 状态：{report['status']}", f"- 模型：{json.dumps(report.get('model'), ensure_ascii=False)}",
             f"- 重放：{report.get('replayed', False)}", f"- 费用合计：{report['cost']['total_units']} SIM（已发生 {report['cost']['incurred_units']}，预留 {report['cost']['reserved_units']}）", "",
             "> offline 的决策来自固定规则，仅验证工程流程。工具均为合成模拟。", ""]
    if report.get("reason"):
        lines.extend(["未完成原因：" + json.dumps(report["reason"], ensure_ascii=False), ""])
    for index, event in enumerate(trace):
        if event["kind"] != "tool":
            lines.extend([f"## 步骤 {event['sequence']}：模型错误", "", json.dumps(event, ensure_ascii=False), ""])
            continue
        next_event = trace[index + 1] if index + 1 < len(trace) else None
        next_action = next_event.get("tool", next_event.get("kind")) if next_event else report["status"]
        lines.extend([f"## 步骤 {event['sequence']}：{event['tool']}", "", f"依据：{event['rationale']}", "",
                      "参数：", "```json", json.dumps(event["parameters"], ensure_ascii=False, indent=2), "```", "",
                      "实际返回：", "```json", json.dumps(event["observation"], ensure_ascii=False, indent=2), "```", "",
                      f"后续动作：{next_action}", ""])
    (directory / "trace.md").write_text("\n".join(lines), encoding="utf-8")
    if report.get("saved_plan"):
        plan = report["saved_plan"]
        display_deadline = iso(parse_time(plan["deadline"]).astimezone(parse_time(plan["projected_ready_by"]).tzinfo))
        (directory / "plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        sections = [f"# {plan['topic']}", "", f"方案：{plan['variant']} / {plan['format']}", f"预算占用：{plan['total_cents'] / 100:g} / {plan['budget_cents'] / 100:g} SIM",
                    f"预计素材制作完成：{plan['projected_ready_by']}", f"截止时间：{display_deadline}", "", plan["scope"], "",
                    "## 脚本", "", f"创意：{plan['script']['angle']}", ""]
        for part in plan["script"]["sections"]:
            sections.extend([f"### {part['stage']}", "", part["text"], ""])
        sections.extend(["## 执行计划", "", "| 步骤 | 负责人 | 状态 | 依赖 |", "| --- | --- | --- | --- |"])
        sections.extend(f"| {step['step']} | {step['owner']} | {step['status']} | {', '.join(step['depends_on']) or '无'} |" for step in plan["execution_plan"])
        sections.extend(["", "素材来源：" + ", ".join(plan["material_ids"]), "", "文案由本地模板生成，须由运营确认活动规则、渠道和内容后发布。", ""])
        (directory / "plan.md").write_text("\n".join(sections), encoding="utf-8")
    else:
        # An explicitly designated output directory must not display an older plan as this run's result.
        for filename in ("plan.json", "plan.md"):
            (directory / filename).unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="有状态的内容任务规划 Agent；默认 live，离线须显式指定 offline")
    parser.add_argument("--input", required=True, type=Path, help="主题、预算、带时区截止时间的 JSON 文件")
    parser.add_argument("--mode", choices=["live", "offline"], default="live")
    parser.add_argument("--db", type=Path, default=Path("runs/state.sqlite3"))
    parser.add_argument("--output", type=Path, default=Path("runs/latest"))
    parser.add_argument("--request-id")
    parser.add_argument("--resume", action="store_true", help="显式续跑未完成任务；已成功步骤不重做")
    parser.add_argument("--max-steps", type=int, default=16)
    parser.add_argument("--now", help="演示/回归专用的带时区参考时间，省略则使用真实时间")
    parser.add_argument("--fail-once", action="append", default=[], metavar="TOOL[:QUALIFIER]")
    parser.add_argument("--fail-always", action="append", default=[], metavar="TOOL[:QUALIFIER]")
    parser.add_argument("--partial-source", action="append", choices=["primary", "archive"], default=[])
    parser.add_argument("--empty-source", action="append", choices=["primary", "archive"], default=[])
    args = parser.parse_args(argv)
    store = None
    try:
        raw = json.loads(args.input.read_text(encoding="utf-8-sig"))
        reference = parse_time(args.now) if args.now else None
        clock = (lambda: reference) if reference else utcnow
        model = OfflineModel() if args.mode == "offline" else ChatModel()
        store = Store(args.db)
        report = run_agent(raw, model, store, request_id=args.request_id, max_steps=args.max_steps, resume=args.resume,
                           faults={"once": {name: 1 for name in args.fail_once}, "always": args.fail_always,
                                   "partial_sources": args.partial_source, "empty_sources": args.empty_source}, clock=clock)
        write_outputs(report, args.output)
        print(json.dumps({"request_id": report["request_id"], "status": report["status"], "reason": report["reason"],
                          "total_units": report["cost"]["total_units"], "replayed": report["replayed"],
                          "output": str(args.output.resolve())}, ensure_ascii=False, indent=2))
        return 0 if report["status"] == "completed" else 2
    except (OSError, ValueError, ModelError, sqlite3.Error) as exc:
        print(json.dumps({"status": "invalid_input", "message": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    finally:
        if store:
            store.close()
