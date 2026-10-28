# 内容任务规划 Agent

小影校招 AI Agent 开发岗位笔试，所选题目：**内容任务规划 Agent**。提供 Python CLI，输入主题、预算与截止时间，输出任务状态、素材、脚本、费用账本、保存的活动方案和完整执行记录。

实现了原生函数调用的 `模型选择工具 → 执行 → 回传观察 → 模型下一步选择` 循环，以及预算/时间守卫、SQLite 状态持久化、重复执行去重和失败步骤续跑。

**验证现状：50 项自动测试、14 组离线案例及 14 组真实模型场景的状态/费用检查通过。** 运行时使用 `qwen3.8-27b`，已实际观察到模型在报价 12 被拒后改选 8、部分素材成功后补充来源、保存失败后复用脚本续跑。真实模型记录见 [examples/live/](examples/live/)，[自动审计](examples/verification/live-audit.json)核对了响应 ID、动作顺序和状态保留。业务工具仍为合成模拟，单轮合成验收不代表真实运营效果或泛化成功率。

## 评审入口

| 内容 | 入口 |
| --- | --- |
| 真实模型：预算 10、估算 12 后改选 8 | [运行记录](examples/live/budget_replan/trace.md)、[实际结果](examples/live/budget_replan/result.json)、[保存方案](examples/live/budget_replan/plan.md) |
| 真实模型：一次工具失败后自主重试 | [运行记录](examples/live/tool_failure/trace.md) |
| 真实模型：部分成功后换来源补充 | [运行记录](examples/live/partial_success/trace.md) |
| 真实模型：保存失败，续跑只重做保存 | [首次记录](examples/live/resume_save/first/trace.md)、[续跑记录](examples/live/resume_save/trace.md) |
| 全部场景与验收点 | [examples/README.md](examples/README.md)、[评估文档](docs/03-evaluation.md) |
| 实际测试日志 | [unittest.txt](examples/verification/unittest.txt)、[机器可读结果](examples/verification/summary.json) |
| 模型决策接入 | [models.py](src/content_agent/models.py) |
| 循环、步数限制、持久化 | [agent.py](src/content_agent/agent.py)、[storage.py](src/content_agent/storage.py) |
| 费用、依赖、状态守卫 | [tools.py](src/content_agent/tools.py) |

## 环境与安装

Python **3.10+**，实际验证环境为 Windows / Python 3.12.4。运行和测试只使用标准库；无 Agent 框架、数据库服务或模型 SDK 依赖。

在项目根目录执行：

```powershell
python -m pip install -e .
```

完全断网时，可跳过安装，先在当前 PowerShell 会话设置源码路径：

```powershell
$env:PYTHONPATH = (Resolve-Path .\src).Path
```

Linux/macOS 的等效方式为 `export PYTHONPATH="$PWD/src"`。之后的 `python -m content_agent`、测试及案例命令均可运行。

## 一分钟离线运行

```powershell
python -m content_agent --input examples/offline/budget_replan/input.json --mode offline --now 2026-10-28T10:00:00+08:00 --db runs/demo.sqlite3 --output runs/demo
```

实际离线结果：先估算 premium=12，观察预算超限，再估算 standard=8，取得素材、生成脚本并保存。`runs/demo/` 中生成 `result.json`、`trace.jsonl`、`trace.md`、`plan.json`、`plan.md`。最终费用 8 SIM＝脚本 1＋制作预留 7。

样例使用历史业务时间，因此命令显式指定 `--now`；真实使用时省略该参数，时钟采用真实当前时间。方案保存完成不代表后续内容已经制作或发布。

退出码：`0`＝方案已保存；`2`＝缺少输入、无可行方案、模型不可用、达到上限或其他未完成状态。未完成原因见 JSON 的 `reason`，已有成功结果照常保留。

## 输入

```json
{
  "topic": "校园秋日短视频挑战",
  "budget": 10,
  "deadline": "2026-10-28T18:00:00+08:00",
  "preferred_variant": "premium"
}
```

`topic`、`budget`、`deadline` 必填；预算可为 0，最多两位小数；截止时间必须包含时区。`preferred_variant` 可省略，默认 premium，是可降级的偏好。账本内部使用整数分，100 分＝1 SIM；报价同时提供 `*_units` 显示金额供模型解释，避免把分误标为 SIM。

缺少预算或截止时间时直接返回 `needs_input`，不调用模型、不执行工具，也不猜测预算和时间。

## 真实模型

默认 `--mode live`，不会在调用失败时悄悄切换到离线策略。配置说明见 [.env.example](.env.example)，程序不自动读取 `.env`。

