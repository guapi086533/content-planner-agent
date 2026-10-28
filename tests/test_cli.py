import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class CliTests(unittest.TestCase):
    def test_cli_exports_result_trace_and_plan_then_replays(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "input.json"
            source.write_text(json.dumps({"topic": "校园秋日短视频挑战", "budget": 10, "deadline": "2099-10-28T18:00:00+08:00"}), encoding="utf-8")
            command = [sys.executable, "-m", "content_agent", "--input", str(source), "--mode", "offline", "--db", str(root / "state.sqlite3"), "--output", str(root / "output")]
            first = subprocess.run(command, capture_output=True, encoding="utf-8", timeout=20)
            self.assertEqual(first.returncode, 0, first.stderr)
            for name in ("result.json", "trace.jsonl", "trace.md", "plan.json", "plan.md"):
                self.assertTrue((root / "output" / name).is_file(), name)
            second = subprocess.run(command, capture_output=True, encoding="utf-8", timeout=20)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertTrue(json.loads(second.stdout)["replayed"])
            report = json.loads((root / "output" / "result.json").read_text(encoding="utf-8"))
            self.assertEqual(report["cost"]["total_units"], 8)
            self.assertEqual(report["saved_plan"]["variant"], "standard")

    def test_cli_missing_input_returns_exit_2_and_removes_stale_plan(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            output = root / "output"
            output.mkdir()
            (output / "plan.md").write_text("stale generated plan", encoding="utf-8")
            (output / "plan.json").write_text("{}", encoding="utf-8")
            source = root / "input.json"
            source.write_text('{"topic":"校园", "deadline":"2099-10-28T18:00:00+08:00"}', encoding="utf-8")
            result = subprocess.run([sys.executable, "-m", "content_agent", "--input", str(source), "--mode", "offline", "--db", str(root / "state.sqlite3"), "--output", str(output)], capture_output=True, encoding="utf-8", timeout=20)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(json.loads(result.stdout)["status"], "needs_input")
            self.assertFalse((output / "plan.md").exists())
            self.assertFalse((output / "plan.json").exists())
