"""Record the measurable implementation interval without inventing candidate time."""

import json
from datetime import datetime, timezone
from pathlib import Path

root = Path(__file__).resolve().parents[1]
metadata = (root / ".gitignore").stat()
birth = getattr(metadata, "st_birthtime", None)
if birth is None:
    # Windows creation time is available as st_ctime; on other systems this is only a proxy.
    birth = metadata.st_ctime
started = datetime.fromtimestamp(birth, timezone.utc)
finished = datetime.now(timezone.utc)
previous_path = root / "examples/verification/worklog.json"
previous = json.loads(previous_path.read_text(encoding="utf-8")) if previous_path.exists() else {}
record = {"measurement": "首个项目文件创建至本次检查的累计墙钟时间，包含轮次间沟通等待；不等于候选人独立投入工时",
          "source": ".gitignore filesystem creation time (st_birthtime or st_ctime fallback)",
          "started_at": started.isoformat(), "checked_at": finished.isoformat(),
          "elapsed_minutes": round((finished - started).total_seconds() / 60, 2),
          "initial_implementation_minutes": previous.get("initial_implementation_minutes", previous.get("elapsed_minutes")),
          "excluded": "前置需求阅读、用户澄清与早期环境/模型探测未单独计时；后续候选人修改、远端提交未发生",
          "completed_live_verification": "14 组真实模型场景及单位修正后的 3 组针对性复验",
          "remaining": ["候选人独立修改和复验记录", "GitHub 发布及远端 CI"]}
(root / "examples/verification/worklog.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(record, ensure_ascii=False, indent=2))
