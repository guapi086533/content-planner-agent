"""SQLite checkpoints and saved plans commit together; no external side effects."""

from __future__ import annotations

import json
import sqlite3
import time
import uuid
from pathlib import Path


class StoreError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


class Store:
    def __init__(self, path: str | Path):
        if str(path) != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(path), timeout=5)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY, fingerprint TEXT NOT NULL, state TEXT NOT NULL,
                owner TEXT, lease_until REAL NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS plans (
                job_id TEXT PRIMARY KEY REFERENCES jobs(id), body TEXT NOT NULL
            );
        """)
        self.owner = uuid.uuid4().hex

    def acquire(self, initial: dict, fingerprint: str, resume: bool) -> tuple[dict, bool]:
        self.db.execute("BEGIN IMMEDIATE")
        try:
            row = self.db.execute("SELECT fingerprint,state,owner,lease_until FROM jobs WHERE id=?", (initial["request_id"],)).fetchone()
            if row:
                if row[0] != fingerprint:
                    raise StoreError("ID_CONFLICT", "相同 request_id 对应不同输入，请使用新的 request_id")
                if row[2] and row[3] > time.time():
                    raise StoreError("JOB_BUSY", "任务正在另一执行器运行，请稍后重试")
                state = json.loads(row[1])
                if state["status"] == "completed" or not resume:
                    if state["status"] == "running":
                        state["status"] = "incomplete"
                        state["reason"] = {"code": "INTERRUPTED", "message": "前次执行中断；成功步骤已保留，可显式 --resume"}
                        self.db.execute("UPDATE jobs SET state=?,owner=NULL,lease_until=0 WHERE id=?", (json.dumps(state, ensure_ascii=False), initial["request_id"]))
                    self.db.commit()
                    return state, True
                self.db.execute("UPDATE jobs SET owner=?,lease_until=? WHERE id=?", (self.owner, time.time() + 300, initial["request_id"]))
            else:
                state = initial
                self.db.execute("INSERT INTO jobs VALUES (?,?,?,?,?)", (initial["request_id"], fingerprint, json.dumps(state, ensure_ascii=False), self.owner, time.time() + 300))
            self.db.commit()
            return state, False
        except BaseException:
            self.db.rollback()
            raise

    def checkpoint(self, state: dict) -> None:
        with self.db:
            cursor = self.db.execute("UPDATE jobs SET state=?,lease_until=? WHERE id=? AND owner=?", (json.dumps(state, ensure_ascii=False, allow_nan=False), time.time() + 300, state["request_id"], self.owner))
            if cursor.rowcount != 1:
                raise StoreError("LEASE_LOST", "任务执行租约已失效")
            if state["saved_plan"] is not None:
                self.db.execute("INSERT OR IGNORE INTO plans VALUES (?,?)", (state["request_id"], json.dumps(state["saved_plan"], ensure_ascii=False)))

    def release(self, request_id: str) -> None:
        with self.db:
            self.db.execute("UPDATE jobs SET owner=NULL,lease_until=0 WHERE id=? AND owner=?", (request_id, self.owner))

    def close(self) -> None:
        self.db.close()
