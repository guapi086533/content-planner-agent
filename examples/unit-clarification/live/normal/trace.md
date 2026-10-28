# live-normal 执行记录

- 状态：completed
- 模型：{"mode": "live", "name": "qwen3.8-27b", "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1"}
- 重放：False
- 费用合计：12.0 SIM（已发生 2.0，预留 10.0）

> offline 的决策来自固定规则，仅验证工程流程。工具均为合成模拟。

## 步骤 1：estimate_cost

依据：preferred_variant 为 premium，先取得该档位的真实费用与时间估算再决定后续。

参数：
```json
{
  "variant": "premium",
  "reason": "preferred_variant 为 premium，先取得该档位的真实费用与时间估算再决定后续。"
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

依据：premium 估算可行（12 SIM、89 分钟），需至少 2 个素材，先从 primary 检索相关素材。

参数：
```json
{
  "query": "校园 秋日 落叶 学生 活动 短视频素材",
  "source": "primary",
  "reason": "premium 估算可行（12 SIM、89 分钟），需至少 2 个素材，先从 primary 检索相关素材。"
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

## 步骤 3：generate_script

依据：premium 估算可行且已取到 2 个足量素材（满足 min_materials=2），据此生成脚本。

参数：
```json
{
  "variant": "premium",
  "material_ids": [
    "campus-01",
    "campus-02"
  ],
  "angle": "以银杏步道开场带入秋日校园氛围，再展示原片到成片的剪辑对比，引导学生参与短视频挑战。",
  "reason": "premium 估算可行且已取到 2 个足量素材（满足 min_materials=2），据此生成脚本。"
}
```

实际返回：
```json
{
  "status": "ok",
  "cached": false,
  "script": {
    "id": "script-ff1a9ec62ca4",
    "variant": "premium",
    "title": "校园秋日短视频挑战",
    "angle": "以银杏步道开场带入秋日校园氛围，再展示原片到成片的剪辑对比，引导学生参与短视频挑战。",
    "format": "60 秒短视频",
    "material_ids": [
      "campus-01",
      "campus-02"
    ],
    "sections": [
      {
        "stage": "开场",
        "text": "以银杏步道开场带入秋日校园氛围，再展示原片到成片的剪辑对比，引导学生参与短视频挑战。：用一个生活片段引出「校园秋日短视频挑战」。"
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
  "charged_cents": 200
}
```

后续动作：save_plan

## 步骤 4：save_plan

依据：premium 估算可行、脚本已成功生成，满足保存依赖，据此校验并预留制作费用保存方案。

参数：
```json
{
  "variant": "premium",
  "reason": "premium 估算可行、脚本已成功生成，满足保存依赖，据此校验并预留制作费用保存方案。"
}
```

实际返回：
```json
{
  "status": "ok",
  "cached": false,
  "plan_id": "plan-e1c6d1f3a3e4",
  "total_cents": 1200,
  "projected_ready_by": "2026-10-28T11:30:00+08:00"
}
```

后续动作：completed
