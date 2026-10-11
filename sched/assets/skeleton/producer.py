"""最小生产者骨架：发现业务事件 → 发布就绪作业。

- cursor 用于去重（幂等），不用于外推业务时间。
- 稳定事件标识 + 业务版本 → 相同事件重放得到相同 job_id。
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

_SCHED_SRC = os.environ.get("SCHED_SRC", "/mnt/data01/projects/scheduler")
if _SCHED_SRC and os.path.isdir(_SCHED_SRC) and _SCHED_SRC not in sys.path:
    sys.path.insert(0, _SCHED_SRC)

from sched_task_sdk import Producer, run_producer  # noqa: E402


class MyProducer(Producer):
    def discover(self, cursor):
        # 已发布过 → 不再发布
        if (cursor or {}).get("published"):
            return cursor, []
        jobs = [{
            "event_id": "round-1",          # 稳定业务事件标识
            "business_version": "1",        # 业务版本
            "entry_args": [],               # 追加到 executor 的参数数组
            "input_refs": [],               # 必要业务输入引用
            "idempotency_key": "round-1",
            "env": {},                      # 安全业务环境参数（不含资源申请/账号）
        }]
        return {"published": True}, jobs


def main() -> int:
    run_producer(MyProducer(), tick_sec=60)
    return 0


if __name__ == "__main__":
    sys.exit(main())