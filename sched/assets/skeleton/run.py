"""骨架：复制后替换 __class__ 名称、steps()、process_step()。

H13 约定（必做）：所有进度都必须实时可见——
- 启动/每个 step/结束 用 print(..., flush=True) 打 stdout/stderr；
- 总进度同步写 self.state.enter_step(名称, progress)，progress 0~1；
- 禁止静默长跑。
"""

import os
import sys
from sched_task_sdk import OneshotTask, DaemonTask, run_task


class MyTask(OneshotTask):   # 或 DaemonTask
    """在这里写业务类名。"""

    def steps(self):
        """yield 每个要处理的单元。"""
        # yield None  # oneshot 空跑
        # while True: yield None  # daemon 常驻
        raise NotImplementedError("必须实现 steps()")

    def process_step(self, step):
        """处理一个 step。"""
        self.state.enter_step(f"处理 {step}", 0.5)   # 进度（0~1）+ 当前步骤，管理台可见
        print(f"[progress] 处理 {step}...", flush=True)
        self.save_checkpoint({"done": [step]})
        # 心跳由 SDK 心跳线程自动维护，无需手动调用


if __name__ == "__main__":
    print(f"[start] 任务启动 subtask={os.environ.get('SCHED_SUBTASK_ID', '?')} "
          f"run_id={os.environ.get('SCHED_RUN_ID', '?')}", flush=True)
    run_task(MyTask())
