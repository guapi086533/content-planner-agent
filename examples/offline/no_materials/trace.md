# offline-no_materials 执行记录

- 状态：incomplete
- 模型：{"mode": "offline", "name": "offline-rules-v1"}
- 重放：False
- 费用合计：0.0 SIM（已发生 0.0，预留 0.0）

> offline 的决策来自固定规则，仅验证工程流程。工具均为合成模拟。

未完成原因：{"code": "NO_MATERIALS", "message": "两个来源均无法提供足量相关素材"}

## 步骤 1：estimate_cost

依据：先核对首选方案费用和时间

参数：
```json
{
  "variant": "premium",
  "reason": "先核对首选方案费用和时间"
}
```

实际返回：
```json
{
  "status": "ok",
  "variant": "premium",
  "total_cents": 1200,
  "spent_cents": 0,
  "script_cents": 200,
  "production_cents": 1000,
  "remaining_minutes": 89,
  "ready_by": "2026-10-28T11:29:00+08:00",
  "budget_gap_cents": 0,
  "deadline_gap_minutes": 0,
  "within_budget": true,
  "within_deadline": true,
  "feasible": true,
  "alternatives": [
    {
      "variant": "standard",
      "total_cents": 800,
      "spent_cents": 0,
      "script_cents": 100,
      "production_cents": 700,
      "remaining_minutes": 44,
      "ready_by": "2026-10-28T10:44:00+08:00",
      "budget_gap_cents": 0,
      "deadline_gap_minutes": 0,
      "within_budget": true,
      "within_deadline": true,
      "feasible": true
    },
    {
      "variant": "lean",
      "total_cents": 400,
      "spent_cents": 0,
      "script_cents": 100,
      "production_cents": 300,
      "remaining_minutes": 19,
      "ready_by": "2026-10-28T10:19:00+08:00",
      "budget_gap_cents": 0,
      "deadline_gap_minutes": 0,
      "within_budget": true,
      "within_deadline": true,
      "feasible": true
    }
  ]
}
```

后续动作：search_materials

## 步骤 2：search_materials

依据：当前素材不足，检索独立来源并保留已取得素材

参数：
```json
{
  "query": "深海矿业设备推广",
  "source": "primary",
  "reason": "当前素材不足，检索独立来源并保留已取得素材"
}
```

实际返回：
```json
{
  "status": "ok",
  "source": "primary",
  "materials": [],
  "count": 0,
  "retained_count": 0,
  "cached": false
}
```

后续动作：search_materials

## 步骤 3：search_materials

依据：当前素材不足，检索独立来源并保留已取得素材

参数：
```json
{
  "query": "深海矿业设备推广",
  "source": "archive",
  "reason": "当前素材不足，检索独立来源并保留已取得素材"
}
```

实际返回：
```json
{
  "status": "ok",
  "source": "archive",
  "materials": [],
  "count": 0,
  "retained_count": 0,
  "cached": false
}
```

后续动作：finish

## 步骤 4：finish

依据：两个来源均无法提供足量相关素材

参数：
```json
{
  "code": "NO_MATERIALS",
  "reason": "两个来源均无法提供足量相关素材"
}
```

实际返回：
```json
{
  "status": "stopped",
  "code": "NO_MATERIALS",
  "message": "两个来源均无法提供足量相关素材"
}
```

后续动作：incomplete
