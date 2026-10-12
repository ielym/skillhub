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
| 作业 BACKOFF 反复 | 执行者持续报 `external_shortage`：看 `job show` reason（退出码 75）；日志在 `runtime/logs/<task>/`；确认不足可恢复而非永久（永久失败不应报不足）。到期自动重排（指数退避 + 抖动），无需人工干预 |
| 作业 FAILED | 业务逻辑错误或未知失败：看 `job show`/`attempt list` 的 exit_code 与 reason（执行进程 stdout/stderr 默认不归档，业务需自行保存输出）；修复后由生产者重放或重发新作业 |
| 生产者反复崩溃 | `status` 的 producers crash 计数；日志 `runtime/logs/<task>/producer.stderr.log`；崩溃退避在一次次加长 |
| 暂停后恢复重跑已完成工作 | 检查检查点是否周期提交、幂等键是否稳定；`runtime/runs/<attempt_id>/checkpoint.json` |
| 有孤儿进程 | 取消/暂停后进程树是否确认退出（cgroup 内 `cgroup.procs`）；重启接管会核实身份 |
| RECOVERING / RECOVERY_BLOCKED | 退出 0 但无 `completed` 记录会自动转入 RECOVERY_BLOCKED（保持可见、不盲目重跑）；进程身份未知同样置 RECOVERY_BLOCKED。调度器每 30s 自动复核迟到完成记录；人工解除用 `sched job requeue <job_id>`（关闭在途 attempt 并重新排队），或确认执行者 `complete()` 被调用 |
| 心跳过期自动暂停 | 执行进程超时无心跳/进展：超时阈值按承诺反馈间隔与实际延迟推导（`heartbeat_stale_sec` 为下限），调度器先告警再协作暂停核实存活，属预期保护；检查执行者是否正常发心跳（SDK 默认自动） |
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