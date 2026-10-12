"""长期任务执行者模板：持续进展、无完成事件，通过进展参与调度观测。

- 周期 checkpoint + 进展；有界步骤边界检查暂停。
- 等待新输入（无在途工作）与正在处理须在进展里区分（has_unfinished）。
"""
from __future__ import annotations

import os
import sys

_SCHED_SRC = os.environ.get("SCHED_SRC", "")
if _SCHED_SRC and os.path.isdir(_SCHED_SRC) and _SCHED_SRC not in sys.path:
    sys.path.insert(0, _SCHED_SRC)

from sched_task_sdk import ExecutorTask, run_task  # noqa: E402


class LongExecutor(ExecutorTask):
    heartbeat_interval_sec = 5.0

    def execute(self):
        done = (self.resume_data() or {}).get("count", 0)
        while True:
            items = self._poll()          # 业务：等待/获取新输入（有界等待）
            if not items:
                # 正常无输入等待 ≠ 变慢；报进展但无在途工作
                self.report_progress(done, False, "idle")
                self.checkpoint({"count": done}, business_version="1",
                                progress={"count": done})
                # 可中断等待：暂停信号到达时立即跳出，而非最多再睡满 2s
                self.wait_interruptible(2.0)
                continue
            for it in items:
                self._process(it)          # 幂等
                done += 1
                self.checkpoint({"count": done}, business_version="1",
                                progress={"count": done})
                self.report_progress(done, True, "process", work_units=done)

    def _poll(self):
        # 业务：返回待处理单元
        return []

    def _process(self, item):
        # 业务：处理单元
        pass


def main() -> int:
    return run_task(LongExecutor())


if __name__ == "__main__":
    sys.exit(main())