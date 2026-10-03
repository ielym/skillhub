"""sched 任务骨架（复制本目录到 tasks/<id>/ 后替换为真实逻辑）。

本骨架演示且强制正确的五件事（对应技能 sched 的铁律）：
1. 断点游标：每个工作单元完成后写 resume_point 并 flush；恢复时从游标继续，重放必须幂等。
2. dry-run：所有外部写副作用（上传/写库/发消息/付费 API）在 SCHED_DRY_RUN=1 时一律短路。
3. 单条坏数据不炸整轮：局部捕获 → skip_item → 本轮继续；二刷轮（SCHED_TRIGGER=second_pass）消费跳过项。
4. 错误分类（已实测的正确姿势，勿改）：
   - 逻辑错误：raise ValueError("LOGIC: ...")，配合 task.json 的 logic_regex=["LOGIC:"] → exit 1 / failed；
   - 资源不足：state.mark_failed + flush 后 sys.exit(100|101)，快速失败不死等；
     100=本机固定资源（内存/CPU/磁盘），101=外部资源（代理/隧道/限流/配额）——
     两者都由调度器指数退避后自动重试，任务无需 sleep 等待；
   - 数据风险：skip_item 落账后 sys.exit(110)，调度器自动二刷（最多 3 轮）；
   - 禁止在 steps() 内调 self.fail(...) 后 return：当前 SDK 会把它覆盖成 exit 0 / success。
5. 心跳由 SDK 后台线程每 30s 自动 flush；步长保持短小（建议单步 ≤20s），不做无超时的阻塞 IO。

闸5 自测要点：dry 路径里保留小段 sleep（约 1s/块），使 smoke.signal_after_sec（默认 1.5s）
发出的 SIGTERM 能命中"块处理中"，从而验证 99 抢占；真实路径应去掉人为 sleep。
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

from sched_task_sdk import SchedTask, Step, run_task

# 业务常量（替换为真实来源；跨任务输入只能是只读稳定源，禁止读兄弟任务目录）
TOTAL_ITEMS = 6
# 演练开关：SCHED_DEMO_SKIP=1 时 item-3 走 skip→110→second_pass 流程，供错误注入演练；
# 默认关闭，保证干净冒烟 exit 0（否则复制后连闸3 都过不了）。真实任务删除该机制。
DEMO_BAD_ITEM = "item-3"


class SkeletonTask(SchedTask):
    def steps(self, resume: dict):
        second_pass = os.environ.get("SCHED_TRIGGER") == "second_pass"

        # ---- 二刷轮：只处理上次跳过的条目，不再全量扫描 ----
        if second_pass:
            for rec in self.read_pending_skipped():
                item_id = rec["item"]
                yield Step("second_pass", {"item": item_id})
                try:
                    self._process_one(item_id)
                except Exception as exc:  # 单条仍失败：确认无救就死信，不再 110 死循环
                    self.dead_letter(item_id, f"second_pass failed: {exc}")
                self.state.resume_point = {"phase": "second_pass", "item": item_id}
                self.state.flush()
            # 二刷结束正常收尾（pending_skipped 的清账策略由业务定，如重写空文件/记结果）
            self._write_output({"second_pass_done": True})
            return

        # ---- 正常轮：从断点游标开始（首次为 {} → 0）----
        start = int((resume or {}).get("cursor", 0))
        failed_any = False
        for idx in range(start, TOTAL_ITEMS):
            item_id = f"item-{idx}"
            yield Step("process", {"index": idx})

            # 演示：dry 路径每块小睡，保证闸5 信号能命中块中（真实任务删除）
            if self.dry_run:
                time.sleep(1.0)

            try:
                self._process_one(item_id)
            except Exception as exc:
                # 单条坏数据：记账跳过，本轮继续，绝不让一条数据卡死/击穿整轮
                self.skip_item(item_id, str(exc))
                failed_any = True

            # 断点=已完成位点（含已记账的跳过项）；重放时本块的写操作必须幂等
            self.state.resume_point = {"cursor": idx + 1}
            self.state.progress = int((idx + 1) / TOTAL_ITEMS * 100)
            self.state.flush()

        if failed_any:
            # 数据风险：跳过项已落 pending_skipped，请求调度器重入队二刷
            self.state.mark_failed("data_risk", "one or more items skipped; request second_pass")
            self.state.flush()
            sys.exit(110)

        self._write_output({"processed": TOTAL_ITEMS})
        # 生成器自然结束 → SDK 自动 mark_success、清空 resume_point、exit 0

    # ---- 业务函数（替换为真实实现）-------------------------------------

    def _process_one(self, item_id: str) -> None:
        """处理单个最小工作单元。约束：
        - 所有写副作用幂等（upsert / 幂等键 / 先查后写），抢占重放不产生重复数据；
        - dry_run 下只 print，不做任何真实写；
        - 外部资源拿不到（代理 429 / 连接失败 / 配额）应快速抛资源类错误，不要 sleep 死等；
        - 确定性的业务校验失败：raise ValueError("LOGIC: ...") 转人工。
        """
        if os.environ.get("SCHED_DEMO_SKIP") == "1" and item_id == DEMO_BAD_ITEM:
            raise ValueError(f"bad payload for {item_id}")  # 仅演练用；真实业务按实际异常处理

        if self.dry_run:
            print(f"[DRY] would process {item_id}")
            return

        # 真实副作用示例（替换）：
        # self._upload_or_write(item_id)
        print(f"processed {item_id}")

    def _write_output(self, payload: dict) -> None:
        """写交付物（task.json outputs.expect 必须存在，否则即使 exit 0 也判 failed）。"""
        out_dir = Path(self.workspace) / "results"
        out_dir.mkdir(parents=True, exist_ok=True)
        # 原子写，避免抢占瞬间留下半截文件
        target = out_dir / "final.json"
        tmp = target.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        tmp.replace(target)


if __name__ == "__main__":
    sys.exit(run_task(SkeletonTask()))
