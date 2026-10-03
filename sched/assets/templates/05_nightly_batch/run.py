"""场景模板 05 · 夜间大批量分片计算（interval 跨夜窗口 + allow_overrun=true）。

要点：
- 优先级低（15）：白天任何更高优任务需要资源时随时被抢占；因此断点必须细：
  resume_point = {"partition": p, "cursor": n}，每处理一个分片条目就 flush。
- allow_overrun=true：即使跑到 08:00 窗口结束后也允许跑完（不被窗口收口 SIGTERM 成 killed 转人工）。
- 天然长任务：单步工作量保持很小（这里每个条目一个步），靠心跳线程保活；
  绝不要把整个 partition 塞进一个几十分钟的大步。
- dry 模式只跑少量条目并每步小睡（闸5 演练）；真实跑用 TOTAL_ENTRIES 全量。
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

from sched_task_sdk import SchedTask, Step, run_task

PARTITIONS = 3
DRY_ENTRIES_PER_PART = 2     # 冒烟/演练只跑 6 步、每步约 1s
REAL_ENTRIES_PER_PART = 5000  # 真实夜跑量级（按实际替换）


class NightlyBatchTask(SchedTask):
    def steps(self, resume: dict):
        if os.environ.get("SCHED_TRIGGER") == "second_pass":
            yield from self._second_pass()
            return
        start_part = int((resume or {}).get("partition", 0))
        start_cursor = int((resume or {}).get("cursor", 0))
        per_part = DRY_ENTRIES_PER_PART if self.dry_run else REAL_ENTRIES_PER_PART
        total = PARTITIONS * per_part
        done = start_part * per_part + start_cursor

        for part in range(start_part, PARTITIONS):
            begin = start_cursor if part == start_part else 0
            for cursor in range(begin, per_part):
                yield Step("compute", {"partition": part, "cursor": cursor})
                if self.dry_run:
                    time.sleep(1.0)  # 仅为闸5 演练
                try:
                    self._compute_entry(part, cursor)
                except Exception as exc:
                    # 单条数据问题不炸整夜任务：跳过记账，本轮继续；末尾按 110 二刷
                    self.skip_item(f"{part}:{cursor}", str(exc))
                done += 1
                self.state.resume_point = {"partition": part, "cursor": cursor + 1}
                self.state.progress = int(done / total * 100)
                self.state.flush()

        skipped = len(self.read_pending_skipped())
        if skipped:
            self.state.mark_failed("data_risk", f"{skipped} entries skipped; request second_pass")
            self.state.flush()
            sys.exit(110)

        path = Path(self.workspace) / "results" / "nightly_result.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps({"partitions": PARTITIONS, "entries_per_partition": per_part}),
                      encoding="utf-8")
        tmp.replace(path)

    def _second_pass(self):
        for rec in self.read_pending_skipped():
            key = rec["item"]
            yield Step("retry_entry", {"entry": key})
            try:
                part_s, cursor_s = key.split(":")
                self._compute_entry(int(part_s), int(cursor_s))
            except Exception as exc:
                self.dead_letter(key, f"second_pass failed: {exc}")
            self.state.resume_point = {"second_pass_entry": key}
            self.state.flush()
        path = Path(self.workspace) / "results" / "nightly_result.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"second_pass_done": True}), encoding="utf-8")

    def _compute_entry(self, part: int, cursor: int) -> None:
        # 真实实现：小块 CPU/IO 计算 + 幂等落盘（分片文件 append/upsert，重放安全）
        if self.dry_run:
            print(f"[DRY] compute p{part}#{cursor}")
            return
        # 例如写 results/part_{p}.jsonl 的第 cursor 行（用幂等键避免重放重复）


if __name__ == "__main__":
    sys.exit(run_task(NightlyBatchTask()))
