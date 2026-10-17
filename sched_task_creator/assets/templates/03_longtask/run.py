"""长期任务执行者模板：持续进展、无完成事件，通过进展参与调度观测。

- 周期 checkpoint + 进展；有界步骤边界检查暂停。
- 等待新输入与正在处理用 stage 区分。
"""
from __future__ import annotations

import os
import sys

_SCHED_SRC = os.environ.get("SCHED_SRC", "")
if _SCHED_SRC and os.path.isdir(_SCHED_SRC) and _SCHED_SRC not in sys.path:
    sys.path.insert(0, _SCHED_SRC)

from sched_task_sdk import ExecutorTask, run_task  # noqa: E402


class LongExecutor(ExecutorTask):
    
    def execute(self):
        done = (self.resume_data() or {}).get("count", 0)
        while True:
            items = self._poll()          # 业务：等待/获取新输入（有界等待）
            if not items:
                # 正常无输入等待 ≠ 变慢；报进展但无在途工作。
                # 检查点只在真实进展后提交：无变化的数据重复落盘会伪造
                # "外部已恢复"证据，污染调度器的退避判定
                self.report_progress(done)
                # 可中断等待：暂停信号到达时立即跳出，而非最多再睡满 2s
                self.wait_interruptible(2.0)
                continue
            for it in items:
                self._process(it)          # 幂等
                done += 1
                self.checkpoint({"count": done}, business_version="1",
                                progress={"count": done})
                self.report_progress(done)

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