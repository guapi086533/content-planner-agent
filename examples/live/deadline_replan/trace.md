# live-deadline_replan 执行记录

- 状态：completed
- 模型：{"mode": "live", "name": "qwen3.8-27b", "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1"}
- 重放：False
- 费用合计：4.0 SIM（已发生 1.0，预留 3.0）

> offline 的决策来自固定规则，仅验证工程流程。工具均为合成模拟。

## 步骤 1：estimate_cost

依据：优先尊重 preferred_variant，先取精剪档位的真实费用与时间估算。

参数：
```json
{
  "variant": "premium",
  "reason": "优先尊重 preferred_variant，先取精剪档位的真实费用与时间估算。"
}
```

实际返回：
```json
{
  "status": "rejected",
  "variant": "premium",
  "total_cents": 1200,
  "spent_cents": 0,
  "script_cents": 200,
  "production_cents": 1000,
  "remaining_minutes": 89,
  "ready_by": "2026-10-28T11:29:00+08:00",
  "budget_gap_cents": 0,
  "deadline_gap_minutes": 69,
  "within_budget": true,
  "within_deadline": false,
  "feasible": false,
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
      "deadline_gap_minutes": 24,
      "within_budget": true,
      "within_deadline": false,
      "feasible": false
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

后续动作：estimate_cost

## 步骤 2：estimate_cost

依据：premium 超截止时间，改取次近档 standard 的真实估算以确认是否可行。

参数：
```json
{
  "variant": "standard",
  "reason": "premium 超截止时间，改取次近档 standard 的真实估算以确认是否可行。"
}
```

实际返回：
```json
{
  "status": "rejected",
  "variant": "standard",
  "total_cents": 800,
  "spent_cents": 0,
  "script_cents": 100,
  "production_cents": 700,
  "remaining_minutes": 44,
  "ready_by": "2026-10-28T10:44:00+08:00",
  "budget_gap_cents": 0,
  "deadline_gap_minutes": 24,
  "within_budget": true,
  "within_deadline": false,
  "feasible": false,
  "alternatives": [
    {
      "variant": "premium",
      "total_cents": 1200,
      "spent_cents": 0,
      "script_cents": 200,
      "production_cents": 1000,
      "remaining_minutes": 89,
      "ready_by": "2026-10-28T11:29:00+08:00",
      "budget_gap_cents": 0,
      "deadline_gap_minutes": 69,
      "within_budget": true,
      "within_deadline": false,
      "feasible": false
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

后续动作：estimate_cost

## 步骤 3：estimate_cost

依据：premium 与 standard 均超截止时间，仅 lean 在预算与时间内可行，取其实测估算确认。

参数：
```json
{
  "variant": "lean",
  "reason": "premium 与 standard 均超截止时间，仅 lean 在预算与时间内可行，取其实测估算确认。"
}
```

实际返回：
```json
{
  "status": "ok",
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
  "feasible": true,
  "alternatives": [
    {
      "variant": "premium",
      "total_cents": 1200,
      "spent_cents": 0,
      "script_cents": 200,
      "production_cents": 1000,
      "remaining_minutes": 89,
      "ready_by": "2026-10-28T11:29:00+08:00",
      "budget_gap_cents": 0,
      "deadline_gap_minutes": 69,
      "within_budget": true,
      "within_deadline": false,
      "feasible": false
    },
    {
      "variant": "standard",
      "total_cents": 800,
      "spent_cents": 0,
      "script_cents": 100,
      "production_cents": 700,
      "remaining_minutes": 44,
      "ready_by": "2026-10-28T10:44:00+08:00",
      "budget_gap_cents": 0,
      "deadline_gap_minutes": 24,
      "within_budget": true,
      "within_deadline": false,
      "feasible": false
    }
  ]
}
```

后续动作：search_materials

## 步骤 4：search_materials

依据：lean 需至少1个素材，先检索 primary 来源的校园秋日相关素材。

参数：
```json
{
  "query": "校园秋日 落叶 操场 学生 生活场景",
  "source": "primary",
  "reason": "lean 需至少1个素材，先检索 primary 来源的校园秋日相关素材。"
}
```

实际返回：
```json
{
  "status": "ok",
  "source": "primary",
  "materials": [
    {
      "id": "campus-01",
      "source": "primary",
      "title": "校园银杏步道",
      "tags": [
        "校园",
        "秋日",
        "秋季",
        "短视频",
        "campus",
        "autumn"
      ],
      "kind": "video",
      "content": "合成镜头：学生沿金色银杏步道行走，可用于活动开场。",
      "license": "synthetic-demo"
    },
    {
      "id": "campus-02",
      "source": "primary",
      "title": "剪辑前后对比",
      "tags": [
        "校园",
        "剪辑",
        "短视频",
        "挑战",
        "campus"
      ],
      "kind": "image",
      "content": "合成画面：手机原片与调色成片对比，不含真实产品效果承诺。",
      "license": "synthetic-demo"
    }
  ],
  "count": 2,
  "retained_count": 2,
  "cached": false
}
```

后续动作：generate_script

## 步骤 5：generate_script

依据：lean 档位估算可行且已有2个相关素材，满足最少1个要求，据此生成图文活动脚本。

参数：
```json
{
  "variant": "lean",
  "material_ids": [
    "campus-01",
    "campus-02"
  ],
  "angle": "以校园银杏步道的金色秋日氛围开场，用三张图文卡片呈现「秋日校园挑战」的参与方式与打卡场景，鼓励同学记录身边的秋意瞬间。",
  "reason": "lean 档位估算可行且已有2个相关素材，满足最少1个要求，据此生成图文活动脚本。"
}
```

实际返回：
```json
{
  "status": "ok",
  "cached": false,
  "script": {
    "id": "script-d0d258d35676",
    "variant": "lean",
    "title": "校园秋日短视频挑战",
    "angle": "以校园银杏步道的金色秋日氛围开场，用三张图文卡片呈现「秋日校园挑战」的参与方式与打卡场景，鼓励同学记录身边的秋意瞬间。",
    "format": "三张图文卡片",
    "material_ids": [
      "campus-01",
      "campus-02"
    ],
    "sections": [
      {
        "stage": "开场",
        "text": "以校园银杏步道的金色秋日氛围开场，用三张图文卡片呈现「秋日校园挑战」的参与方式与打卡场景，鼓励同学记录身边的秋意瞬间。：用一个生活片段引出「校园秋日短视频挑战」。"
      },
      {
        "stage": "主体",
        "text": "合成镜头：学生沿金色银杏步道行走，可用于活动开场。 / 合成画面：手机原片与调色成片对比，不含真实产品效果承诺。"
      },
      {
        "stage": "行动",
        "text": "邀请观众围绕主题创作并发布作品；具体渠道、活动话题与审核规则由运营确认。"
      }
    ],
    "generator": "local-template-v1",
    "requires_editorial_review": true
  },
  "charged_cents": 100
}
```

后续动作：save_plan

## 步骤 6：save_plan

依据：lean 估算可行且脚本已成功，依赖齐备，保存方案并预留制作费用。

参数：
```json
{
  "variant": "lean",
  "reason": "lean 估算可行且脚本已成功，依赖齐备，保存方案并预留制作费用。"
}
```

实际返回：
```json
{
  "status": "ok",
  "cached": false,
  "plan_id": "plan-119e33737063",
  "total_cents": 400,
  "projected_ready_by": "2026-10-28T10:20:00+08:00"
}
```

后续动作：completed
