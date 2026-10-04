# 铁律与红线（H1–H10）

违反任一条 **不得交付**，且需立刻修——这些不是"建议"，是系统级契约。

## H1 唯一执行通道

**规则**：正式执行只能由调度器扫描 `requests/` 里的意图触发。禁止 cron/手工跑 `run.py`/子任务自触发（自触发会绕开资源协调，可能打爆机器）。

**检查方式**：`run.py` 开头判断 `SCHED_RUN_ID` 环境变量——没有就输出警告并退出（`_dev` 目录调试例外）。

## H2 全进程可抢占

**规则**：无豁免——daemon/oneshot 都可被高优抢占。抢占后必须 40s 内落断点 exit 99；否则调度器 SIGKILL。

## H3 全进程断点硬契约

**规则**：daemon 同样要满足 SIGTERM → 落断点 → exit 99。不落地则调度器重启/抢占后无法恢复，进程会丢工作。

**SDK 保证**：继承 `SchedTask` 后 SIGTERM 钩子自动设 `_preempted` + 心跳线程退出 + exit 99。

## H4 append-only 意图

**规则**：意图文件（`requests/<request_id>.json`）写后**不可变、不可自行删除**。

- 改写已有意图 → 调度器标 `rejected`（append-only 违规，需手动处理）
- 自行删意图 → 调度器在持久态里标记 `done`（意图终结），但**不推荐自行删除**——应通过 SDK `request_stop` / `no_retry` 等协议控制

**正确做法**：新执行 = 新 `request_id` 文件（`emit_intent()` 自动生成新 ID）。

## H5 生命周期只走控制协议

**规则**：禁止子任务自行删意图文件。停止/不再重试/稍后再跑——统一走固定协议：

| 目标 | 正确做法 | 错误做法 |
| --- | --- | --- |
| 让进程停止 | SDK `request_stop()` → state.json control 段 | 自行删意图文件 |
| 让进程不再重试 | SDK `no_retry()` + exit 0/99/... | 删意图 + 改文件名 |
| 稍后再跑 | SDK `reschedule(delay_sec)` | sleep + 自己 `emit_intent` |
| 资源错误让调度器重试 | exit 100/101 | 什么都不做指望调度器自己重试 |

## H6 进程协调代码化

**规则**：多次新进程、是否停旧进程、何时起新进程——**全部由子任务代码通过 SDK 完成**。禁止在 SKILL.md 要求 Agent 用自然语言"生成"进程。

- 场景：2 天长任务 + 每天抓当天 → 驱动进程 `controller.py` 在启动第 N 天时 `emit_intent(config=day_N.json)`
- 场景：单实例（不要同时跑 2 个旧的）→ 驱动进程在写新意图前先调 SDK `request_stop` 旧进程，等调度器清理

## H7 必走 SDK 契约

**规则**：必须继承 `SchedTask`（或 `OneshotTask` / `DaemonTask`）。SDK 自动提供：

- 心跳线程（写 state.json.updated_at）
- SIGTERM 钩子（落断点 → exit 99）
- 断点落盘（`resume_point.json`）
- 错误分类辅助（`error(category, msg)`）

禁裸脚本绕过这些探针。

## H8 资源如实申报

**规则**：manifest 里 `resources.cpu` / `resources.memory_mb` 必须如实填写——声明值作为初次准入的下界，调度器在运行中通过 cgroup 动态采样校准画像。

外部资源（代理隧道/VPN/API 配额）**无法统一申报**——按 100/101 退出码自分类，SDK `error("resource", "...")` 让调度器自动 retry（意图的 lifetime.retry 控节奏）。

## H9 无密钥、执行面最小

**规则**：密钥必须走 `tasks/<id>/config/` 下 **600 权限文件**（`chmod 600 secret.pem`）。禁把密钥放进 manifest/state.json/错误输出。

禁黑名单 env 键（LD_PRELOAD / LD_LIBRARY_PATH / PYTHONSTARTUP / PATH 等）。

绝对路径、路径里含 `..` 的 entry.file / config 路径都被 manifest 解析器拒绝。

## H10 源码不动、数据不手改

**规则**：子任务作者只在 `tasks/<id>/` 自己的目录内工作。**禁止**：

- 改 `sched/` 包源码（那是调度器开发者的领域）
- 手动编辑 `data/runtime/*.json`、`data/jobs.json`、`data/runs/*.jsonl`（调试清理时按流程编辑除外）

## 红线总表（任一条 = 立即停手重写）

| 红线 | 含义 |
| --- | --- |
| `SCHED_RUN_ID` 空跑正式任务 | 任务绕过调度器直跑，资源不受控 |
| 意图文件被改写（指纹变更） | append-only 契约破坏，调度器标 rejected |
| 意图文件被自行删除 | 风险高：调度器感知可能滞后，进程和意图状态不一致 |
| 裸脚本跳过 SDK | 无心跳/断点，卡死无法恢复 |
| 进程里硬编码密钥 | 泄漏 + 调试时被打出来 |
| 自然语言"生成"多个进程 | 不可控——必须代码化 |
