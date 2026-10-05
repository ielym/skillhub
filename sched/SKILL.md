---
name: sched
description: sched 本地子任务守护器的使用规则与子任务创建规范。当用户要在 sched 上新建、上线、调试、交付一个被守护子任务，或咨询子任务清单(manifest)/意图文件/双闸准入/进程控制协议/抢占/断点续跑/错误码时使用。
---

# sched（任务守护器）

## 核心定位

sched 是常驻单进程的**本地子任务守护器**：

1. **进程意图驱动**：子任务通过写入不可变的「意图文件」（`requests/<request_id>.json`）声明"我要一个进程"；调度器扫描后拉起、维护、终结。
2. **固定控制协议**：子任务/进程与调度器只通过三条固定通道通信——**意图文件**（写新进程）、**state.json 的 control 段**（stop / no_retry / reschedule）、**退出码**（0 / 99 / 100 / 101 / 102 / 110）。
3. **全局资源协调**：cgroup v2 硬限 + 账本 + 资源画像（声明 + 运行中动态采样），同优先级冷启动轮转、有数据后 SJF。
4. **全进程可抢占**：**没有不可抢占**——高优绝对优势，可抢占任何更低优先级进程（daemon 也一样）。被抢进程 exit 99、落断点、同意图续跑。
5. **全进程断点硬契约**：daemon 与 oneshot 共用一套 SDK 断点（SIGTERM → 落断点 → exit 99）。调度器重启/抢占后从断点续跑，不重复已完成工作。
6. **append-only 意图**：意图文件写后不可变、不自行删除；新执行 = 新 `request_id` 文件，天然可回溯不同时期执行方式。
7. **无 interval / 无 trigger**：时机全部由子任务代码通过"写新意图"表达——调度器只做"扫描→收敛→资源协调"。

**路径约定（全文统一）**：

- **代码根**：scheduler 仓库 clone 目录（`tasks/`、`data/` 的父目录；默认 `sched` 包上一级，环境变量 `SCHED_HOME` 覆盖）。
- **skill 目录**：本 skill 的安装目录（模板/参考在其 `assets/`、`references/` 下）。

## 核心理念

| 维度 | sched 的规则 |
| --- | --- |
| 调度依据 | **优先级决定一切**：高优等待可抢占低优在跑任务（含 daemon） |
| 任务形态 | **daemon 与 oneshot 共用**：daemon 常驻靠 `while True` 循环 + 断点契约；oneshot 有限迭代；**都可被抢占** |
| 准入 | **双闸自动检查**：静态（manifest schema + entry 可执行 + 路径）→ 契约可执行（dry 跑通 + state.json 合法）。放入 `tasks/<id>/` 即自动开检，无需手动注册 |
| 资源 | 必须如实申报 CPU/内存（manifest resources）；cgroup 硬限 + 账本 + 画像；外部资源（代理/配额/VPN）**不做统一管理**，子任务按 100/101 退出码自分类，同意图 retry 配置（backoff）自治 |
| 新执行 | **新执行 = 新意图文件**（新 `request_id`），绝不可改写已有意图文件 |
| 进程协调 | **子任务自己管理**：多次新进程 = 多次 `emit_intent()`；无全局 queue/replace/reject 语义；通过代码（SDK）完成，禁止自然语言 |
| 失败处理 | 统一退出码：0 成功、99 抢占续跑、100/101 资源不足回退 pending、102 跳过本轮、110 数据风险、其他非 0 兜底按资源回退 pending |
| 任务基类 | **强制 SDK 契约行为**：继承 `SchedTask`（或 `OneshotTask`/`DaemonTask`），心跳、断点、99 退出、错误分类 |
| 生命周期控制 | 只能通过**固定协议**：意图文件（写新进程）、state.json control 段（stop/no_retry/reschedule）、退出码。**禁止自行删改意图文件** |

## 适用 / 不适用

- **适用**：在代码根上创建新的被守护子任务；为已有子任务改配置/排障/做交付验收；判断一个子任务能否/如何纳入守护；咨询 manifest 怎么写、意图文件怎么发、退出码什么意思。
- **不适用**：调度器核心源码（`sched/` 包）本身的重构开发（走需求审查流程，不属于子任务创建）。
- **铁律：子任务作者只在 `tasks/<id>/` 自己的目录内工作，禁止改 `sched/` 包源码、禁止手改 `data/runtime/` 内文件。**

## 命令速查

均在代码根执行（或等价 `sched` 命令）；确切行为与失败情形见 [configuration.md](references/configuration.md)。

