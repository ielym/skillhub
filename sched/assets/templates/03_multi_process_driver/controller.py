"""模板 03：multi_process_driver —— 驱动进程。

每天早上写一个新意图（抓当天论文），同时按需发起 2 天大任务。
由调度器每天自动拉起 controller.py（可以是 daemon 也可以是 oneshot）。
"""

import sys
from datetime import datetime
from sched_task_sdk import DaemonTask, run_task, emit_intent, list_intents


class ArxivDriver(DaemonTask):

    def steps(self):
        while True:
            today = datetime.now().strftime("%Y-%m-%d")
            existing = list_intents()
            ids = {i["request_id"] for i in existing}

            # 每天一个新意图（oneshot）
            new_id = f"arxiv-{today}"
            if new_id not in ids:
                emit_intent(
                    request_id=new_id,
                    kind="oneshot",
                    config=f"config/{today}.json",
                    priority=40,
                    resources={"cpu": 0.5, "memory_mb": 512},
                    lifetime={
                        "completion": "terminal",
                        "retry": {"backoff_base_sec": 5,
                                  "backoff_cap_sec": 300, "not_after": ""},
                    },
                )
                print(f"[driver] emitted {new_id}")

            # 每 3 天一个 2 天大任务（可选）
            day_of_month = datetime.now().day
            if day_of_month % 3 == 0:
                big_id = f"arxiv-big-{today}"
                if big_id not in ids:
                    emit_intent(
                        request_id=big_id,
                        kind="daemon",      # 长期跑的 2 天大任务
                        config="config/big.json",
                        priority=60,
                        resources={"cpu": 2.0, "memory_mb": 4096},
                        lifetime={
                            "completion": "indefinite",
                            "retry": {"backoff_base_sec": 30,
                                      "backoff_cap_sec": 600, "not_after": ""},
                        },
                    )
                    print(f"[driver] emitted big task {big_id}")

            self.save_checkpoint({"driver_ok": True})
            yield today


if __name__ == "__main__":
    run_task(ArxivDriver(name="arxiv_driver"))
