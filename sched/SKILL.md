---
name: sched
description: sched 本地子任务调度器（v3 生产者/执行分离协议）的操作、部署与调度策略。当用户要启动/停止/重启调度器、使用 CLI（serve/web/status/task/job/attempt 命令）、部署 Web 控制台（0.0.0.0:5555，无令牌）、排查调度异常（退避/暂停/恢复受阻/失败），或咨询调度策略（动态扩容、优先级保护、按任务独立资源退避）时使用。创建新的子任务走 sched_task_creator skill。
---

# sched（任务调度器 v3）

## 核心定位

sched 是常驻单进程的**本地子任务调度器**，采用**生产者 / 执行分离**架构：

1. **常驻生产者**：每个启用任务常驻一个生产者进程，自行维护业务触发时间，发现动态任务后把「就绪 JSON」发布到 `outbox/`。生产者与执行进程分属不同管理范围，**永不因调度压力被暂停/限额/抢占**。
2. **调度器只控制执行进程运行规模**：看到有效就绪 JSON 即视为已就绪，不再判断业务执行时间、不设日历定时。
3. **动态运行目标**：没有写死的最大并发/排队上限/资源申请。调度器只观测执行进程的实测消耗与业务进展，平缓扩容（冷启动 1 个，逐步 +1），高优保护、累计退让。
4. **按任务独立资源退避（TaskBackoff）**：本地资源（CPU/内存/IO）走 ResourceTrend 滞回状态机；外部资源不建模身份与配额，唯一事实来源是 exit 75 事件流。同一任务内的作业必共用外部资源——报资源错误先步降（暂停）本任务内最新启动的在途执行，再等剩余执行"正确一步"验证决定继续退避或恢复；全部退避即任务级退避（按递增间隔探测）；恢复与新拉起都逐个进行（前一个正确完成一步才放下一个）。跨任务是否共用资源未知，故各任务完全独立退避，互不牵连。
5. **SQLite 执行库**：作业/attempt/事件/检查点/回执落盘，重启接管、进程身份核实、作业去重。
6. **统一执行协议**：进展 + 错误/完成 + 资源不足（exit 75）+ 检查点（纯文件）+ 协作暂停 + 幂等提交。

**路径约定（全文统一）**：

- **代码根**：scheduler 仓库 clone 目录（`tasks/`、`runtime/`、`config.json` 的父目录；默认 `sched` 包上一级，环境变量 `SCHED_HOME` 覆盖）。
- **skill 目录**：本 skill 的安装目录（参考在 `references/` 下）。

## 核心理念

| 维度 | sched 的规则 |
| --- | --- |
| 触发模型 | **生产/执行分离**：生产者发现业务事件并发布就绪 JSON，执行进程独立受控 |
| 任务形态 | **有限任务与长期任务同一套请求协议**：都提供业务进展；有限任务完成后另提交完成记录 |
| 资源 | **不填写资源申请**：调度器只观测执行进程实测 CPU/内存/IO 与业务效果，学习接近饱和的位置 |
| 外部资源 | **本地不记录**：不建接口/账号/隧道/配额/资源指纹关联图；资源不足统一用 exit 75 表达；规避按事件流反馈自适应 |
| 新执行 | **生产者发布新作业 = 新 job_id**（由任务标识 + 稳定事件标识 + 业务版本确定，重放得到同一 job_id） |
| 进程协调 | **生产者自己管理**：多次新作业 = 生产者多次发布；禁止自然语言驱动 |
| 失败处理 | **退出码**：0 成功（需完成记录）、75 资源不足（资源类错误，可恢复退让）、其他非 0 业务/未知失败 |
| 断点/幂等 | **必需契约**：协作暂停、幂等提交（稳定幂等键 + 可核实提交记录）；断点是任务可选实践（H8，调度器不规定维护方式） |
| 生命周期 | **只走协议**：事件通道（心跳/进展/错误/完成/确认）+ 控制通道（暂停命令）+ 检查点文件 + 退出码 |

## 适用 / 不适用

- **适用**：调度器的启动/停止/重启、CLI 与 Web 控制台使用、部署与运维、调度异常排查（退避/暂停/恢复受阻/失败归因）、调度策略与架构咨询。
- **不适用**：创建/开发/调试新的子任务（走 `sched_task_creator` skill）；调度器核心源码（`sched/` 包）本身的重构开发（走需求审查流程）。

## 命令速查

均在代码根执行；确切行为与失败情形见 [configuration.md](references/configuration.md)。

```bash
sched serve                 # 常驻调度循环（前台）
sched web                   # Web 控制台（固定规则：无令牌、0.0.0.0、端口 5555，见 deployment.md）
sched status                # 全局状态（生产者 / 动态目标 / 存活 attempt / 队列 / 退让 / 任务退避状态）
sched list                  # 已加载任务（task.json）
sched task validate <id>    # 校验任务清单（task.json + 入口存在）
sched task enable <id>      # 启用任务（写 task.json enabled=true）
sched task disable <id>     # 禁用任务
sched job list [task]       # 作业清单
sched job show <job_id>     # 作业详情 + attempts
sched job cancel <job_id>   # 显式取消（终态；serve 在线走命令通道，离线直连撤进程树）
sched job requeue <job_id>  # 显式重排：关闭在途 attempt 并重新排队（运行中拒绝）
sched attempt list [job]    # attempt 清单
sched attempt cancel <id>   # 显式取消单个 attempt
```

## 路由：我要做什么 → 看哪个文件

| 你的问题 / 任务 | 必读文件 |
| --- | --- |
| CLI 确切行为、config.json、数据/日志布局 | [configuration.md](references/configuration.md) |
| 动态扩容 / 优先级保护 / 累计退让 / 变慢检测 / 按任务资源退避 / 状态机 | [scheduling.md](references/scheduling.md) |
| 首次部署、运行身份（systemd）、日常运维、Web 控制台 | [deployment.md](references/deployment.md) |
| 跑挂了 / 状态异常 / 退避循环怎么排查 | [troubleshooting.md](references/troubleshooting.md) |
| 协议参考（task.json / 就绪 JSON / 事件 / 退出码 / 检查点） | [contracts.md](references/contracts.md) |
| 创建新的子任务 | `sched_task_creator` skill |

## Web 控制台

固定部署规则：`sched web --host 0.0.0.0 --port 5555`，无令牌（systemd 单元 `scheduler-web.service`）。功能：总览（1h~48h 时间窗图表）/ 任务 / 作业 / 实时执行 / 事件流，SSE 实时推送；作业与任务的超级管理（取消 / 重排 / 删除）。详见 [deployment.md](references/deployment.md)。

## 关键行为速记

- **作业状态**：QUEUED → STARTING → RUNNING →（PAUSING → PAUSED | BACKOFF | SUCCEEDED | FAILED | CANCELLED）；重启走 RECOVERING/RECOVERY_BLOCKED 核实
- **暂停语义**：`pause_attempt` 协作暂停（可自动恢复）≠ `cancel_attempt`/`cancel_job` 终态取消（立即可持久化，防崩溃复活）
- **资源不足退避**：三层独立——作业级指数退避（有真实进展重新计数）；任务级 TaskBackoff 状态机（步降→验证→全退避探测→逐个放回，各任务互不牵连）；动态目标不因不足收缩，退避期冻结扩容探索
- **本地资源**：内存 ≥80% 单采样 SHED（停新增 + 撤内存）；CPU/IO 滞回判 HOLD（停新增）
- **serve 重启**：检查点恢复重放，在途执行无损回 QUEUED，零 CANCELLED
