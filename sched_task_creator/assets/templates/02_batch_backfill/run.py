"""批量回溯执行者模板：读取 SCHED_CONFIG，处理单个单元（幂等）。

与 01_daily_producer 的 run.py 同构；多个单元由多个作业/attempt 并行处理，
每份作业处理一个单元（单元粒度即作业粒度）。
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_SCHED_SRC = os.environ.get("SCHED_SRC", "")
if _SCHED_SRC and os.path.isdir(_SCHED_SRC) and _SCHED_SRC not in sys.path:
    sys.path.insert(0, _SCHED_SRC)

from sched_task_sdk import ExecutorTask, run_task  # noqa: E402


def _ws() -> Path:
    return Path(os.environ.get("SCHED_WORKSPACE") or Path.cwd())


def _load_config() -> dict:
    rel = os.environ.get("SCHED_CONFIG") or ""
    p = _ws() / rel if rel else (_ws() / "config.json")
    return json.loads(p.read_text("utf-8")) if p.is_file() else {}


class UnitExecutor(ExecutorTask):
    def execute(self):
        cfg = _load_config()
        key = cfg.get("key")
        done = self.resume_data() or {}
        if done.get("done"):
            self.complete({"key": key, "skipped": "already_done"})
            return
        self.report_progress(0, True, "start")
        # 幂等：先查外部完成标记，再处理
        self._process(cfg)
        self.checkpoint({"done": True}, business_version=cfg.get("version") or "1",
                        progress={"done": 1})
        self.report_progress(1, False, "done", work_units=1)
        self.complete({"key": key, "count": 1})

    def _process(self, cfg):
        # 业务：处理该单元
        pass


def main() -> int:
    return run_task(UnitExecutor())


if __name__ == "__main__":
    sys.exit(main())