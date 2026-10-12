"""长期任务生产者模板：确认一个常驻作业在跑（如需更多作业，按需发布）。

长期任务与有限任务同一套请求协议；此处生产者发布一个长期作业（业务自行区分）。
"""
from __future__ import annotations

import os
import sys

_SCHED_SRC = os.environ.get("SCHED_SRC", "")
if _SCHED_SRC and os.path.isdir(_SCHED_SRC) and _SCHED_SRC not in sys.path:
    sys.path.insert(0, _SCHED_SRC)

from sched_task_sdk import Producer, run_producer  # noqa: E402


class LongProducer(Producer):
    def discover(self, cursor):
        if (cursor or {}).get("published"):
            return cursor, []
        return {"published": True}, [{
            "event_id": "stream", "business_version": "1",
            "input_refs": [], "idempotency_key": "stream",
            "env": {}, "entry_args": [],
        }]


def main() -> int:
    run_producer(LongProducer(), tick_sec=300)
    return 0


if __name__ == "__main__":
    sys.exit(main())