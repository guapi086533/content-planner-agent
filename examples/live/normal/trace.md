# live-normal 执行记录

- 状态：incomplete
- 模型：{"mode": "live", "name": "qwen-plus", "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1"}
- 重放：False
- 费用合计：0.0 SIM（已发生 0.0，预留 0.0）

> offline 的决策来自固定规则，仅验证工程流程。工具均为合成模拟。

未完成原因：{"code": "MODEL_UNAVAILABLE", "message": "模型服务 HTTP 403，错误码 AllocationQuota.FreeTierOnly；未回退到 Mock", "http_status": 403}

## 步骤 1：模型错误

{"sequence": 1, "run": 1, "kind": "model_error", "decision_source": "live", "observed_at": "2026-10-28T13:50:12+00:00", "code": "MODEL_UNAVAILABLE", "message": "模型服务 HTTP 403，错误码 AllocationQuota.FreeTierOnly；未回退到 Mock", "http_status": 403}
