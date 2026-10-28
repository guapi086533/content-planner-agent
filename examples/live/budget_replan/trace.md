# live-budget_replan 执行记录

- 状态：completed
- 模型：{"mode": "live", "name": "qwen3.8-27b", "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1"}
- 重放：False
- 费用合计：8.0 SIM（已发生 1.0，预留 7.0）

> offline 的决策来自固定规则，仅验证工程流程。工具均为合成模拟。

## 步骤 1：estimate_cost

依据：尊重 preferred_variant，先取得 premium 档位的真实费用与时间估算。

参数：
```json
{
  "variant": "premium",
  "reason": "尊重 preferred_variant，先取得 premium 档位的真实费用与时间估算。"
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
  "budget_gap_cents": 200,
  "deadline_gap_minutes": 0,
  "within_budget": false,
  "within_deadline": true,
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

后续动作：estimate_cost

## 步骤 2：estimate_cost

依据：premium 超预算被拒，改取可行的 standard 档位估算作为目标。

参数：
```json
{
  "variant": "standard",
  "reason": "premium 超预算被拒，改取可行的 standard 档位估算作为目标。"
}
```

实际返回：
```json
{
  "status": "ok",
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
      "budget_gap_cents": 200,
      "deadline_gap_minutes": 0,
      "within_budget": false,
      "within_deadline": true,
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

后续动作：search_materials

## 步骤 3：search_materials

依据：standard 需至少1个素材，先检索 primary 来源的校园秋日主题素材。

参数：
```json
{
  "query": "校园 秋日 短视频 落叶 操场 学生生活",
  "source": "primary",
  "reason": "standard 需至少1个素材，先检索 primary 来源的校园秋日主题素材。"
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

## 步骤 4：generate_script

依据：已有 standard 可行估算且素材满足最低要求，生成30秒短视频脚本。

参数：
```json
{
  "variant": "standard",
  "material_ids": [
    "campus-01",
    "campus-02"
  ],
  "angle": "以金色银杏步道开场，邀请学生拍摄秋日校园瞬间并参与剪辑挑战，用原片与成片对比展示创作乐趣。",
  "reason": "已有 standard 可行估算且素材满足最低要求，生成30秒短视频脚本。"
}
```

实际返回：
```json
{
  "status": "ok",
  "cached": false,
  "script": {
    "id": "script-b14b725529dd",
    "variant": "standard",
    "title": "校园秋日短视频挑战",
    "angle": "以金色银杏步道开场，邀请学生拍摄秋日校园瞬间并参与剪辑挑战，用原片与成片对比展示创作乐趣。",
    "format": "30 秒短视频",
    "material_ids": [
      "campus-01",
      "campus-02"
    ],
    "sections": [
      {
        "stage": "开场",
        "text": "以金色银杏步道开场，邀请学生拍摄秋日校园瞬间并参与剪辑挑战，用原片与成片对比展示创作乐趣。：用一个生活片段引出「校园秋日短视频挑战」。"
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

## 步骤 5：save_plan

依据：standard 脚本已成功且估算在预算与截止时间内，保存方案并预留制作费用。

参数：
```json
{
  "variant": "standard",
  "reason": "standard 脚本已成功且估算在预算与截止时间内，保存方案并预留制作费用。"
}
```

实际返回：
```json
{
  "status": "ok",
  "cached": false,
  "plan_id": "plan-c6c545337ac8",
  "total_cents": 800,
  "projected_ready_by": "2026-10-28T10:45:00+08:00"
}
```

后续动作：completed
