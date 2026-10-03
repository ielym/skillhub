"""场景模板 03 · 手动按需导出（schedule.type=manual，可断点、可抢占）。

要点：
- 手动触发不是特权：run 只负责入队，执行时高优任务来了一样会被抢占，一样要有 99 断点续跑。
- 导出按批（batch）分页拉取并追加写文件；断点 {"last_batch": n}。
  重放幂等：恢复后重建/截断到上次提交边界，再从下一 batch 追加（这里演示用"整文件重导"策略：
  断点记录最后完成批次，续跑时若结果文件已存在则从断点继续 append —— append 的是尚未写过的下一批，天然不重复）。
- 单条坏记录 skip_item，不阻断整份导出；有跳过项则 110 触发二刷补漏。
- 触发：python3 -m sched run report-on-demand。
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from sched_task_sdk import SchedTask, Step, run_task

BATCHES = 6
ROWS_PER_BATCH = 50


class ReportOnDemandTask(SchedTask):
    def steps(self, resume: dict):
        last_batch = int((resume or {}).get("last_batch", 0))
        if last_batch == 0:
            self._reset_export_file()  # 新一轮：重建文件并写表头
        else:
            print(f"resume export from batch {last_batch + 1}")

        skipped = False
        for batch in range(last_batch, BATCHES):
            yield Step("export_batch", {"batch": batch})
            if self.dry_run:
                time.sleep(1.0)  # 仅为闸5 演练
            rows = self._fetch_batch(batch)
            lines = []
            for r in rows:
                if not self._row_ok(r):
                    self.skip_item(str(r.get("id")), "bad row")
                    skipped = True
                    continue
                lines.append(self._to_csv_line(r))
            self._append_lines(lines)
            self.state.resume_point = {"last_batch": batch + 1}
            self.state.progress = int((batch + 1) / BATCHES * 100)
            self.state.flush()

        if skipped:
            self.state.mark_failed("data_risk", "rows skipped; request second_pass")
            self.state.flush()
            sys.exit(110)
        # outputs.expect = results/export.csv：文件已在首轮写表头时创建，空导出也算成功交付

    # ---- 业务实现（替换为真实查询/格式）------------------------------------

    def _reset_export_file(self) -> None:
        p = Path(self.workspace) / "results" / "export.csv"
        p.parent.mkdir(parents=True, exist_ok=True)
        if self.dry_run:
            print("[DRY] (re)create export.csv with header")
            p.write_text("id,v\n", encoding="utf-8")
            return
        p.write_text("id,v\n", encoding="utf-8")

    def _fetch_batch(self, batch: int) -> list[dict]:
        return [{"id": batch * ROWS_PER_BATCH + i, "v": i} for i in range(ROWS_PER_BATCH)]

    @staticmethod
    def _row_ok(row: dict) -> bool:
        return isinstance(row.get("id"), int) and isinstance(row.get("v"), int)

    @staticmethod
    def _to_csv_line(row: dict) -> str:
        return f"{row['id']},{row['v']}\n"

    def _append_lines(self, lines: list[str]) -> None:
        p = Path(self.workspace) / "results" / "export.csv"
        if self.dry_run:
            print(f"[DRY] append {len(lines)} rows")
            return
        with open(p, "a", encoding="utf-8") as f:
            f.writelines(lines)


if __name__ == "__main__":
    sys.exit(run_task(ReportOnDemandTask()))
