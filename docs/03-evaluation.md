# 效果验证、失败与限制

## 本次结论

在 Windows / Python 3.12.4 实际执行，**50 项自动测试通过，14 组离线案例的状态与费用符合预期**。工程层面的预算守卫、步骤依赖、成功结果保留、重复执行和失败续跑得到验证。

**真实模型动态决策尚未验证。** 千问 `qwen-plus` 的三组实际运行都在第一次模型请求返回 HTTP 403 / `AllocationQuota.FreeTierOnly`，业务工具尚未调用。真实成功路径为 0，不能用离线规则和 HTTP 测试替身推断模型已经满足 ReAct 验收。

## 可复验命令与证据

```powershell
python scripts/verify.py
python scripts/run_examples.py --mode offline
python scripts/run_examples.py --mode live --cases normal budget_replan tool_failure
```

前两条命令本次成功。第三条本次失败并保留实际输出。测试详情见 [unittest.txt](../examples/verification/unittest.txt) 与 [summary.json](../examples/verification/summary.json)；离线案例见 [offline/summary.json](../examples/offline/summary.json)；真实失败见 [live/summary.json](../examples/live/summary.json)。

本次本地没有执行 GitHub Actions，不能声称已验证 Linux 或所有 Python 版本。CI 配置提交后可由远端实际运行。

## 必须验收点

| 验收点 | 测试预期 | 实际结果与证据 |
| --- | --- | --- |
| 正常完成 | premium，费用 12，保存一次 | 符合；[结果](../examples/offline/normal/result.json)、[Trace](../examples/offline/normal/trace.md) |
| 缺预算 | 提示 budget，不调用模型 | 符合，needs_input / MISSING_FIELDS；[结果](../examples/offline/missing_budget/result.json) |
| 缺截止时间 | 提示 deadline，不猜测时间 | 符合；[结果](../examples/offline/missing_deadline/result.json) |
| 工具失败 | 记录 primary 错误，换来源 | 符合，archive 取得素材并完成；[Trace](../examples/offline/tool_failure/trace.md) |
| 预算超限可降级 | 预算 10，先报 12，再报 8，最终费用 8 | 符合，premium 未生成、未计费；[结果](../examples/offline/budget_replan/result.json)、[Trace](../examples/offline/budget_replan/trace.md) |
| 预算超限无解 | 预算 3，无方案，指出缺口 | 符合，最低报价 4，缺口 1，未保存；[结果](../examples/offline/budget_impossible/result.json) |
| 重复执行 | 不重复调用、扣费或新增方案 | 符合，重放费用仍 12，run_count=1；[首次结果](../examples/offline/repeat/first/result.json)、[二次结果](../examples/offline/repeat/result.json) |
| 失败不得记成功 | 持续脚本失败时 script=failed | 符合，材料成功保留、saved_plan=null；[结果](../examples/offline/persistent_failure/result.json) |
| 真实模型根据观察改动作 | 至少两条成功路径 | 未验证，当前服务不可用；[实际错误](../examples/live/budget_replan/trace.md) |

表中“符合”均限定为离线流程与工程约束，不是模型效果指标。

## 额外边界与续跑

| 场景 | 实际检查结果 | 证据 |
| --- | --- | --- |
| 部分成功 | primary 返回 1 条；archive 再补 2 条，原 ID 进入保存方案 | [Trace](../examples/offline/partial_success/trace.md) |
| 保存失败后跨连接恢复 | 首轮 5 步结束，script=succeeded、save=failed、费用 1；续跑仅保存，费用 8 | [首次](../examples/offline/resume_save/first/result.json)、[续跑](../examples/offline/resume_save/result.json) |
| 无资料 | 两来源均无相关素材，NO_MATERIALS，不编造素材 ID | [Trace](../examples/offline/no_materials/trace.md) |
| 截止时间降级 | 20 分钟窗口选 lean，预计 10:20 完成，费用 4 | [结果](../examples/offline/deadline_replan/result.json) |
| 时间无解 | 10 分钟窗口全部档位超时，未保存 | [结果](../examples/offline/deadline_impossible/result.json) |
| 步数上限 | 1 次决策后 STEP_LIMIT；正常结束不冒充完成 | [结果](../examples/offline/step_limit/result.json) |
| 沉没成本 | 已生成其他档位脚本的费用计入新报价，13>12 时拒绝保存 | [test_agent.py](../tests/test_agent.py) 的 `test_sunk_cost_is_included_when_switching_variants` |
| 原生协议 | 第二次 HTTP 请求确实带回第一次 rejected 结果与 tool_call_id；多动作、截断、文本冒充完成均拒绝 | [test_models.py](../tests/test_models.py)；使用测试替身 |
| 持久化一致性 | 事务异常时状态与方案同时回滚；活动租约阻止同任务并发执行 | [test_agent.py](../tests/test_agent.py) |

测试没有统计准确率、质量分或“成功率 100%”等泛化指标。14 组案例是预定义的小规模合成场景，不能代表真实用户输入分布。

## 已发现并修正的问题

实现检查时补上了四个细节：早期报价在额外耗时/费用后必须重新核算；切换档位后不能让步骤引用旧脚本；复用同一输出目录时，未完成结果必须移除上次生成的 `plan.json/plan.md`；实际事件时间不能被回归用的固定业务时钟替代。对应边界均有可执行测试或状态一致性检查，没有将修正前假想运行冒充实际失败日志。

## 当前限制与下一轮实验

1. 当前没有成功的真实模型路径。应先恢复可用服务，再分别运行正常、预算降级、一次工具故障，每条重复若干次记录方差；失败也保留。
2. 模型服务故障发生在首轮，尚未验证真实模型在中途断线后继续规划的行为。状态保存逻辑通过工程测试覆盖，但不是线上稳定性证明。
3. 素材库仅六条合成资料，检索是关键词匹配，脚本是本地模板，不评估成片效果、创意质量或真实版权。
4. 制作费用为预留，制作和发布尚未发生；人工审核等待不计入制作时间。真实 API 成本没有纳入模拟预算，只有 usage 字段可供以后核算。
5. 当前只支持本地 SQLite 与 Chat Completions 函数调用接口。没有任务队列、消息压缩、长期存储清理或对真实外部副作用的恢复保证。
6. 候选人个人独立复验与修改尚未提供，见 [AI 使用说明](04-ai-usage.md)。
