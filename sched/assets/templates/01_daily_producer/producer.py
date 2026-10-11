"""每日生产者模板：每天固定时刻发现目标日期并发布一个就绪作业。

- 稳定事件标识 = 目标日期；cursor 记「最后已发布日期」，避免重复发布。
- 参数写入 per-date 配置文件，经 env/input_refs 引用（不靠 job_id 反推）。
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

_SCHED_SRC = os.environ.get("SCHED_SRC", "/mnt/data01/projects/scheduler")
if _SCHED_SRC and os.path.isdir(_SCHED_SRC) and _SCHED_SRC not in sys.path:
    sys.path.insert(0, _SCHED_SRC)

from sched_task_sdk import Producer, run_producer  # noqa: E402

BEIJING = ZoneInfo("Asia/Shanghai")


def _ws() -> Path:
    return Path(os.environ.get("SCHED_WORKSPACE") or Path(__file__).resolve().parent)


def _cfg() -> dict:
    p = _ws() / "config.json"
    return json.loads(p.read_text("utf-8")) if p.is_file() else {}


class DailyProducer(Producer):
    def discover(self, cursor):
        cfg = _cfg()
        now = datetime.now(BEIJING)
        if now.hour < int(cfg.get("run_at_hour", 15)):
            return cursor, []
        target = (now.date() - timedelta(days=2)).isoformat()  # 业务目标日期
        if (cursor or {}).get("last_date") == target:
            return cursor, []

        rel = f"config/dates/{target}.json"
        d = _ws() / "config" / "dates"
        d.mkdir(parents=True, exist_ok=True)
        (d / f"{target}.json").write_text(json.dumps({
            "topic": cfg.get("topic"), "date": target, "query": cfg.get("query"),
        }, ensure_ascii=False, indent=2), encoding="utf-8")

        jobs = [{
            "event_id": target, "business_version": "1",
            "input_refs": [rel], "idempotency_key": f"{cfg.get('topic')}:{target}",
            "env": {"SCHED_CONFIG": rel}, "entry_args": [],
        }]
        return {"last_date": target}, jobs


def main() -> int:
    run_producer(DailyProducer(), tick_sec=300)
    return 0


if __name__ == "__main__":
    sys.exit(main())