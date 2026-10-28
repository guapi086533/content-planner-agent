# 效果验证、失败与限制

## 本次结论

在 Windows / Python 3.12.4 实际执行，**50 项自动测试、14 组离线案例、14 组真实模型场景的状态与费用检查通过**。外部真实模型为 `qwen3.8-27b`；业务工具仍为本地合成函数。

**已取得正常、预算降级、部分成功后补充来源等真实决策路径。** 正常路径保存 12 SIM 的 premium；预算 10 时模型观察 premium=12 被拒，再估 standard=8 并保存；primary 仅部分成功时，模型改检索 archive，同时保留原素材。响应 ID、工具结果与动作顺序见 [live-audit.json](../examples/verification/live-audit.json)。

“状态与费用检查通过”不代表模型每句说明都正确：首轮预算无解场景出现了金额单位口误。此问题已通过提示与显示字段修正，并针对性复验 3 个场景；原始说明和修正后记录同时保留，详见下文。

## 可复验命令与证据

```powershell
python scripts/verify.py
python scripts/run_examples.py --mode offline
python scripts/run_examples.py --mode live
python scripts/audit_live.py
# 单位说明修正后的独立批次，不覆盖首轮完整记录
python scripts/run_examples.py --mode live --cases budget_impossible budget_replan normal --output-root examples/unit-clarification
```

上述工程测试、案例及独立复验均实际执行。测试详情见 [unittest.txt](../examples/verification/unittest.txt)；离线案例见 [offline/summary.json](../examples/offline/summary.json)；真实模型首轮汇总见 [live/summary.json](../examples/live/summary.json)；单位修正后的批次见 [unit-clarification/live/summary.json](../examples/unit-clarification/live/summary.json)。此前 qwen-plus 的 403 错误另存于 [provider-errors](../examples/provider-errors/qwen-plus/summary.json)。

