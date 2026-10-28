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
record = {"measurement": "本机首个项目文件 .gitignore 创建至本次交付检查；不等于候选人独立投入工时",
          "source": ".gitignore filesystem creation time (st_birthtime or st_ctime fallback)",
          "started_at": started.isoformat(), "checked_at": finished.isoformat(),
          "elapsed_minutes": round((finished - started).total_seconds() / 60, 2),
          "excluded": "前置需求阅读、用户澄清与早期环境/模型探测未单独计时；后续候选人修改、远端提交未发生",
          "remaining": ["真实模型成功决策路径", "候选人独立修改和复验记录", "GitHub 发布及远端 CI"]}
(root / "examples/verification/worklog.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(record, ensure_ascii=False, indent=2))
