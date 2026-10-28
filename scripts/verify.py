"""Run the executable suite and save genuine stdout plus machine-readable results."""

import io
import json
import platform
import sys
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
stream = io.StringIO()
started = time.perf_counter()
suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"))
result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
elapsed = time.perf_counter() - started
directory = ROOT / "examples" / "verification"
directory.mkdir(parents=True, exist_ok=True)
(directory / "unittest.txt").write_text(stream.getvalue(), encoding="utf-8")
summary = {"executed_at": datetime.now(timezone.utc).isoformat(), "python": platform.python_version(),
           "platform": platform.system(), "command": "python scripts/verify.py", "tests_run": result.testsRun,
           "failures": len(result.failures), "errors": len(result.errors), "skipped": len(result.skipped),
           "elapsed_seconds": round(elapsed, 3), "passed": result.wasSuccessful(),
           "network": "HTTP adapter tests use explicit unittest mocks; no live requests in this suite."}
(directory / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(stream.getvalue())
print(json.dumps(summary, ensure_ascii=False))
sys.exit(0 if result.wasSuccessful() else 1)
