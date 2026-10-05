"""模板 03：multi_process_driver —— 被拉起的业务进程（run.py）。

调度器拉起这个进程时 --config 指向 driver 写入的 config 文件。
继承 OneshotTask 或 DaemonTask，按意图 kind 选择。

H13：启动打印读取的参数（config），每步打印 + enter_step 写 progress。
"""

import json
import os
import sys
from pathlib import Path

from sched_task_sdk import DaemonTask, OneshotTask, run_task


def _load_config() -> dict:
    """从 SCHED_CONFIG 或 --config 加载业务配置。"""
    p = os.environ.get("SCHED_CONFIG") or ""
    if not p:
        return {}
    path = Path(os.environ.get("SCHED_WORKSPACE", ".")) / p
    if path.exists():
        return json.loads(path.read_text("utf-8"))
    return {}


class ArxivFetcher(OneshotTask):   # driver 里 intent.kind="oneshot" 时
    """抓 config 指定日期的论文。"""

    def steps(self):
        cfg = _load_config()
        target_date = cfg.get("date")
        if not target_date:
            print("缺运行参数 date（H12：必须写在 config 文件里，禁止从文件名反推）", file=sys.stderr, flush=True)
            sys.exit(1)
        print(f"[start] 抓取日期 {target_date}，config={cfg}", flush=True)
        items = fetch_items(target_date)
        total = len(items)
        self.state.total_steps = total
        for i, item in enumerate(items):
            self.state.enter_step(f"保存 {i + 1}/{total}", (i + 1) / total if total else 1.0)
            print(f"[progress] {i + 1}/{total} 保存 {item.get('id')}", flush=True)
            self.save_checkpoint({"last_index": i, "last_id": item.get("id")})
            yield item
        print(f"[done] {target_date}: 共保存 {total} 条", flush=True)

    def process_step(self, item):
        try:
            save_item(item)
        except Exception as e:
            print(f"[fail] 保存失败 {item.get('id')}: {e}", file=sys.stderr, flush=True)
            self.state.error("resource", f"保存失败：{e}")
            sys.exit(101)


class ArxivBigTask(DaemonTask):   # driver 里 intent.kind="daemon" 时
    """2 天大任务，被抢占后续跑。"""

    def steps(self):
        cfg = _load_config()
        while True:
            chunk = fetch_next_chunk(cfg)
            self.state.enter_step(f"抓取分块 {chunk.get('cursor')}", 0.5)
            print(f"[progress] 抓取分块 {chunk.get('cursor')}，{len(chunk.get('items') or [])} 条", flush=True)
            self.save_checkpoint({"cursor": chunk.get("cursor")})
            yield chunk


def fetch_items(date: str):
    raise NotImplementedError("实现抓取逻辑")


def save_item(item):
    raise NotImplementedError("实现落库逻辑")


def fetch_next_chunk(cfg: dict):
    raise NotImplementedError("实现大任务分块抓取逻辑")


if __name__ == "__main__":
    # 也可以根据 SCHED_REQUEST_ID / SCHED_CONFIG 动态选择类
    run_task(ArxivFetcher(name="arxiv_fetcher"))
