"""每日执行者模板：读取 SCHED_CONFIG 指向的 per-date 配置，逐项幂等处理。

- 断点 done_ids + 幂等提交（外部写入前先查存在/用稳定键）。
- 外部短期不足 → report_shortage → exit 75。
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


class DailyExecutor(ExecutorTask):
    def execute(self):
        cfg = _load_config()
        date_str = cfg.get("date")
        items = self._fetch_items(cfg)          # 业务：获得待处理单元
        done = set((self.resume_data() or {}).get("done_ids", []))
        self.report_progress(len(done), True, "start", work_units=len(items))
        for it in items:
            key = it.key
            if key in done:
                continue
            self._process_one(it)               # 幂等：先查已有再写
            done.add(key)
            self.checkpoint({"done_ids": sorted(done)},
                            business_version=cfg.get("version") or date_str or "1",
                            progress={"done": len(done), "total": len(items)})
            self.report_progress(len(done), len(done) < len(items), "process",
                                 work_units=len(done))
        self.complete({"count": len(done), "date": date_str})

    def _fetch_items(self, cfg):
        # 业务：按 cfg 检索得到单元列表
        return []

    def _process_one(self, item):
        # 业务：处理单个单元（幂等）
        pass


def main() -> int:
    return run_task(DailyExecutor())


if __name__ == "__main__":
    sys.exit(main())