本地验证环境为 Windows / Python 3.12.4。GitHub Actions 配置了 Windows/Linux × Python 3.10/3.12 矩阵，跨平台结果以[最终提交对应的运行记录](https://github.com/guapi086533/content-planner-agent/actions)为准，不能由本地测试通过推断其他环境也通过。

## 必须验收点

| 验收点 | 测试预期 | 实际结果与证据 |
| --- | --- | --- |
| 正常完成 | premium，费用 12，保存一次 | 符合；[结果](../examples/live/normal/result.json)、[Trace](../examples/live/normal/trace.md) |
| 缺预算 | 提示 budget，不调用模型 | 符合，needs_input / MISSING_FIELDS；[结果](../examples/live/missing_budget/result.json) |
| 缺截止时间 | 提示 deadline，不猜测时间 | 符合；[结果](../examples/live/missing_deadline/result.json) |
| 工具失败 | 保留 primary 错误，由模型选择后续动作 | 真实模型根据 retryable=true 重试 primary 并完成；[Trace](../examples/live/tool_failure/trace.md)。离线策略选择 archive，二者不同 |
| 预算超限可降级 | 预算 10，先报 12，再报 8，最终费用 8 | 符合，premium 未生成、未计费；[结果](../examples/live/budget_replan/result.json)、[Trace](../examples/live/budget_replan/trace.md) |
| 预算超限无解 | 预算 3，无方案，指出缺口 | 首轮状态/账本正确，但文字误标单位；修正复验正确给出 3 SIM 及最低缺口 1 SIM；[复验结果](../examples/unit-clarification/live/budget_impossible/result.json) |
| 重复执行 | 不重复调用、扣费或新增方案 | 符合，重放费用仍 12，run_count=1；[首次](../examples/live/repeat/first/result.json)、[二次](../examples/live/repeat/result.json) |
| 失败不得记成功 | 持续脚本失败时 script=failed | 符合；模型尝试 premium、standard 后停止，素材保留；[结果](../examples/live/persistent_failure/result.json) |
| 真实模型根据观察改动作 | 至少两条成功路径 | 符合；[预算降级](../examples/live/budget_replan/trace.md)、[部分成功补充来源](../examples/live/partial_success/trace.md)，与正常路径不同 |

表中真实调用包含模型响应 ID 和 token usage。缺字段场景由确定性输入校验直接结束，不调用模型。离线结果仍单列存档，不与真实模型证据混用。

## 额外边界与续跑

| 场景 | 实际检查结果 | 证据 |
| --- | --- | --- |
| 部分成功 | primary 返回 1 条；archive 再补 2 条，原 ID 进入保存方案 | [Trace](../examples/live/partial_success/trace.md) |
| 保存失败后跨连接恢复 | 首轮 5 步结束，script=succeeded、save=failed、费用 1；续跑仅保存，费用 8 | [首次](../examples/live/resume_save/first/result.json)、[续跑](../examples/live/resume_save/result.json) |
| 无资料 | 两来源均无相关素材，NO_MATERIALS，不编造素材 ID | [Trace](../examples/live/no_materials/trace.md) |
| 截止时间降级 | 20 分钟窗口选 lean，预计 10:20 完成，费用 4 | [结果](../examples/live/deadline_replan/result.json) |
| 时间无解 | 10 分钟窗口全部档位超时，未保存 | [结果](../examples/live/deadline_impossible/result.json) |
| 步数上限 | 1 次决策后 STEP_LIMIT；正常结束不冒充完成 | [结果](../examples/live/step_limit/result.json) |
| 沉没成本 | 已生成其他档位脚本的费用计入新报价，13>12 时拒绝保存 | [test_agent.py](../tests/test_agent.py) 的 `test_sunk_cost_is_included_when_switching_variants` |
| 原生协议 | 第二次 HTTP 请求确实带回第一次 rejected 结果与 tool_call_id；多动作、截断、文本冒充完成均拒绝 | [test_models.py](../tests/test_models.py)；使用测试替身 |
| 持久化一致性 | 事务异常时状态与方案同时回滚；活动租约阻止同任务并发执行 | [test_agent.py](../tests/test_agent.py) |

14 组场景是预定义的小规模合成集合，每场景只执行一次，不代表真实用户输入分布。正常路径、重复执行、续跑等共享历史 Trace 的 token 用量按 response_id 去重，详见 live-audit.json；没有把重放计为新的模型调用，也没有由本次通过率推断泛化准确率。

## 已发现并修正的问题

实现检查时补上了四个细节：早期报价在额外耗时/费用后必须重新核算；切换档位后不能让步骤引用旧脚本；复用同一输出目录时，未完成结果必须移除上次生成的 `plan.json/plan.md`；实际事件时间不能被回归用的固定业务时钟替代。对应边界均有可执行测试或状态一致性检查，没有将修正前假想运行冒充实际失败日志。

真实模型额外暴露了单位问题：[首轮原始记录](../examples/live/budget_impossible/trace.md)把 `budget_cents=300` 写成“300 SIM”。代码账本正确返回 3 SIM 预算、最低 1 SIM 缺口。随后在提示中明确 100 分＝1 SIM，并为报价增加显示字段。修正后的[实际复验](../examples/unit-clarification/live/budget_impossible/trace.md)写出“3 SIM，分别缺 9/5/1 SIM”；另外复验了正常和预算降级，状态/费用仍符合预期。没有改写原错误文案，也没有将单次修正复验视为永久消除所有表达错误。

## 当前限制与下一轮实验

1. 当前仅验证一个真实模型、一套合成场景及三条针对性复验。应增加重复次数、主题和边界，并保留失败，不能宣称生产稳定性。
2. 尚未验证真实模型 API 在中途断线后的持续运行；本次工具失败为合成注入，保存续跑确实再次调用了真实模型，但不是网络故障演练。
3. 素材库仅六条合成资料，检索是关键词匹配，脚本是本地模板，不评估成片效果、创意质量或真实版权。
4. 制作费用为预留，制作和发布尚未发生；人工审核等待不计入制作时间。真实 API 成本没有纳入模拟预算，只有 usage 字段可供以后核算。
5. 当前只支持本地 SQLite 与 Chat Completions 函数调用接口。没有任务队列、消息压缩、长期存储清理或对真实外部副作用的恢复保证。
6. 候选人个人独立复验与修改尚未提供，见 [AI 使用说明](04-ai-usage.md)。
