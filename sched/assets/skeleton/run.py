"""骨架：复制后替换 __class__ 名称、steps()、process_step()。"""

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
        self.save_checkpoint({"done": [step]})
        self.heartbeat()  # SDK 自动做


if __name__ == "__main__":
    run_task(MyTask())