```powershell
# 先在本机环境中安全配置 AGENT_API_KEY 或 DASHSCOPE_API_KEY。
$env:AGENT_BASE_URL = 'https://dashscope.aliyuncs.com/compatible-mode/v1'
$env:AGENT_MODEL = 'qwen3.8-27b'
python -m content_agent --input examples/offline/budget_replan/input.json --mode live --now 2026-10-28T10:00:00+08:00 --db runs/live.sqlite3 --output runs/live
```

支持原生 function calling 的 Chat Completions 兼容接口。切换供应商时同时设置 `AGENT_BASE_URL`、`AGENT_MODEL` 和 `AGENT_API_KEY`。未指定通用密钥时，阿里云地址读取 `DASHSCOPE_API_KEY`，其他地址读取 `OPENAI_API_KEY`。仅支持 Responses API 的模型不适用当前适配器。

当前默认模型为用户控制台中有可用额度的 `qwen3.8-27b`，已成功完成真实函数调用。模型能力见[阿里云官方页面](https://help.aliyun.com/zh/model-studio/qwen3-8-27b)。此前 `qwen-plus` 返回 HTTP 403，其记录保存在 [provider-errors/qwen-plus](examples/provider-errors/qwen-plus/summary.json)；单个型号额度不足不表示所有型号不可用。没有更改账户计费开关，密钥只在运行进程中使用。

## 重复执行与失败续跑

同一数据库中，规范化输入生成稳定的 request ID。重复执行返回已存结果，`replayed=true`，不再调用模型、生成脚本、扣费或新增方案。也可用 `--request-id demo-1` 指定业务 ID；同一 ID 绑定不同输入会返回 `ID_CONFLICT`。

以下演示在第 5 次决策的保存步骤注入一次失败，随后跨进程续跑：

```powershell
python -m content_agent --input examples/offline/budget_replan/input.json --mode offline --now 2026-10-28T10:00:00+08:00 --db runs/resume.sqlite3 --output runs/first --request-id resume-demo --fail-once save_plan --max-steps 5
python -m content_agent --input examples/offline/budget_replan/input.json --mode offline --now 2026-10-28T10:00:00+08:00 --db runs/resume.sqlite3 --output runs/resumed --request-id resume-demo --resume
```

首条命令预期退出 2：脚本成功、保存失败、费用占用 1；续跑只调用保存，费用最终为 8。故障计数持久化，`--resume` 不会重新注入。未指定 `--resume` 时，未完成任务也只重放，不自动推进。

每轮最多 16 次模型决策，可通过 `--max-steps 1..64` 调整，工具调用数不会超过该上限。无效模型输出也消耗决策次数，达到上限返回 `incomplete / STEP_LIMIT`。模型网络请求超时为 45 秒，调用失败不会自动重试。

## 验证

```powershell
python scripts/verify.py
python scripts/run_examples.py --mode offline
# 真实模型调用消耗 API 额度；首次 14 场景验收已实际执行。
python scripts/run_examples.py --mode live --cases normal budget_replan tool_failure
python scripts/audit_live.py
```

前两条命令分别生成自动测试日志和 14 组离线案例。完整真实批次的命令是 `python scripts/run_examples.py --mode live`。带 `--cases` 时仅重生成所选案例及该批次汇总，建议用 `--output-root examples/recheck` 保留原有完整批次。案例生成器使用临时数据库；输出均来自实际执行。实际 `observed_at` 与业务参考时间分开记录。

首轮真实运行曾出现一条金额单位说明错误，账本仍正确。已在提示与报价中补充单位，并独立复验正常、预算降级、预算无解三场景，见 [单位修正记录](examples/unit-clarification/live/summary.json)与[评估文档](docs/03-evaluation.md)。原始记录保留，未手工改写。

[GitHub Actions](.github/workflows/test.yml) 配置了 Windows/Linux × Python 3.10/3.12 矩阵；本地仅验证 Windows 3.12.4，远端 CI 尚未运行。

## 目录与交付

```text
src/content_agent/       决策循环、模型适配、工具、状态存储、CLI
tests/                  可执行工程和接口契约测试
examples/               输入、实际输出、JSONL/Markdown Trace、测试日志
data/                   合成素材及费用/耗时规则索引
docs/01-requirements.md  用户、范围、成功标准
docs/02-solution.md      方案、动态决策和取舍
docs/03-evaluation.md    预期、实际、失败与限制
docs/04-ai-usage.md      AI 使用范围与贡献归属
docs/05-retrospective.md 学习、改进和下一步
scripts/                重生成验证材料
```

依用户选择，本轮先完成本地项目和 Git 提交，不创建或推送远程仓库。题号未提供，提交时填写试卷实际题号，不能自行编造。最终 SHA 用 `git rev-parse HEAD` 获取；后续 GitHub 交付步骤见 [docs/06-submission.md](docs/06-submission.md)。
