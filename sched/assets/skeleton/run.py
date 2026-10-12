"""最小执行者骨架：业务处理 + 断点 + 进展 + 完成。

- self.checkpoint(data) 是「落断点 + 查暂停」的统一点，务必在有界步骤边界调用。
- 有限任务最后 self.complete(...)。
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

_SCHED_SRC = os.environ.get("SCHED_SRC", "")
if _SCHED_SRC and os.path.isdir(_SCHED_SRC) and _SCHED_SRC not in sys.path:
    sys.path.insert(0, _SCHED_SRC)

from sched_task_sdk import ExecutorTask, run_task  # noqa: E402


class MyExecutor(ExecutorTask):
    def execute(self):
        done = self.resume_data() or []     # 断点恢复
        total = 10
        for i in range(total):
            if i in done:
                continue
            # 业务处理（幂等）...
            done.append(i)
            # 落断点 + 查暂停；业务版本与进度一并写入检查点（设计第七节）
            self.checkpoint(done, business_version="1",
                            progress={"completed": len(done)})
            self.report_progress(len(done), len(done) < total, "process",
                                 work_units=len(done))
        self.complete({"count": len(done)})  # 提交完成记录


def main() -> int:
    return run_task(MyExecutor())


if __name__ == "__main__":
    sys.exit(main())