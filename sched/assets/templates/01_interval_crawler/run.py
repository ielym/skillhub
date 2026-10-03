"""场景模板 01 · 定时分页采集（interval + 时间窗 + 代理软资源）。

要点：
- 每页是一个可抢占步：处理完一页立即落断点 {"page": n}，被抢占后从下一页继续（重放幂等：用 upsert）。
- dry 模式零外网：print 模拟；每页保留约 1s 使闸5 的 SIGTERM（默认 1.5s）能命中页处理中。
- 资源类问题（代理失效/429/连接失败）：立即 sys.exit(101)，不 sleep 死等，排队交给调度器。
  演练开关 SCHED_DEMO_RESERR=1。
- 单页内的坏条目：skip_item 落账后本轮继续；本轮结束若有跳过项 → 110 请求二刷；
  second_pass 轮只补跳过项。演练开关 SCHED_DEMO_SKIP=1（条目 item-2）。
- 部署前置：set-soft proxy <容量>，否则永久排队（见 references/configuration.md）。
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

from sched_task_sdk import SchedTask, Step, run_task

PAGES = 5
ITEMS_PER_PAGE = 3


class CrawlerHourlyTask(SchedTask):
    def steps(self, resume: dict):
        if os.environ.get("SCHED_TRIGGER") == "second_pass":
            yield from self._second_pass()
            return

        start_page = int((resume or {}).get("page", 0))
        skipped = False
        for page in range(start_page, PAGES):
            yield Step("fetch_page", {"page": page})
            if self.dry_run:
                time.sleep(1.0)  # 仅为闸5 演练；真实任务删除
            if os.environ.get("SCHED_DEMO_RESERR") == "1":
                self.state.mark_failed("resource", "proxy unavailable / 429")
                self.state.flush()
                sys.exit(101)

            for item in self._fetch_page(page):
                try:
                    self._upsert_item(page, item)
                except Exception as exc:
                    self.skip_item(f"p{page}-{item}", str(exc))
                    skipped = True

            self.state.resume_point = {"page": page + 1}
            self.state.progress = int((page + 1) / PAGES * 100)
            self.state.flush()

        if skipped:
            self.state.mark_failed("data_risk", "bad items recorded; request second_pass")
            self.state.flush()
            sys.exit(110)

        self._atomic_write_json(Path(self.workspace) / "results" / "latest.json",
                              {"pages": PAGES, "ok": True})

    def _second_pass(self):
        for rec in self.read_pending_skipped():
            key = rec["item"]
            yield Step("retry_item", {"item": key})
            try:
                page, item = key.split("-", 1)
                self._upsert_item(int(page), item, force=True)
            except Exception as exc:
                self.dead_letter(key, f"second_pass failed: {exc}")
            self.state.resume_point = {"second_pass_item": key}
            self.state.flush()
        self._atomic_write_json(Path(self.workspace) / "results" / "latest.json",
                              {"second_pass_done": True})

    # ---- 业务实现（替换为真实采集）----------------------------------------

    def _fetch_page(self, page: int) -> list[str]:
        # 真实实现：requests.get(...proxies=...)，超时必须显式设置；429/连接错误不要在本地吞，
        # 让异常消息命中 resource_regex（或直接 sys.exit(101)）。
        return [f"{page}-{i}" for i in range(ITEMS_PER_PAGE)]

    def _upsert_item(self, page: int, item: str, force: bool = False) -> None:
        if not force and os.environ.get("SCHED_DEMO_SKIP") == "1" and item == "2-2":
            raise ValueError(f"parse failed at page {page}")
        if self.dry_run:
            print(f"[DRY] upsert item {item}")
            return
        # 真实实现必须幂等：upsert / ON CONFLICT REPLACE / 带幂等键写库或 OSS
        print(f"upsert item {item}")

    @staticmethod
    def _atomic_write_json(path: Path, payload: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        tmp.replace(path)


if __name__ == "__main__":
    sys.exit(run_task(CrawlerHourlyTask()))
