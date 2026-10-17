# 排查手册

## 看状态

```bash
sched status                # 生产者存活 / 队列 / 存活 attempt / 动态目标 / 退让 / 保护对象
                            # （serve 在线时首行显示 serve=alive，数据来自每轮运行时快照）
sched list                  # 任务与优先级
sched job list <task>       # 该任务作业
sched job show <job_id>     # 作业状态 + attempts + reason
sched attempt list <job>    # attempt 历史（exit_code / status）
```

## 常见症状

| 症状 | 排查 |
| --- | --- |
| 作业一直 QUEUED 不启动 | 是否达动态目标（`status` 的 scale 段）；是否在退让/冷却；是否资源观测接近饱和；**是否处于高优先级保护轮（仅更高优先级可准入）**；`attempt list` 看是否已有存活 attempt 未退出 |
| 作业 BACKOFF 反复 | 执行者持续报 `error` 事件（资源类）并 exit 75：看 `job show` reason；日志在 `runtime/logs/<task>/`；确认资源不足可恢复而非永久（永久失败不应报资源不足）。到期自动重排（指数退避 + 抖动），无需人工干预 |
| 作业 FAILED | 业务逻辑错误或未知失败：看 `job show`/`attempt list` 的 exit_code 与 reason（执行进程 stdout/stderr 默认不归档，业务需自行保存输出）；修复后由生产者重放或重发新作业 |
| 生产者反复崩溃 | `status` 的 producers crash 计数；日志 `runtime/logs/<task>/producer.stderr.log`；崩溃退避在一次次加长 |
| 暂停后恢复重跑已完成工作 | 检查检查点是否周期提交、幂等键是否稳定；`runtime/runs/<attempt_id>/checkpoint.json` |
| 有孤儿进程 | 取消/暂停后进程树是否确认退出（cgroup 内 `cgroup.procs`）；重启接管会核实身份 |
| RECOVERING / RECOVERY_BLOCKED | 退出 0 但无 `done` 记录会自动转入 RECOVERY_BLOCKED（保持可见、不盲目重跑）。进程身份未知的 attempt 由调度器按 cgroup 归属自动核实清理后重放；仅清理不净（不可中断 D 态）才保持 RECOVERY_BLOCKED。调度器每 30s 自动复核迟到完成记录；人工解除用 `sched job requeue <job_id>`（关闭在途 attempt 并重新排队），或确认执行者 `complete()` 被调用 |
| 任务整体不启动（task backoff） | `sched status` 的 task backoff 段：`state=verify`＝步降后等剩余执行验证；`state=empty`＝任务级退避探测中（`wait` 为距下次探测秒数，`probe_level` 随失败递增）；各任务独立退避，其余任务不受影响。资源恢复并正确执行一步后自动回 normal |
| 事件停滞自动暂停 | 执行进程超时无进展/事件：存活由调度器自观测进程树 + CPU + 事件间隔，停滞阈值按自统计反馈节奏与实际延迟推导（`staleness_min_sec` 为下限），调度器先告警再协作暂停核实存活，属预期保护；任务不发心跳，反馈节奏由调度器对实际事件间隔自统计（TaskTiming EMA） |
| OOM/内存增长退让后反复暂停 | 执行内存快速增长或 cgroup OOM 证据会暂停可释放内存较多的低优先级执行（见 `status` 的 `oom_events`）；此类暂停的作业按 `stale_pause_cooldown_sec` 冷却后再排队，属预期防紧密重启循环；若某任务内存需求≈机器容量，它会低频重试而非静默放弃——修复业务内存或降低该任务批量 |
| CLI cancel 未生效 | serve 在线时走 `runtime/commands.jsonl` 命令通道并等 `commands_ack.jsonl` 回执；serve 离线时降级直连撤进程树；看回执与 `job show` 状态 |

## 关键文件位置

- 执行事件：`runtime/runs/<attempt_id>/events.jsonl`
- 暂停命令：`runtime/runs/<attempt_id>/control.json`
- 检查点：`runtime/runs/<attempt_id>/checkpoint.json`
- 状态日志：`runtime/status.jsonl`
- 运行时快照 / CLI 控制命令与回执：`runtime/snapshot.json`、`runtime/commands.jsonl`、`runtime/commands_ack.jsonl`
- 审计（接收/隔离）：`runtime/isolation/`、`runtime/archive/`

## 数据清理（仅调试，建议先停服务）

- 清空全部调度状态：删除 `runtime/exec.db` 与各任务 `outbox/`、`producer_state/`（谨慎：会丢游标与未完成作业记录）。
- 单作业重置：`sched job cancel <job_id>` 后由生产者按稳定标识重放。