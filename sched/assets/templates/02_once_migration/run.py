"""场景模板 02 · 一次性数据迁移 / 历史回填（schedule.type=once）。

要点：
- once 任务只在 once_at 触发一次（过期时刻永不触发！），迁移完成后任务留在注册表不再调度；
  如需清理，按 acceptance.md C4 流程。
- 迁移按 ID 切片（chunk）推进，每片一个步、每片末落断点 {"last_id": n}；
  被抢占后从下一 ID 继续，所有写入必须幂等（推荐 INSERT ... ON CONFLICT DO NOTHING/DO UPDATE）。
- 确定性的数据/模式错误（例如源行缺必填列）属于逻辑错误：raise ValueError("LOGIC: ...")，
  exit 1 / failed 转人工，绝不允许"带着错误继续迁移"。
- dry 演练保留约 1s/片使闸5 信号能命中。
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from sched_task_sdk import SchedTask, Step, run_task

TOTAL_ROWS = 48
CHUNK = 8  # 每个步处理 8 行：单片远小于 20s，断点细、可随时抢占


class BackfillOnceTask(SchedTask):
    def steps(self, resume: dict):
        last_id = int((resume or {}).get("last_id", 0))
        while last_id < TOTAL_ROWS:
            lo, hi = last_id + 1, min(last_id + CHUNK, TOTAL_ROWS)
            yield Step("migrate_chunk", {"from": lo, "to": hi})
            if self.dry_run:
                time.sleep(1.0)  # 仅为闸5 演练
            rows = self._read_source(lo, hi)
            for row in rows:
                self._validate_or_raise(row)
                self._idempotent_write(row)
            last_id = hi
            self.state.resume_point = {"last_id": last_id}
            self.state.progress = int(last_id / TOTAL_ROWS * 100)
            self.state.flush()

        summary = {"migrated": TOTAL_ROWS, "status": "done"}
        self._atomic_write_json(Path(self.workspace) / "results" / "backfill_summary.json", summary)

    # ---- 业务实现（替换为真实源/目标）-------------------------------------

    def _read_source(self, lo: int, hi: int) -> list[dict]:
        if self.dry_run:
            return [{"id": i, "v": i * 2} for i in range(lo, hi + 1)]
        # 真实实现：SELECT ... WHERE id BETWEEN lo AND hi ORDER BY id（只读稳定源）
        return []

    def _validate_or_raise(self, row: dict) -> None:
        # 确定性、不可重试的错误必须转人工，不要跳过/忽略
        if "id" not in row:
            raise ValueError(f"LOGIC: source row missing id: {row!r}")
        if not isinstance(row.get("v"), int):
            raise ValueError(f"LOGIC: row {row.get('id')} v not int")

    def _idempotent_write(self, row: dict) -> None:
        if self.dry_run:
            print(f"[DRY] upsert target id={row['id']}")
            return
        # 真实实现必须是幂等写；避免断点重放造成重复数据

    @staticmethod
    def _atomic_write_json(path: Path, payload: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        tmp.replace(path)


if __name__ == "__main__":
    sys.exit(run_task(BackfillOnceTask()))
