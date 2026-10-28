# offline-partial_success 执行记录

- 状态：completed
- 模型：{"mode": "offline", "name": "offline-rules-v1"}
- 重放：False
- 费用合计：12.0 SIM（已发生 2.0，预留 10.0）

> offline 的决策来自固定规则，仅验证工程流程。工具均为合成模拟。

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
  "currency": "SIM",
  "total_units": 12.0,
  "budget_units": 20.0,
  "budget_gap_units": 0.0,
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
      "currency": "SIM",
      "total_units": 8.0,
      "budget_units": 20.0,
      "budget_gap_units": 0.0,
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
      "currency": "SIM",
      "total_units": 4.0,
      "budget_units": 20.0,
      "budget_gap_units": 0.0,
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
  "query": "校园秋日短视频挑战",
  "source": "primary",
  "reason": "当前素材不足，检索独立来源并保留已取得素材"
}
```

实际返回：
```json
{
  "status": "partial",
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
    }
  ],
  "count": 1,
  "retained_count": 1,
  "cached": false,
  "warning": "本来源仅部分分片成功；已成功素材保留，可检索 archive 补充或降低素材需求。"
}
```

后续动作：search_materials

## 步骤 3：search_materials

依据：当前素材不足，检索独立来源并保留已取得素材

参数：
```json
{
  "query": "校园秋日短视频挑战",
  "source": "archive",
  "reason": "当前素材不足，检索独立来源并保留已取得素材"
}
```

实际返回：
```json
{
  "status": "ok",
  "source": "archive",
  "materials": [
    {
      "id": "campus-03",
      "source": "archive",
      "title": "宿舍创作花絮",
      "tags": [
        "校园",
        "秋日",
        "剪辑",
        "挑战",
        "短视频",
        "campus",
        "autumn"
      ],
      "kind": "video",
      "content": "合成镜头：两位同学合作拍摄十秒生活片段，适合参与示范。",
      "license": "synthetic-demo"
    },
    {
      "id": "campus-04",
      "source": "archive",
      "title": "活动投稿卡片",
      "tags": [
        "校园",
        "秋日",
        "挑战",
        "短视频",
        "campus"
      ],
      "kind": "image",
      "content": "合成卡片：发布作品并附活动话题；奖项与奖励尚未设定，不得虚构。",
      "license": "synthetic-demo"
    }
  ],
  "count": 2,
  "retained_count": 3,
  "cached": false
}
```

后续动作：generate_script

## 步骤 4：generate_script

依据：该档位估算可行且素材满足依赖，生成脚本

参数：
```json
{
  "variant": "premium",
  "material_ids": [
    "campus-01",
    "campus-03"
  ],
  "angle": "用校园生活片段呈现主题，鼓励低门槛参与",
  "reason": "该档位估算可行且素材满足依赖，生成脚本"
}
```

实际返回：
```json
{
  "status": "ok",
  "cached": false,
  "script": {
    "id": "script-9fcfbb27fe00",
    "variant": "premium",
    "title": "校园秋日短视频挑战",
    "angle": "用校园生活片段呈现主题，鼓励低门槛参与",
    "format": "60 秒短视频",
    "material_ids": [
      "campus-01",
      "campus-03"
    ],
    "sections": [
      {
        "stage": "开场",
        "text": "用校园生活片段呈现主题，鼓励低门槛参与：用一个生活片段引出「校园秋日短视频挑战」。"
      },
      {
        "stage": "主体",
        "text": "合成镜头：学生沿金色银杏步道行走，可用于活动开场。 / 合成镜头：两位同学合作拍摄十秒生活片段，适合参与示范。"
      },
      {
        "stage": "行动",
        "text": "邀请观众围绕主题创作并发布作品；具体渠道、活动话题与审核规则由运营确认。"
      }
    ],
    "generator": "local-template-v1",
    "requires_editorial_review": true
  },
  "charged_cents": 200
}
```

后续动作：save_plan

## 步骤 5：save_plan

依据：复用成功脚本，校验最终费用和时间后保存

参数：
```json
{
  "variant": "premium",
  "reason": "复用成功脚本，校验最终费用和时间后保存"
}
```

实际返回：
```json
{
  "status": "ok",
  "cached": false,
  "plan_id": "plan-839023dc80ba",
  "total_cents": 1200,
  "projected_ready_by": "2026-10-28T11:31:00+08:00"
}
```

后续动作：completed
