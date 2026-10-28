# offline-deadline_impossible 执行记录

- 状态：incomplete
- 模型：{"mode": "offline", "name": "offline-rules-v1"}
- 重放：False
- 费用合计：0.0 SIM（已发生 0.0，预留 0.0）

> offline 的决策来自固定规则，仅验证工程流程。工具均为合成模拟。

未完成原因：{"code": "NO_FEASIBLE_PLAN", "message": "所有档位均超预算或超时，缺口见实际估算结果", "observed_gaps": [{"variant": "premium", "total_cents": 1200, "spent_cents": 0, "currency": "SIM", "total_units": 12.0, "budget_units": 20.0, "budget_gap_units": 0.0, "script_cents": 200, "production_cents": 1000, "remaining_minutes": 89, "ready_by": "2026-10-28T11:29:00+08:00", "budget_gap_cents": 0, "deadline_gap_minutes": 79, "within_budget": true, "within_deadline": false, "feasible": false}, {"variant": "standard", "total_cents": 800, "spent_cents": 0, "currency": "SIM", "total_units": 8.0, "budget_units": 20.0, "budget_gap_units": 0.0, "script_cents": 100, "production_cents": 700, "remaining_minutes": 44, "ready_by": "2026-10-28T10:44:00+08:00", "budget_gap_cents": 0, "deadline_gap_minutes": 34, "within_budget": true, "within_deadline": false, "feasible": false}, {"variant": "lean", "total_cents": 400, "spent_cents": 0, "currency": "SIM", "total_units": 4.0, "budget_units": 20.0, "budget_gap_units": 0.0, "script_cents": 100, "production_cents": 300, "remaining_minutes": 19, "ready_by": "2026-10-28T10:19:00+08:00", "budget_gap_cents": 0, "deadline_gap_minutes": 9, "within_budget": true, "within_deadline": false, "feasible": false}]}

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
  "status": "rejected",
  "variant": "premium",
  "total_cents": 1200,
  "spent_cents": 0,
  "currency": "SIM",
  "total_units": 12.0,
  "budget_units": 20.0,
  "budget_gap_units": 0.0,
  "script_cents": 200,
  "production_cents": 1000,
  "remaining_minutes": 89,
  "ready_by": "2026-10-28T11:29:00+08:00",
  "budget_gap_cents": 0,
  "deadline_gap_minutes": 79,
  "within_budget": true,
  "within_deadline": false,
  "feasible": false,
  "alternatives": [
    {
      "variant": "standard",
      "total_cents": 800,
      "spent_cents": 0,
      "currency": "SIM",
      "total_units": 8.0,
      "budget_units": 20.0,
      "budget_gap_units": 0.0,
      "script_cents": 100,
      "production_cents": 700,
      "remaining_minutes": 44,
      "ready_by": "2026-10-28T10:44:00+08:00",
      "budget_gap_cents": 0,
      "deadline_gap_minutes": 34,
      "within_budget": true,
      "within_deadline": false,
      "feasible": false
    },
    {
      "variant": "lean",
      "total_cents": 400,
      "spent_cents": 0,
      "currency": "SIM",
      "total_units": 4.0,
      "budget_units": 20.0,
      "budget_gap_units": 0.0,
      "script_cents": 100,
      "production_cents": 300,
      "remaining_minutes": 19,
      "ready_by": "2026-10-28T10:19:00+08:00",
      "budget_gap_cents": 0,
      "deadline_gap_minutes": 9,
      "within_budget": true,
      "within_deadline": false,
      "feasible": false
    }
  ]
}
```

后续动作：estimate_cost

## 步骤 2：estimate_cost

依据：上次估算不满足预算或时间，改估替代档位

参数：
```json
{
  "variant": "standard",
  "reason": "上次估算不满足预算或时间，改估替代档位"
}
```

实际返回：
```json
{
  "status": "rejected",
  "variant": "standard",
  "total_cents": 800,
  "spent_cents": 0,
  "currency": "SIM",
  "total_units": 8.0,
  "budget_units": 20.0,
  "budget_gap_units": 0.0,
  "script_cents": 100,
  "production_cents": 700,
  "remaining_minutes": 44,
  "ready_by": "2026-10-28T10:44:00+08:00",
  "budget_gap_cents": 0,
  "deadline_gap_minutes": 34,
  "within_budget": true,
  "within_deadline": false,
  "feasible": false,
  "alternatives": [
    {
      "variant": "premium",
      "total_cents": 1200,
      "spent_cents": 0,
      "currency": "SIM",
      "total_units": 12.0,
      "budget_units": 20.0,
      "budget_gap_units": 0.0,
      "script_cents": 200,
      "production_cents": 1000,
      "remaining_minutes": 89,
      "ready_by": "2026-10-28T11:29:00+08:00",
      "budget_gap_cents": 0,
      "deadline_gap_minutes": 79,
      "within_budget": true,
      "within_deadline": false,
      "feasible": false
    },
    {
      "variant": "lean",
      "total_cents": 400,
      "spent_cents": 0,
      "currency": "SIM",
      "total_units": 4.0,
      "budget_units": 20.0,
      "budget_gap_units": 0.0,
      "script_cents": 100,
      "production_cents": 300,
      "remaining_minutes": 19,
      "ready_by": "2026-10-28T10:19:00+08:00",
      "budget_gap_cents": 0,
      "deadline_gap_minutes": 9,
      "within_budget": true,
      "within_deadline": false,
      "feasible": false
    }
  ]
}
```

后续动作：estimate_cost

## 步骤 3：estimate_cost

依据：上次估算不满足预算或时间，改估替代档位

参数：
```json
{
  "variant": "lean",
  "reason": "上次估算不满足预算或时间，改估替代档位"
}
```

实际返回：
```json
{
  "status": "rejected",
  "variant": "lean",
  "total_cents": 400,
  "spent_cents": 0,
  "currency": "SIM",
  "total_units": 4.0,
  "budget_units": 20.0,
  "budget_gap_units": 0.0,
  "script_cents": 100,
  "production_cents": 300,
  "remaining_minutes": 19,
  "ready_by": "2026-10-28T10:19:00+08:00",
  "budget_gap_cents": 0,
  "deadline_gap_minutes": 9,
  "within_budget": true,
  "within_deadline": false,
  "feasible": false,
  "alternatives": [
    {
      "variant": "premium",
      "total_cents": 1200,
      "spent_cents": 0,
      "currency": "SIM",
      "total_units": 12.0,
      "budget_units": 20.0,
      "budget_gap_units": 0.0,
      "script_cents": 200,
      "production_cents": 1000,
      "remaining_minutes": 89,
      "ready_by": "2026-10-28T11:29:00+08:00",
      "budget_gap_cents": 0,
      "deadline_gap_minutes": 79,
      "within_budget": true,
      "within_deadline": false,
      "feasible": false
    },
    {
      "variant": "standard",
      "total_cents": 800,
      "spent_cents": 0,
      "currency": "SIM",
      "total_units": 8.0,
      "budget_units": 20.0,
      "budget_gap_units": 0.0,
      "script_cents": 100,
      "production_cents": 700,
      "remaining_minutes": 44,
      "ready_by": "2026-10-28T10:44:00+08:00",
      "budget_gap_cents": 0,
      "deadline_gap_minutes": 34,
      "within_budget": true,
      "within_deadline": false,
      "feasible": false
    }
  ]
}
```

后续动作：finish

## 步骤 4：finish

依据：所有档位均超预算或超时，缺口见实际估算结果

参数：
```json
{
  "code": "NO_FEASIBLE_PLAN",
  "reason": "所有档位均超预算或超时，缺口见实际估算结果"
}
```

实际返回：
```json
{
  "status": "stopped",
  "code": "NO_FEASIBLE_PLAN",
  "message": "所有档位均超预算或超时，缺口见实际估算结果",
  "observed_gaps": [
    {
      "variant": "premium",
      "total_cents": 1200,
      "spent_cents": 0,
      "currency": "SIM",
      "total_units": 12.0,
      "budget_units": 20.0,
      "budget_gap_units": 0.0,
      "script_cents": 200,
      "production_cents": 1000,
      "remaining_minutes": 89,
      "ready_by": "2026-10-28T11:29:00+08:00",
      "budget_gap_cents": 0,
      "deadline_gap_minutes": 79,
      "within_budget": true,
      "within_deadline": false,
      "feasible": false
    },
    {
      "variant": "standard",
      "total_cents": 800,
      "spent_cents": 0,
      "currency": "SIM",
      "total_units": 8.0,
      "budget_units": 20.0,
      "budget_gap_units": 0.0,
      "script_cents": 100,
      "production_cents": 700,
      "remaining_minutes": 44,
      "ready_by": "2026-10-28T10:44:00+08:00",
      "budget_gap_cents": 0,
      "deadline_gap_minutes": 34,
      "within_budget": true,
      "within_deadline": false,
      "feasible": false
    },
    {
      "variant": "lean",
      "total_cents": 400,
      "spent_cents": 0,
      "currency": "SIM",
      "total_units": 4.0,
      "budget_units": 20.0,
      "budget_gap_units": 0.0,
      "script_cents": 100,
      "production_cents": 300,
      "remaining_minutes": 19,
      "ready_by": "2026-10-28T10:19:00+08:00",
      "budget_gap_cents": 0,
      "deadline_gap_minutes": 9,
      "within_budget": true,
      "within_deadline": false,
      "feasible": false
    }
  ]
}
```

后续动作：incomplete
