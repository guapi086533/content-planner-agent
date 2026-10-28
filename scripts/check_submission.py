"""Check repository evidence and local links without printing credential values."""

import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
required = ["README.md", "requirements.txt", "pyproject.toml", ".env.example",
            "docs/01-requirements.md", "docs/02-solution.md", "docs/03-evaluation.md",
            "docs/04-ai-usage.md", "docs/05-retrospective.md", "examples/offline/summary.json",
            "examples/live/summary.json", "examples/verification/summary.json"]
errors = [f"missing: {name}" for name in required if not (ROOT / name).is_file()]
paths = [p for p in ROOT.rglob("*") if p.is_file() and not any(part in (".git", "__pycache__", "runs") or part.endswith(".egg-info") for part in p.relative_to(ROOT).parts)]
secrets = [os.environ.get(name, "") for name in ("AGENT_API_KEY", "DASHSCOPE_API_KEY", "OPENAI_API_KEY")]
secrets = [value.encode() for value in secrets if len(value) >= 12]
for path in paths:
    content = path.read_bytes()
    if any(secret in content for secret in secrets):
        errors.append(f"credential value found in: {path.relative_to(ROOT)}")
    if path.suffix == ".md":
        for target in re.findall(r"\]\(([^)]+)\)", content.decode("utf-8")):
            if "://" in target or target.startswith("#"):
                continue
            relative = unquote(target.split("#", 1)[0])
            if relative and not (path.parent / relative).exists():
                errors.append(f"broken link: {path.relative_to(ROOT)} -> {relative}")
offline = json.loads((ROOT / "examples/offline/summary.json").read_text(encoding="utf-8"))
if len(offline["cases"]) != 14 or not all(c["matches_expected_status_and_cost"] for c in offline["cases"]):
    errors.append("offline evidence does not cover all 14 expected cases")
for path in (ROOT / "examples").rglob("result.json"):
    report = json.loads(path.read_text(encoding="utf-8"))
    ledger = sum(entry["cents"] for entry in report["cost"]["ledger"])
    if ledger != round(report["cost"]["total_units"] * 100):
        errors.append(f"ledger mismatch: {path.relative_to(ROOT)}")
    if report["status"] == "completed":
        if not report["saved_plan"] or ledger > report["request"]["budget_cents"]:
            errors.append(f"invalid completed state: {path.relative_to(ROOT)}")
        if not all(s["status"] == "succeeded" for s in report["steps"].values()):
            errors.append(f"completed state has unfinished agent steps: {path.relative_to(ROOT)}")
tests = json.loads((ROOT / "examples/verification/summary.json").read_text(encoding="utf-8"))
if not tests["passed"] or tests["tests_run"] < 50:
    errors.append("tests are not passing or not current")
tracked = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True)
if tracked.returncode == 0:
    for name in tracked.stdout.decode("utf-8").split("\0"):
        if name and (name == ".env" or name.endswith((".db", ".sqlite3", ".pyc")) or name.startswith("runs/")):
            errors.append(f"unexpected runtime file tracked: {name}")
summary = {"checked_at": datetime.now(timezone.utc).isoformat(), "files_checked": len(paths),
           "offline_cases": len(offline["cases"]), "tests_run": tests["tests_run"], "errors": errors, "passed": not errors,
           "live_model_effectiveness": "not verified; see examples/live and docs/03-evaluation.md"}
(ROOT / "examples/verification/submission-check.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(summary, ensure_ascii=False, indent=2))
raise SystemExit(0 if not errors else 1)
