# 双闸准入（gates）

注册/上线时由 `sched.register_subtask()` 或调度器自动发现后触发（静态校验在 manifest 解析时即完成）。

## 闸1 静态（manifest 解析）

**判定**：`manifest.parse_manifest()` 成功返回 `TaskManifest`

**检查点**：
- schema_version == 3
- entry.file 存在且在任务目录内
- entry.interpreter 是合法命令名（无路径）
- priority 在 0~100
- run_mode ∈ {auto, manual}
- heartbeat.timeout_sec ≥ 5

**失败修复**：看 Web 管理台或 `sched status` 里的 `error` 字段，逐条修 manifest.json。

## 闸2 契约可执行

**判定**：调度器 dry 跑一次 `run.py`（注入 `SCHED_CONTRACT_PROBE=1`），exit_code=0

**检查点**：
- run.py 是合法 Python 脚本（或可执行脚本）
- SDK `SchedTask.run()` 返回 0（心跳/断点/错误分类接口可用）

**失败修复**：本地 `python3 run.py` 裸跑复现，修业务代码直到 exit 0。

> **不设容量闸、不做冒烟测资源**：子任务无需预先跑小批量样本估算资源。调度器在任务**实际运行中**通过 cgroup 动态采样建立资源画像，逐步校准（声明值仅作初次准入的下界）。

## 闸失败不自动重试

闸失败后调度器**不做定时自动重试**——改 manifest 或 run.py 后，调度器热加载时会按新指纹重新检查（30s 周期），或手动 `sched register <id>` / Web 管理台「注册本地任务」立即重检。