"""场景模板 04 · 不可断点的原子运维动作（contract_exempt=true + manual）。

⚠️ 豁免语义（与普通任务的全部差异，务必理解再用）：
- 闸1–4 照跑，**闸5（断点）不跑**；但契约探针、心跳、资源申报、交付物校验一样不能少。
- 只能手动触发：python3 -m sched run atomic-cutover。
- **不可抢占**：运行中即使高优任务在等，也不会收到 SIGTERM；因此动作必须真的"短而原子"。
- serve 崩溃/重启不会自动恢复本任务（active 里的在途记录只落"待人工"），必须人工核对外部状态后再 run。
- 适用面极窄：外部系统只提供原子提交、无幂等重放、无中间位点（如一次性 cutover/密钥轮转/拓扑切换）。
  凡是能拆步落断点的任务，一律用普通模板（03），**严禁借 exempt 逃避抢占**。

实现上仍继承 SDK：probe/心跳/错误分类继续可用；但只有一个不可再分的步骤，不写业务 resume_point。
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

from sched_task_sdk import SchedTask, Step, run_task


class AtomicCutoverTask(SchedTask):
    def steps(self, resume: dict):
        yield Step("atomic_cutover")
        # 前置校验失败属于逻辑错误：显式失败、转人工，不做半截切换
        if not self._precheck():
            raise ValueError("LOGIC: precheck failed; refuse to cut over")
        self._do_cutover()  # 外部系统原子 API：要么全成，要么外部侧无副作用/可由人工判滚
        result = {"cutover_at": datetime.now().astimezone().isoformat(timespec="seconds"),
                  "dry_run": self.dry_run}
        path = Path(self.workspace) / "results" / "cutover.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
        # 生成器自然结束 → success（SDK 会清空 resume_point；exempt 不依赖它）

    def _precheck(self) -> bool:
        # 真实实现：外部系统版本/状态/权限/备份确认
        return True

    def _do_cutover(self) -> None:
        if self.dry_run:
            print("[DRY] would call external atomic cutover API")
            return
        print("cutover done")


if __name__ == "__main__":
    sys.exit(run_task(AtomicCutoverTask()))
