"""每日执行者模板：读取 SCHED_CONFIG 指向的 per-date 配置，逐项幂等处理。

- 断点 done_ids + 幂等提交（外部写入前先查存在/用稳定键）。
- 外部请求纪律：有限重试（R3，最多 2 次 × 固定 3s）——耗尽仍失败立即携带错误类型与资源标识 report_shortage → exit 75。
- 检查点只在真实进展后提交；异常分支不保存未变化的断点数据。
- 检索结果为空属于业务事实：复核后直接 complete，不报外部不足。
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

_SCHED_SRC = os.environ.get("SCHED_SRC", "")
if _SCHED_SRC and os.path.isdir(_SCHED_SRC) and _SCHED_SRC not in sys.path:
    sys.path.insert(0, _SCHED_SRC)

from sched_task_sdk import ExecutorTask, run_task  # noqa: E402


def _ws() -> Path:
    return Path(os.environ.get("SCHED_WORKSPACE") or Path.cwd())


def _load_config() -> dict:
    rel = os.environ.get("SCHED_CONFIG") or ""
    p = _ws() / rel if rel else (_ws() / "config.json")
    return json.loads(p.read_text("utf-8")) if p.is_file() else {}


# ------------------------------------------------------------------ 外部请求纪律
# 不预设外部资源限制（qps/并发均未知且会变）；不做任何任务间协调（无共享
# 锁/槽/令牌）。资源错误有限重试（R3/R9）：首次失败后原地重试最多 2 次
# （固定短间隔，仅过滤瞬时抖动），仍失败立即携带错误类型与资源标识上浮
# exit 75，退避/重排/并发调整由调度器统一决定。重试上限与间隔为固定常量，
# 禁止无界/递增重试。响应读取保留总时长上限（R8）：防坏出口慢速滴数据
# 无限续命（进程假活）。
READ_CAP_SEC = 300.0
MAX_RETRIES = 2        # R3：资源错误任务内重试次数（首次 + 2 次重试）
RETRY_GAP_SEC = 3.0    # R3：重试间隔（固定短间隔，仅过滤瞬时抖动）


def _log(msg: str) -> None:
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"{ts} | {msg}", flush=True)


def fetch_external(url: str) -> bytes:
    """外部请求标准模式：有限重试（最多 2 次 × 固定 3s）+ 耗尽上浮。

    重试只过滤瞬时抖动（每次尝试都是新连接/新出口）；仍失败立即携带
    错误类型与资源标识上浮 exit 75（R3/R4/R9）。禁止无界重试/退避增长
    ——持续故障的区分与规避由调度器按事件流密度决定（R6 的空结果复核
    除外——那是业务事实确认，不是失败重试）。
    """
    import urllib.request
    from sched_task_sdk import Shortage
    last_err = None
    for attempt in range(1 + MAX_RETRIES):
        if attempt:
            _log(f"  请求重试 {attempt}/{MAX_RETRIES}（{RETRY_GAP_SEC:.0f}s 后）：{url[:100]}")
            time.sleep(RETRY_GAP_SEC)
        try:
            with urllib.request.urlopen(url, timeout=30) as resp:
                parts, t0 = [], time.time()
                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    parts.append(chunk)
                    if time.time() - t0 > READ_CAP_SEC:
                        # R8 慢速滴：非瞬时抖动，不重试立即上浮
                        raise Shortage(f"TimeoutError: {url}（外部资源不可得）")
                return b"".join(parts)
        except Shortage:
            raise
        except Exception as e:  # noqa: BLE001 — 统一转上浮
            last_err = Shortage(f"{type(e).__name__}: {url}（外部资源不可得）")
    raise last_err


class DailyExecutor(ExecutorTask):
    def execute(self):
        cfg = _load_config()
        date_str = cfg.get("date")
        items = self._fetch_items(cfg)          # 业务：获得待处理单元
        done = set((self.resume_data() or {}).get("done_ids", []))

        # 空结果属于业务事实：复核数次仍为空即按真实无数据处理，
        # 直接完成——报外部不足会因"确实无数据"而无限退避。
        if not items:
            for i in range(3):
                _log(f"  结果为空，复核 {i + 1}/3（60s 间隔）")
                time.sleep(60)
                items = self._fetch_items(cfg)
                if items:
                    break
            if not items:
                self.complete({"count": 0, "date": date_str,
                               "reason": "检索确认无数据"})
                return

        self.report_progress(len(done))
        for it in items:
            key = it.key
            if key in done:
                continue
            self._process_one(it)               # 幂等：先查已有再写
            done.add(key)
            # 检查点在真实进展后提交（新单元完成）
            self.checkpoint({"done_ids": sorted(done)},
                            business_version=cfg.get("version") or date_str or "1",
                            progress={"done": len(done), "total": len(items)})
            self.report_progress(len(done))
        self.complete({"count": len(done), "date": date_str})

    def _fetch_items(self, cfg):
        # 业务：按 cfg 检索得到单元列表。
        # 外部数据源的公布存在滞后（含索引尾巴），触发窗口须留足余量
        # （如按 T-7 创建作业）。检索走 fetch_external 的请求纪律。
        return []

    def _process_one(self, item):
        # 业务：处理单个单元（幂等：外部写入前先查存在/用稳定键）。
        # 外部请求走 fetch_external（有限重试 R3：最多 2 次，耗尽上浮）；
        # 禁止兜底/跳过/记入失败名单等任何吞掉形式，调度器退避后重排续跑。
        # 仅"目标不可得"类业务事实（404、内容非法、目标已撤回）可跳过。
        pass


def main() -> int:
    return run_task(DailyExecutor())


if __name__ == "__main__":
    sys.exit(main())
