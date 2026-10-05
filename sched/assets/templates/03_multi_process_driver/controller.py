"""模板 03：multi_process_driver —— 驱动进程。

每天早上写一个新意图（抓当天论文），同时按需发起 2 天大任务。
由调度器每天自动拉起 controller.py（可以是 daemon 也可以是 oneshot）。

优先级统一来自 manifest.json（意图不可携带 priority）。
H13：每次 emit 都 print(..., flush=True) 留痕。
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from sched_task_sdk import DaemonTask, run_task, emit_intent, list_intents


def _write_date_config(today: str) -> str:
    """把某个日期的运行参数完整写进 config/<date>.json（自包含），返回相对路径。

    H12：运行参数必须写在 config 文件里，进程只从 SCHED_CONFIG 读；
    request_id 文件名只作唯一标识，不解析、不承载语义。
    """
    rel = f"config/{today}.json"
    path = Path(__file__).resolve().parent / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"date": today, "topic": "arxiv"}, ensure_ascii=False, indent=2),
                    encoding="utf-8")
    return rel


class ArxivDriver(DaemonTask):

    def steps(self):
        while True:
            today = datetime.now().strftime("%Y-%m-%d")
            existing = list_intents()
            ids = {i["request_id"] for i in existing}

            # 每天一个新意图（oneshot）：先写参数文件，再 emit，config 指向参数文件
            new_id = f"arxiv-{today}"           # 纯唯一标识，不作为参数来源
            if new_id not in ids:
                cfg_rel = _write_date_config(today)
                emit_intent(
                    request_id=new_id,
                    kind="oneshot",
                    config=cfg_rel,
                    resources={"cpu": 0.5, "memory_mb": 512},
                    lifetime={
                        "completion": "terminal",
                        "retry": {"backoff_base_sec": 5,
                                  "backoff_cap_sec": 300, "not_after": ""},
                    },
                )
                print(f"[driver] emitted {new_id} (config={cfg_rel})", flush=True)
            else:
                print(f"[driver] {new_id} 已存在，跳过", flush=True)

            # 每 3 天一个 2 天大任务（可选）
            day_of_month = datetime.now().day
            if day_of_month % 3 == 0:
                big_id = f"arxiv-big-{today}"
                if big_id not in ids:
                    emit_intent(
                        request_id=big_id,
                        kind="daemon",      # 长期跑的 2 天大任务
                        config="config/big.json",
                        resources={"cpu": 2.0, "memory_mb": 4096},
                        lifetime={
                            "completion": "indefinite",
                            "retry": {"backoff_base_sec": 30,
                                      "backoff_cap_sec": 600, "not_after": ""},
                        },
                    )
                    print(f"[driver] emitted big task {big_id}", flush=True)

            self.state.enter_step("driver 巡检", 1.0)
            self.save_checkpoint({"driver_ok": True})
            yield today


if __name__ == "__main__":
    run_task(ArxivDriver(name="arxiv_driver"))
