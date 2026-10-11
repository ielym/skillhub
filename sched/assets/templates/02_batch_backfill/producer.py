"""批量回溯生产者模板：发现范围内每个未完成单元并发布就绪作业。

- cursor 持久化「已发布或已判定完成」的单元集合，重启不重复。
- 已完成单元（外部存在完成标记）跳过；失败交给调度器对已入库作业退让重试。
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_SCHED_SRC = os.environ.get("SCHED_SRC", "/mnt/data01/projects/scheduler")
if _SCHED_SRC and os.path.isdir(_SCHED_SRC) and _SCHED_SRC not in sys.path:
    sys.path.insert(0, _SCHED_SRC)

from sched_task_sdk import Producer, run_producer  # noqa: E402


def _ws() -> Path:
    return Path(os.environ.get("SCHED_WORKSPACE") or Path(__file__).resolve().parent)


def _cfg() -> dict:
    p = _ws() / "config.json"
    return json.loads(p.read_text("utf-8")) if p.is_file() else {}


def _already_done(key: str) -> bool:
    # 业务：判断该单元是否已完成（幂等跳过）
    return False


def _keys(cfg) -> list[str]:
    # 业务：生成范围内单元稳定标识列表
    return []


class BackfillProducer(Producer):
    def discover(self, cursor):
        cfg = _cfg()
        seen = set((cursor or {}).get("seen_keys") or [])
        jobs = []
        for key in _keys(cfg):
            if key in seen:
                continue
            seen.add(key)
            if _already_done(key):
                continue
            rel = f"config/units/{key}.json"
            d = _ws() / "config" / "units"
            d.mkdir(parents=True, exist_ok=True)
            (d / f"{key}.json").write_text(json.dumps(
                {"topic": cfg.get("topic"), "key": key, "query": cfg.get("query")},
                ensure_ascii=False, indent=2), encoding="utf-8")
            jobs.append({
                "event_id": key, "business_version": "1",
                "input_refs": [rel], "idempotency_key": f"{cfg.get('topic')}:{key}",
                "env": {"SCHED_CONFIG": rel}, "entry_args": [],
            })
        return {"seen_keys": sorted(seen)}, jobs


def main() -> int:
    run_producer(BackfillProducer(), tick_sec=60)
    return 0


if __name__ == "__main__":
    sys.exit(main())