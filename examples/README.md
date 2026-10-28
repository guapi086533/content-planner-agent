# 验证材料入口

所有 `result.json`、`trace.jsonl`、`trace.md`、`plan.json`、`plan.md` 均由项目代码实际执行生成。`input.json` 是原始输入，`options.json` 记录模式、故障开关、业务参考时间和上限。生成脚本为 [run_examples.py](../scripts/run_examples.py)。

**offline 是固定规则 Mock，不能证明真实模型决策效果。live 当前均因模型服务不可用失败，尚无成功的真实模型决策证据。** 两类结果分别保存在目录中，各条 Trace 均有 `decision_source`，没有伪装成模型响应的预设日志。

## 离线验收案例

| 场景 | 输入 | 实际结果 | 执行记录 |
| --- | --- | --- | --- |
| 正常完成 | [normal](offline/normal/input.json) | completed，12 SIM | [Trace](offline/normal/trace.md)、[方案](offline/normal/plan.md) |
| 缺预算 | [missing_budget](offline/missing_budget/input.json) | needs_input，0 次工具调用 | [Trace](offline/missing_budget/trace.md) |
| 缺截止时间 | [missing_deadline](offline/missing_deadline/input.json) | needs_input，0 次工具调用 | [Trace](offline/missing_deadline/trace.md) |
| 工具一次失败 | [tool_failure](offline/tool_failure/input.json) | primary 失败，改 archive，完成 12 SIM | [Trace](offline/tool_failure/trace.md) |
| 预算超限可重规划 | [budget_replan](offline/budget_replan/input.json) | 12 被拒→8 被接受，保存 standard | [Trace](offline/budget_replan/trace.md)、[方案](offline/budget_replan/plan.md) |
| 预算超限无解 | [budget_impossible](offline/budget_impossible/input.json) | incomplete，最低缺 1 SIM | [Trace](offline/budget_impossible/trace.md) |
| 重复执行 | [repeat](offline/repeat/input.json) | 第二次 replayed=true，费用不变 | [首次](offline/repeat/first/trace.md)、[重放](offline/repeat/trace.md) |
| 部分成功 | [partial_success](offline/partial_success/input.json) | 原素材保留，archive 补充，完成 | [Trace](offline/partial_success/trace.md) |
| 保存失败后续跑 | [resume_save](offline/resume_save/input.json) | 首次已花 1；续跑只保存，最终 8 | [首次](offline/resume_save/first/trace.md)、[续跑](offline/resume_save/trace.md) |
| 持续失败 | [persistent_failure](offline/persistent_failure/input.json) | 脚本 failed，不保存，保留素材 | [Trace](offline/persistent_failure/trace.md) |
| 无相关资料 | [no_materials](offline/no_materials/input.json) | 两来源均无素材，明确停止 | [Trace](offline/no_materials/trace.md) |
| 截止时间可降级 | [deadline_replan](offline/deadline_replan/input.json) | 20 分钟，选择 lean，4 SIM | [Trace](offline/deadline_replan/trace.md) |
| 截止时间无解 | [deadline_impossible](offline/deadline_impossible/input.json) | incomplete，存在时间缺口 | [Trace](offline/deadline_impossible/trace.md) |
| 达到步数上限 | [step_limit](offline/step_limit/input.json) | incomplete / STEP_LIMIT | [Trace](offline/step_limit/trace.md) |

汇总：[offline/summary.json](offline/summary.json)。同目录的 `result.json` 包含步骤状态、完整账本和保留结果；JSONL 适合程序读取，Markdown 记录还列出下一次实际动作。

## 真实服务记录

| 场景 | 业务期望 | 本次实际 |
| --- | --- | --- |
| [normal](live/normal/trace.md) | 正常保存 | HTTP 403 / AllocationQuota.FreeTierOnly，incomplete |
| [budget_replan](live/budget_replan/trace.md) | 观察超预算后降级 | 首次模型调用不可用，未执行工具 |
| [tool_failure](live/tool_failure/trace.md) | 观察工具失败后换来源 | 首次模型调用不可用，故障注入尚未触发 |

汇总：[live/summary.json](live/summary.json)。这三条记录只证明不可用时能诚实停止，不证明模型完成了题目中的真实动态决策。

模型恢复后重跑：

```powershell
python scripts/run_examples.py --mode live --cases normal budget_replan tool_failure
```

至少应取得 `normal` 与 `budget_replan`（或 `tool_failure`）两条成功的真实模型路径，检查响应 ID、实际参数、工具观察及后续动作，再修改评估结论。失败不得手工改为成功。

## 自动测试

- [实际 unittest 输出](verification/unittest.txt)：50 项测试，0 失败、0 错误。
- [结构化结果](verification/summary.json)：运行时间、Python 版本、系统、命令和计数。
- [工程阶段计时](verification/worklog.json)：从首个文件创建到交付检查的可核验用时边界。

HTTP 接口测试使用显式测试替身，不计入真实服务成功证据。所有样例业务时钟固定为 `2026-10-28T10:00:00+08:00`；事件的 `observed_at` 是实际执行时间，不将两者混淆。