```bash
python3 -m sched list                  # 已上线子任务、ok 状态、优先级、资源预估
python3 -m sched register <id>        # 立即跑双闸上线检查
python3 -m sched start <id>           # 启用 run_mode=manual 的子任务（置 enabled=true）
python3 -m sched status                # 子任务数、WQ、运行中、账本、意图消费状态
python3 -m sched process list [name]  # 子任务的意图清单（--json 含运行中进程）
python3 -m sched process stop <sid> <rid>     # 终止运行中意图（把意图文件标记消失 → 调度器 cancel 进程并置 done）
python3 -m sched process no-retry <sid> <rid> # 不再重试（同样标记意图消失 → 终结）
python3 -m sched clear [--delete-requests]    # 清空全部调度状态（注册表/WQ/意图/运行历史；建议先停服务）
python3 -m sched serve                 # 常驻调度循环（自动发现新子任务、热加载 30s）
python3 -m sched serve --web           # 同时启动内嵌 Web 管理台
```

## 路由：我要做什么 → 看哪个文件

| 你的问题 / 任务 | 必读文件 |
| --- | --- |
| 从零做一个子任务，按什么流程走 | [workflow.md](references/workflow.md)（四阶段流程）+ [acceptance.md](references/acceptance.md)（全部强制清单） |
| 哪些事绝对不能做 / 交付红线 | [rules.md](references/rules.md)（铁律 H1–H13 + 红线总表） |
| 上线检查（双闸）不过，怎么修 | [gates.md](references/gates.md)（双闸逐条判定与修复） |
| manifest 怎么写 / 意图文件怎么发 / SDK 怎么用 / 退出码 / control 段 | [contracts.md](references/contracts.md) |
| settings 参数、CLI 确切行为、数据/日志布局 | [configuration.md](references/configuration.md) |
| 抢占/排队/重试自治/意图消费状态 | [scheduling.md](references/scheduling.md) |
| 首次部署、cgroup 委派自检、Web 公网暴露、日常运维 | [deployment.md](references/deployment.md) |
| 子任务跑挂了 / 状态异常怎么排查 | [troubleshooting.md](references/troubleshooting.md) |
| 起步代码（骨架/场景模板） | [templates.md](references/templates.md) + [assets/](assets/) |

## 铁律索引（H1–H13，违反任一条不得交付）

1. **H1 唯一执行通道**：正式执行只能由调度器扫描意图触发；禁止 cron/手工跑/自触发。
2. **H2 全进程可抢占**：无豁免；daemon/oneshot 都可被高优抢占；被抢必落断点 exit 99。
3. **H3 全进程断点硬契约**：daemon 同样 SIGTERM → 落断点 → exit 99；不落地则后续无法恢复。
4. **H4 append-only 意图**：意图文件写后不可变、不自行删除；新执行 = 新 request_id。
5. **H5 生命周期只走控制协议**：禁止自行删改意图文件；停止/不再重试/稍后再跑走 state.json control 段或退出码。
6. **H6 进程协调代码化**：多次新进程、是否停旧进程、何时起新进程——**全部由子任务代码通过 SDK 完成**（`emit_intent` / `no_retry` / `request_stop`），禁止自然语言。
7. **H7 必走 SDK 契约**：继承 `SchedTask`，禁裸脚本绕过心跳/断点/分类。
8. **H8 资源如实申报**：manifest 里 resources 必填且有依据；外部资源（代理/配额等）无法统一申报与管理，靠 100/101 自治。
9. **H9 无密钥、执行面最小**：密钥走 600 权限文件；禁黑名单 env 键与绝对/`..` 路径。
10. **H10 源码不动、数据不手改**：仅调试清理时按流程编辑数据文件。
11. **H11 子任务自包含、禁止共享业务代码**：每个 `tasks/<id>/` 独享完整代码，禁止 `tasks/shared/` 或 `sys.path.insert` 共享业务逻辑（SDK `sched_task_sdk` 除外）。
12. **H12 运行参数写在配置里、禁止文件名反推**：进程跑什么（date/topic/query 等）必须写在意图 `config` 指向的文件里，禁止用 `request_id` 文件名编码参数。
13. **H13 及时打印进度日志**：所有子任务必须及时把执行进度写到 stdout/stderr（`flush=True`），并同步写 `state.enter_step` 的 progress，供管理台实时观察与 debug；禁止静默长跑。

全文（含每条的细节与原因）见 [rules.md](references/rules.md)。

## 标准流程一句话

**阶段 0 设计**（定 id/run_mode/优先级/资源/断点/意图策略，选模板）→ **阶段 1 本地裸进程调试**（`_dev` 目录跑 `run.py --dry-run`、断点演练）→ **阶段 2 放入 `tasks/<id>/`，调度器自动跑双闸上线**（闸失败在管理台/status 看原因，改文件后自动重检；也可手动 `register <id>` 立即检查）→ **阶段 3 跑通完整意图流程 + 抢占恢复演练** → **阶段 4 只认调度触发成功的交付验收**。
